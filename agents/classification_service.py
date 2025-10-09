# agents/services/classification_service.py
import os
from typing import Literal, TypedDict, Union
from dotenv import load_dotenv
import json

# --- Load environment variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Initialize models ---
use_openai = False
use_gemini = False

if OPENAI_API_KEY:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    use_openai = True
elif GEMINI_API_KEY:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    use_gemini = True
else:
    raise EnvironmentError("❌ Neither OPENAI_API_KEY nor GEMINI_API_KEY found in .env file.")


# --- Expected classification return values ---
Classification = Literal["tool", "workflow", "both"]

class ClassificationResult(TypedDict):
    label: Classification
    confidence: float
    reasoning: str


# ------------------ MAIN FUNCTION ------------------ #
def classify_query(query: str) -> Classification:
    """
    Classifies a query into 'tool', 'workflow', or 'both' using available LLM.
    Priority: OpenAI → Gemini
    Falls back safely if one provider is unavailable.
    """

    prompt = f"""
You are a Galaxy Project classification assistant.

Your task:
1️⃣ Analyze the user query and reason in one or two sentences.
2️⃣ Then output a JSON object with keys:
- reasoning: short reasoning text
- label: "tool", "workflow", or "both"
- confidence: number between 0 and 1 indicating certainty.

Classification rules:
- "tool" → the user clearly refers to a single Galaxy tool or function.
- "workflow" → the user clearly refers to a multi-step analysis or pipeline.
- "both" → ambiguous, general, or could involve both tool and workflow.

Respond ONLY with valid JSON, no extra text.

Example format:
{{
  "reasoning": "The user mentions RNA-seq alignment which involves multiple tools.",
  "label": "workflow",
  "confidence": 0.82
}}

Now classify this query:
"{query}"
"""

    raw_output = ""
    parsed: Union[ClassificationResult, None] = None

    try:
        if use_openai:
            # --- Use OpenAI (primary) ---
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw_output = response.choices[0].message.content.strip()

        elif use_gemini:
            # --- Use Gemini (fallback) ---
            import google.generativeai as genai
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(prompt)
            raw_output = response.text.strip()

        # ------------------ SAFE JSON PARSING ------------------ #
        cleaned = raw_output.strip("`").replace("json", "").strip()
        parsed = json.loads(cleaned)

        label = parsed.get("label", "").lower().strip()
        confidence = float(parsed.get("confidence", 0))
        reasoning = parsed.get("reasoning", "").strip()

        if label not in ["tool", "workflow", "both"]:
            label = "both"

        print(f"[LLM: {'OpenAI' if use_openai else 'Gemini'}]")
        print(f"Query: {query}")
        print(f"Reasoning: {reasoning}")
        print(f"Label: {label} | Confidence: {confidence}\n")

        return label

    except Exception as e:
        print(f"⚠️ Classification parsing failed: {e}")
        print(f"Raw output: {raw_output}")
        return "both"
