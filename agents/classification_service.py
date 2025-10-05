# agents/services/classification_service.py
import os
from typing import Literal, TypedDict, Union
from dotenv import load_dotenv
import google.generativeai as genai
import json

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("❌ GEMINI_API_KEY not found in .env file.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Expected classification return values
Classification = Literal["tool", "workflow", "both"]

class ClassificationResult(TypedDict):
    label: Classification
    confidence: float
    reasoning: str


# ------------------ MAIN FUNCTION ------------------ #
def classify_query(query: str) -> Classification:
    """
    Use Gemini to classify user query into:
    - 'tool' → clearly asks for a single Galaxy tool
    - 'workflow' → clearly asks for a Galaxy workflow / pipeline
    - 'both' → ambiguous or could mean either/both

    Gemini will reason briefly and return JSON including:
    { "reasoning": "...", "label": "tool|workflow|both", "confidence": 0.85 }
    """

    prompt = f"""
You are a Galaxy Project classification assistant.

Your task:
1️⃣ Analyze the user query and reason in one or two sentences.
2️⃣ Then output a JSON object with keys:
- reasoning: short reasoning text
- label: "tool", "workflow", or "both"
- confidence: number between 0 and 1 indicating certainty

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

    # Recommended: Use the latest stable flash model
    # model = genai.GenerativeModel("models/gemini-2.5-flash")
    # or, for best reasoning accuracy:
    model = genai.GenerativeModel("models/gemini-2.5-pro")

    # Generate classification
    response = model.generate_content(prompt)

    raw_output = response.text.strip()
    parsed: Union[ClassificationResult, None] = None
 # ------------------ SAFE JSON PARSING ------------------ #
    try:
        # Some Gemini responses may include markdown fences or extra text — clean them
        cleaned = raw_output.strip("`").replace("json", "").strip()
        parsed = json.loads(cleaned)

        # Normalize label to lowercase
        label = parsed.get("label", "").lower().strip()
        confidence = float(parsed.get("confidence", 0))
        reasoning = parsed.get("reasoning", "").strip()

        # Fallbacks for safety
        if label not in ["tool", "workflow", "both"]:
            label = "both"

        # Optional: log reasoning for debugging (comment out in production)
        print(f"[Gemini] Query: {query}")
        print(f"[Gemini] Reasoning: {reasoning}")
        print(f"[Gemini] Label: {label} | Confidence: {confidence}\n")

        return label

    except Exception as e:
        # If Gemini fails to parse, default to 'both'
        print(f"⚠️ Gemini parsing failed: {e}")
        print(f"Raw output: {raw_output}")
        return "both"