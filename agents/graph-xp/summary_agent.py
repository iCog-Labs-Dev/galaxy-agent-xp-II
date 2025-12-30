from __future__ import annotations

import os
import logging
from typing import Optional, Protocol, List
from dotenv import load_dotenv

# - CONFIGURATION 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# ENV HELPERS 
def _get_env() -> tuple[Optional[str], Optional[str]]:
    return os.getenv("GEMINI_API_KEY"), os.getenv("OPENAI_API_KEY")


def _default_provider() -> str:
    gemini_key, openai_key = _get_env()
    return "openai" if openai_key else "gemini"


def _validate_env() -> None:
    gemini_key, openai_key = _get_env()
    if not gemini_key and not openai_key:
        raise ValueError(
            "Missing GEMINI_API_KEY and OPENAI_API_KEY"
        )


# ------------------ LLM INTERFACE ------------------ #
class LLMInterface(Protocol):
    def generate(self, prompt: str) -> str: ...


# ------------------ PROVIDERS ------------------ #
class GeminiModel:
    def __init__(self, api_key: str, model_name: str = "models/gemini-2.5-flash"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        return (response.text or "").strip()


class OpenAIModel:
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        import openai
        openai.api_key = api_key
        self._openai = openai
        self._model = model_name

    def generate(self, prompt: str) -> str:
        response = self._openai.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()


#  PROVIDER SELECTION 
def get_llm(provider: Optional[str] = None) -> LLMInterface:
    _validate_env()
    gemini_key, openai_key = _get_env()
    chosen = (provider or _default_provider()).lower()

    if chosen == "openai":
        if openai_key:
            return OpenAIModel(openai_key)
        elif gemini_key:
            logger.warning("Falling back to Gemini")
            return GeminiModel(gemini_key)
        else:
            raise ValueError("No valid LLM provider available")

    if chosen == "gemini":
        if gemini_key:
            return GeminiModel(gemini_key)
        elif openai_key:
            logger.warning("Falling back to OpenAI")
            return OpenAIModel(openai_key)
        else:
            raise ValueError("No valid LLM provider available")

    # Provider explicitly invalid
    raise ValueError("Unknown LLM provider")


class SummaryAgent:
    """
    Unified summary agent for tools and workflows.
    Produces clean, human-readable summaries.
    """

    def __init__(self, llm: Optional[LLMInterface] = None):
        self.llm = llm or get_llm()

    # -------- TOOLS -------- #
    def summarize_tools_suggestions(self, tools: List[dict], query: str) -> str:
        if not tools:
            return "No relevant tools found."

        tool_descriptions = "\n".join(
            f"{t.get('name', 'Unknown Tool')} | Category: {t.get('category', 'N/A')} | {t.get('description', 'No description.')}"
            for t in tools
        )

        prompt = f"""
You are a helpful AI assistant for Galaxy bioinformatics tools.

User query: "{query}"

Provide a **clean, human-readable summary**. 
Do not use asterisks, hashes, or Markdown.
Use newlines to separate each tool. Include:
- Tool name
- Category
- One-line relevance/description

{tool_descriptions}
"""
        return self.llm.generate(prompt)

    # -------- WORKFLOWS -------- #
    def summarize_workflows_suggestions(self, workflows: List[dict], query: str) -> str:
        if not workflows:
            return "No relevant workflows found."

        workflow_descriptions = "\n".join(
            f"{wf.get('name', 'Unknown Workflow')} | Category: {wf.get('category', 'N/A')} | Score: {wf.get('score', 0):.2f} | {wf.get('readme_excerpt', 'No description.')}"
            for wf in workflows
        )

        prompt = f"""
You are a helpful AI assistant for Galaxy workflows.

User query: "{query}"

Provide a **clean, human-readable summary**. 
Do not use asterisks, hashes, or Markdown.
Use newlines to separate each workflow. Include:
- Workflow name
- Category
- Score
- One-line description

{workflow_descriptions}
"""
        return self.llm.generate(prompt)


    

_default_summary_agent: Optional[SummaryAgent] = None


def _get_summary_agent() -> SummaryAgent:
    global _default_summary_agent
    if _default_summary_agent is None:
        _default_summary_agent = SummaryAgent()
    return _default_summary_agent


def summarize_tool_suggestions(tools: List[dict], query: str) -> str:
    """
    Function wrapper for tool summarization.
    Keeps compatibility with existing imports.
    """
    return _get_summary_agent().summarize_tools_suggestions(tools, query)


def summarize_workflow_suggestions(workflows: List[dict], query: str) -> str:
    """
    Function wrapper for workflow summarization.
    Keeps compatibility with existing imports.
    """
    return _get_summary_agent().summarize_workflows_suggestions(workflows, query)