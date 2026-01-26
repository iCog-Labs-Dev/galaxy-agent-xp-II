import os
import time
import json
import re
import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# --- Configuration ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "abc12345"))

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_LLM_MODEL", "Qwen/Qwen2.5-72B-Instruct")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

if not HF_TOKEN:
    raise SystemExit("❌ Error: HF_API_TOKEN environment variable not set.")

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json",
}


class CommunitySummarizer:
    def __init__(self, uri, auth, skip_migration_check=False):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.http = requests.Session()
        self.http.headers.update(HEADERS)
        
        # Ensure database schema is up to date
        if not skip_migration_check:
            self._check_migrations()

    def close(self):
        self.http.close()
        self.driver.close()

    def _check_migrations(self):
        """Verify database schema is up to date before running."""
        from .migrations.runner import MigrationRunner
        
        runner = MigrationRunner(self.driver)
        if not runner.is_up_to_date():
            pending = [s["version"] for s in runner.get_status() if not s["applied"]]
            raise RuntimeError(
                f"Database schema is outdated. Pending migrations: {pending}\n"
                f"Run: python -m agents.community_detection.migrate upgrade"
            )

    def _chat_with_retry(self, messages, max_retries=5):
        payload = {
            "model": HF_MODEL,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.3,
            "stream": False,
        }

        for attempt in range(1, max_retries + 1):
            try:
                resp = self.http.post(HF_API_URL, json=payload, timeout=90)

                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]

                if resp.status_code in [429, 503]:
                    wait = 10 * attempt
                    print(f"    ⏳ Model busy/rate-limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                print(f"    ❌ API Error {resp.status_code}: {resp.text[:200]}")

            except Exception as e:
                print(f"    ❌ Network Error: {e}")

            time.sleep(2)
        return None

    def _prepare_json_string(self, text):
        """Extract JSON object from text."""
        if not text:
            return None

        # Clean markdown
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)

        # Find start of JSON
        start = text.find("{")
        if start == -1:
            return None

        return text[start:]

    def generate_summary_json(self, context_text, level_name):
        system_msg = "You are a Bioinformatics Assistant. You output ONLY valid JSON."

        if level_name == "L0":
            example_input = "Tools:\n- FastQC: Quality control tool\n- Trimmomatic: Flexible read trimming tool"
            example_output = json.dumps(
                {
                    "title": "Read Quality Control",
                    "summary": "This set of tools focuses on the initial quality assessment and preprocessing of raw sequencing data, including adapter trimming and quality filtering.",
                }
            )
            user_prompt = f"Analyze these Galaxy tools:\n{context_text}"
        else:
            example_input = "Sub-tasks:\n- Read Mapping: Align reads to reference\n- Variant Calling: Identify mutations"
            example_output = json.dumps(
                {
                    "title": "Genomic Variant Analysis",
                    "summary": "A comprehensive workflow that progresses from raw read alignment to the identification and annotation of genetic variants relative to a reference genome.",
                }
            )
            user_prompt = f"Analyze these sub-tasks:\n{context_text}"

        messages = [
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": f"{example_input}\n\nReturn JSON with 'title' and 'summary'.",
            },
            {"role": "assistant", "content": example_output},
            {
                "role": "user",
                "content": f"{user_prompt}\n\nReturn JSON with 'title' and 'summary'.",
            },
        ]

        response_text = self._chat_with_retry(messages)

        if not response_text:
            return None

        try:
            # Extract and parse JSON
            json_candidate = self._prepare_json_string(response_text)

            if not json_candidate:
                print(f"    ⚠️ No JSON object found in response.")
                return None

            decoder = json.JSONDecoder(strict=False)
            data, _ = decoder.raw_decode(json_candidate)

            title = data.get("title") or data.get("name")
            summary = data.get("summary") or data.get("description")

            if title and summary:
                return {"title": title, "summary": summary}
            else:
                print(f"    ⚠️ Missing keys in JSON: {data.keys()}")

        except json.JSONDecodeError as e:
            print(f"    ⚠️ JSON Fail: {e}")
            print(f"    Raw output start: {str(response_text)[:150]}...")
        except Exception as e:
            print(f"    ⚠️ Parse Error: {e}")

        return None

    def summarize_l0(self):
        print("\n--- Processing Level 0 (Specific Clusters) ---")
        with self.driver.session() as session:
            comm_ids = session.run(
                """
                MATCH (c:Community {level: 0}) 
                WHERE c.name IS NULL OR c.name STARTS WITH 'comm_'
                RETURN c.id
            """
            ).value()

        print(f"Found {len(comm_ids)} clusters to summarize.")
        for comm_id in comm_ids:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (c:Community {id: $id})<-[:IN_COMMUNITY]-(t:Tool)
                    OPTIONAL MATCH (t)-[r:USED_WITH]-(other)
                    WITH t, count(r) as degree
                    ORDER BY degree DESC
                    LIMIT 15
                    RETURN t.name as name, t.description as desc
                """,
                    id=comm_id,
                )
                tools = [f"- {r['name']}: {r['desc']}" for r in result]

            if not tools:
                print(f"  > Skipping {comm_id} (empty)")
                continue

            print(f"  > Summarizing {comm_id}...")
            data = self.generate_summary_json("\n".join(tools), "L0")

            if data:
                print(f"    ✅ {data['title']}")
                with self.driver.session() as session:
                    session.run(
                        "MATCH (c:Community {id: $id}) SET c.name = $t, c.summary = $s",
                        id=comm_id,
                        t=data["title"],
                        s=data["summary"],
                    )
            time.sleep(2)

    def summarize_l1(self):
        print("\n--- Processing Level 1 (Broad Themes) ---")
        with self.driver.session() as session:
            comm_ids = session.run(
                """
                MATCH (c:Community {level: 1}) 
                WHERE c.name IS NULL OR c.name STARTS WITH 'comm_'
                RETURN c.id
            """
            ).value()

        print(f"Found {len(comm_ids)} themes to summarize.")
        for comm_id in comm_ids:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (c:Community {id: $id})-[:IS_PARENT_OF]->(sub:Community)
                    RETURN sub.name as title, sub.summary as summary
                    ORDER BY sub.name
                """,
                    id=comm_id,
                )
                subs = [f"- {r['title']}: {r['summary']}" for r in result]

            if not subs:
                print(f"  > Skipping {comm_id} (empty)")
                continue

            print(f"  > Summarizing {comm_id}...")
            data = self.generate_summary_json("\n".join(subs), "L1")

            if data:
                print(f"    ✅ {data['title']}")
                with self.driver.session() as session:
                    session.run(
                        "MATCH (c:Community {id: $id}) SET c.name = $t, c.summary = $s",
                        id=comm_id,
                        t=data["title"],
                        s=data["summary"],
                    )
            time.sleep(2)


if __name__ == "__main__":
    job = CommunitySummarizer(NEO4J_URI, NEO4J_AUTH)
    try:
        job.summarize_l0()
        job.summarize_l1()
    finally:
        job.close()
