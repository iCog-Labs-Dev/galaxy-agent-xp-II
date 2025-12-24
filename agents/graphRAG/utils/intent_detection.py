#!/usr/bin/env python3
"""
LLM Intent Classification Service for Galaxy Agent.

Purpose:
- Classify user queries as "tool", "workflow", or "both".
- Does NOT generate embeddings (handled separately in the embedding service).

Priority: Gemini → OpenAI
"""

import os
import json
from typing import Literal, TypedDict
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Expected classification return values ---
Classification = Literal["tool", "workflow", "both"]

class ClassificationResult(TypedDict):
    label: Classification
    confidence: float
    reasoning: str

# --- Lazy-loaded clients ---
_gemini_initialized = False
_openai_client = None

# ------------------ Helper Functions ------------------ #

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

# ------------------ Main Classification ------------------ #

def classify_query(query: str) -> ClassificationResult:
    """
    Classify a user query as 'tool', 'workflow', or 'both'.
    Uses Gemini first, falls back to OpenAI.
    """
    label: Classification = "both"
    confidence = 0.5
    reasoning = "Fallback classification"
    raw_output = ""

    try:
        prompt = f"""
You are a Galaxy Project classification assistant.

Task:
- Analyze the user query and reason in 1-2 sentences.
- Output JSON with keys:
  - reasoning: short reasoning text
  - label: "tool", "workflow", or "both"
  - confidence: number between 0 and 1

Classification rules:
- "tool" → the user clearly refers to a single Galaxy tool or function
- "workflow" → the user clearly refers to a multi-step analysis or pipeline
- "both" → ambiguous/general or could involve both

Example format:
{{
  "reasoning": "The user mentions RNA-seq alignment which involves multiple tools.",
  "label": "workflow",
  "confidence": 0.82
}}

Respond ONLY with JSON, no extra text.

Query: "{query}"
"""

        # --- Gemini first ---
        if _init_gemini():
            import google.generativeai as genai
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(prompt)
            raw_output = response.text.strip()

        # --- Fall back to OpenAI ---
        else:
            client = _init_openai_client()
            if client:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                raw_output = response.choices[0].message.content.strip()
            else:
                print("⚠️ No API keys available for classification. Returning 'both'.")
                return ClassificationResult(label="both", confidence=0.5, reasoning="No API keys available")

        # ------------------ Parse JSON safely ------------------ #
        cleaned = raw_output.strip("`").replace("json", "").strip()
        parsed = json.loads(cleaned)
        reasoning = parsed.get("reasoning", reasoning)
        confidence = float(parsed.get("confidence", confidence))
        label_candidate = parsed.get("label", "").lower().strip()
        if label_candidate in ["tool", "workflow", "both"]:
            label = label_candidate

    except Exception as e:
        print(f"⚠️ Classification failed: {e}")
        print(f"Raw LLM output: {raw_output}")

    return ClassificationResult(label=label, confidence=confidence, reasoning=reasoning)

# ------------------ Example Usage ------------------ #
if __name__ == "__main__":
    q = input("Enter your query: ")
    result = classify_query(q)
    print(json.dumps(result, indent=2))
