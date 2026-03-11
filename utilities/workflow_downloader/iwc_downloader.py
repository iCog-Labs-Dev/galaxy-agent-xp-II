import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GITHUB_API_URL = "https://api.github.com/repos/galaxyproject/iwc/contents/workflows"
RAW_BASE_URL = "https://raw.githubusercontent.com/galaxyproject/iwc/main/workflows"

MAX_WORKFLOWS = None

github_token = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {github_token}"} if github_token else {}


def github_api_get(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def fetch_raw(path):
    url = f"{RAW_BASE_URL}/{path}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.text


# ----------------------------
#   FULL WORKFLOW PARSER
# ----------------------------
def parse_ga_file(ga_json):
    try:
        workflow_name = ga_json.get("name", "")
        steps = ga_json.get("steps", {})

        step_list = []
        subworkflows = []
        step_data: dict
        step_id: str
        
        for step_id, step_data in steps.items():
            
            step_type = step_data.get("type", "")
             
            step_list.append({
                "step_id": int(step_id),
                "annotation": step_data.get("annotation", ""),
                "type": step_type,
                "tool_id": step_data.get("tool_id"),
                "tool_version": step_data.get("tool_version"),
                "name": step_data.get("name", ""),
                "subworkflow_name": step_data.get("subworkflow").get("name") if step_data.get("subworkflow", "") else "",
                "label": step_data.get("label", ""),
                "inputs": step_data.get("inputs", []),
                "outputs": step_data.get("outputs", []),
                "input_connections": step_data.get("input_connections", {}),
                "tool_shed_repository": step_data.get("tool_shed_repository", {})
            })
            
        if step_type == "subworkflow" and "subworkflow" in step_data:

                subwf_json = step_data["subworkflow"]
                parsed_sub = parse_ga_file(subwf_json)

                if parsed_sub:
                    subworkflows.append(parsed_sub)

        return {
            "workflow_name": workflow_name,
            "number_of_steps": len(steps),
            "steps": step_list,
            "subworkflows": subworkflows
        }

    except Exception as e:
        print("Error parsing GA file:", e)
        raise
        # return None


# ----------------------------
#   SCAN INDIVIDUAL REPO
# ----------------------------
def scan_repo(category, repo_name):
    base_path = f"{category}/{repo_name}"
    url = f"{GITHUB_API_URL}/{category}/{repo_name}"

    try:
        repo_contents = github_api_get(url)
    except Exception as e:
        print(f"⚠️ Failed to scan repo '{repo_name}': {e}")
        return None

    workflow_files = []
    subworkflows= []
    files_present = set()
    directories_present = set()
    readme_content = None

    # loop inside workflow repo
    for item in repo_contents:
        name = item["name"]
        if item["type"] == "file":
            files_present.add(name)

            if name.endswith(".ga"):
                path = f"{base_path}/{name}"
                ga_text = fetch_raw(path)
                if isinstance(ga_text, str):
                    ga_text = json.loads(ga_text)
                    
                parsed = parse_ga_file(ga_text)
                
                if parsed:
                    subworkflows = parsed.get("subworkflows")
                    parsed.pop("subworkflows")
                    parsed.update({
                        "file_name": name,
                        "raw_download_url": f"{RAW_BASE_URL}/{path}"
                    })
                    workflow_files.append(parsed)
                    if subworkflows:
                        workflow_files.extend((subworkflows))

            if name == "README.md":
                try:
                    readme_content = fetch_raw(f"{base_path}/{name}")
                except:
                    readme_content = None

        elif item["type"] == "dir":
            directories_present.add(name)

    return {
        "category": category.lower(),
        "workflow_repository": repo_name.lower(),
        "workflow_files": workflow_files,
        "readme_content": readme_content,
    }


# ----------------------------
#   MAIN RUNNER
# ----------------------------
def main():
    print("🔍 Fetching workflow categories...")
    categories = github_api_get(GITHUB_API_URL)
    all_data = []
    count = 0

    for cat in categories:
        if cat["type"] != "dir":
            continue
        category = cat["name"]
        print(f"\n📂 Category: {category}")

        repos = github_api_get(f"{GITHUB_API_URL}/{category}")

        for repo in repos:
            if repo["type"] != "dir":
                continue

            if MAX_WORKFLOWS is not None and count >= MAX_WORKFLOWS:
                break

            repo_name = repo["name"]
            print(f"  📁 Repo: {repo_name}")

            repo_data = scan_repo(category, repo_name)
            if repo_data:
                all_data.append(repo_data)
                count += 1

        if MAX_WORKFLOWS is not None and count >= MAX_WORKFLOWS:
            break

    # Save output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"iwc_full.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\n📦 Saved complete workflow dump to: {output_file}")


if __name__ == "__main__":
    main()
