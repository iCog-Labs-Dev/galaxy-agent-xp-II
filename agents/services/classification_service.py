# agents/services/classification_service.py
import os
from typing import Literal
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("❌ GEMINI_API_KEY not found in .env file.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Expected classification return values
Classification = Literal["tool", "workflow", "both"]

def classify_query(query: str) -> Classification:
    """
    Use Gemini to classify a user's query into:
    - 'tool': user clearly asks for a specific Galaxy tool
    - 'workflow': user clearly asks for a Galaxy workflow
    - 'both': query is ambiguous or could involve both

    Returns:
        Classification (str): "tool", "workflow", or "both"
    """

    # Prompt with a bit of few-shot reasoning to improve classification
    prompt = f"""
You are a highly intelligent assistant that classifies Galaxy Project queries.

Classify the following user query strictly as one of:
- "tool" (if the user is clearly asking for a single Galaxy tool)
- "workflow" (if the user is clearly asking for a workflow / multi-step pipeline)
- "both" (if the query is ambiguous, could involve either tools or workflows, 
        or mentions analysis without specifying)

Only return exactly one of these three words: tool, workflow, or both. 
Do not add any extra text or explanation.

Query: "{query}"
"""

    # Select Gemini model
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Generate classification
    response = model.generate_content(prompt)

    # Clean and normalize output
    result = response.text.strip().lower()

    # Fallback to 'both' for any unexpected outputs
    if result not in ["tool", "workflow", "both"]:
        return "both"
    
    return result
