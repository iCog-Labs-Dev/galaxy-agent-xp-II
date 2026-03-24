import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def get_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment (.env).")
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

def generate_workflow_name_llm(workflow_json, prompt_override=None):
    """Generate a descriptive Galaxy workflow name using Gemini (langchain_google_genai, gemini-2.5-flash)."""
    workflow_str = json.dumps(workflow_json, indent=2)
    prompt = prompt_override or f"""
You are an expert in bioinformatics and scientific workflow design.
Your task is to generate a concise and descriptive name for a Galaxy workflow.
The name must summarize the workflow's main purpose based on the tools and analysis steps in the JSON.
Guidelines:
1. The name must clearly describe the workflow's analysis goal.
2. Focus on the primary biological or computational task (e.g., RNA-Seq analysis, Variant calling, Genome assembly).
3. Use between 3 or 4 words.
4. Use only letters and spaces (no punctuation).
5. Capitalize major words.
6. Do NOT include explanations or extra text.
7. Return ONLY the workflow name.
Workflow JSON:
{workflow_str}
Output:
Workflow Name:
"""
    try:
        llm = get_llm()
        resp = llm.invoke(prompt)
        name = resp.content.strip()
        return name if name else "Workflow_Auto_Generated"
    except Exception as e:
        print(f"Gemini API exception: {e}")
        return f"AI_Generated_Workflow{str(e)[:20]}"

def extract_short_name_from_id(tool_id: str) -> str:
    """
    Extracts the short tool name from a Galaxy tool ID.
    Handles IDs like:
      - testtoolshed.g2.bx.psu.edu/repos/bgruening/graphicsmagick_image_convert/graphicsmagick_image_convert/1.3.31+galaxy1
      - toolshed.g2.bx.psu.edu/repos/imgteam/projective_transformation/ip_projective_transformation/0.1.0
    Returns the last segment before the version (e.g., 'graphicsmagick_image_convert', 'ip_projective_transformation').
    """
    if not tool_id:
        return ""
    parts = tool_id.strip().split("/")
    if len(parts) < 2:
        return tool_id
    return parts[-2]
