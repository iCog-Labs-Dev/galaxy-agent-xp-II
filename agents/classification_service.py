# agents/services/classification_service.py
import os
import json
from typing import Literal, TypedDict, Union
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Expected classification return values ---
Classification = Literal["tool", "workflow", "both"]

class ClassificationResult(TypedDict):
    label: Classification
    confidence: float
    reasoning: str

# --- Lazy-loaded clients ---
_openai_client = None
_gemini_initialized = False

def _init_openai_client():
    global _openai_client
    if not OPENAI_API_KEY:
        return None
    if _openai_client is None:
        try:
            from openai import OpenAI
            _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            print(f"⚠️ Failed to initialize OpenAI client: {e}")
            _openai_client = None
    return _openai_client

def _init_gemini():
    global _gemini_initialized
    if not GEMINI_API_KEY:
        return False
    if not _gemini_initialized:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            _gemini_initialized = True
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini client: {e}")
            _gemini_initialized = False
    return _gemini_initialized

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
        # --- Try OpenAI first ---
        client = _init_openai_client()
        if client:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw_output = response.choices[0].message.content.strip()

        # --- Fall back to Gemini ---
        elif _init_gemini():
            import google.generativeai as genai
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(prompt)
            raw_output = response.text.strip()

        else:
            print("⚠️ No API keys available for classification. Returning 'both'.")
            return "both"

        # ------------------ SAFE JSON PARSING ------------------ #
        cleaned = raw_output.strip("`").replace("json", "").strip()
        parsed = json.loads(cleaned)

        label = parsed.get("label", "").lower().strip()
        confidence = float(parsed.get("confidence", 0))
        reasoning = parsed.get("reasoning", "").strip()

        if label not in ["tool", "workflow", "both"]:
            label = "both"

        print(f"[LLM: {'OpenAI' if client else 'Gemini'}]")
        print(f"Query: {query}")
        print(f"Reasoning: {reasoning}")
        print(f"Label: {label} | Confidence: {confidence}\n")

        return label

    except Exception as e:
        print(f"⚠️ Classification parsing failed: {e}")
        print(f"Raw output: {raw_output}")
        return "both"
