#!/usr/bin/env python3
"""
LLM Intent Classification Service for Galaxy Agent.

Priority: Gemini (multi-model) → OpenAI
"""

import os
import json
import time
from typing import Literal, TypedDict
from dotenv import load_dotenv
import google.generativeai as genai

# --------------------- Load environment variables ---------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --------------------- Expected output types -------------------------
Classification = Literal["tool", "workflow", "both"]

class ClassificationResult(TypedDict):
    label: Classification
    confidence: float
    reasoning: str

# --------------------- Gemini setup ---------------------------------
_gemini_initialized = False
GEMINI_MODELS = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-beta",
    "models/gemini-2.5-light"
]

def _init_gemini():
    global _gemini_initialized
    if not GEMINI_API_KEY:
        return False
    if not _gemini_initialized:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            _gemini_initialized = True
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini client: {e}")
            _gemini_initialized = False
    return _gemini_initialized

# --------------------- OpenAI helper --------------------------------
def _classify_with_openai(prompt: str) -> str | None:
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ OpenAI failed: {e}")
        return None

# --------------------- Main classification -------------------------
def classify_query(query: str) -> ClassificationResult:
    label: Classification = "both"
    confidence = 0.5
    reasoning = "Fallback classification"
    raw_output = ""

    prompt = f"""
You are a Galaxy Project classification assistant.

Return ONLY JSON:
{{
  "reasoning": "...",
  "label": "tool | workflow | both",
  "confidence": 0.0
}}

Query: "{query}"
"""

    # -------- Gemini first --------
    if _init_gemini():
        for model_name in GEMINI_MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                raw_output = response.text.strip()
                break
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    print(f"⚠️ {model_name} limit reached, switching to next model...")
                    continue
                else:
                    raise e

    # -------- OpenAI fallback --------
    if not raw_output:
        raw_output = _classify_with_openai(prompt) or ""

    # -------- If all failed --------
    if not raw_output:
        return ClassificationResult(
            label="both",
            confidence=0.5,
            reasoning="All LLMs exhausted"
        )

    # -------- Parse JSON safely --------
    try:
        cleaned = raw_output.strip("`").replace("json", "").strip()
        parsed = json.loads(cleaned)
        label_candidate = parsed.get("label", label).lower().strip()
        if label_candidate in ["tool", "workflow", "both"]:
            label = label_candidate
        confidence = float(parsed.get("confidence", confidence))
        reasoning = parsed.get("reasoning", reasoning)
    except Exception:
        print(f"⚠️ Failed to parse LLM output: {raw_output}")

    return ClassificationResult(
        label=label,
        confidence=confidence,
        reasoning=reasoning
    )

# --------------------- Example CLI ----------------------------------
if __name__ == "__main__":
    while True:
        q = input("Enter your query (or 'exit' to quit): ")
        if q.lower() == "exit":
            break
        result = classify_query(q)
        print(json.dumps(result, indent=2))
