import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])


class GeminiLLM:
    """
    Gemini LLM adapter compatible with:
    - Text2CypherRetriever (Cypher generation)
    - GraphRAG (final answer generation)
    """

    def __init__(self, model_name: str = "models/gemini-2.5-flash"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> str:
        """
        Core text generation method.
        Used internally by invoke().
        """
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0
            )
        )
        return getattr(response, "text", "") or ""

    # REQUIRED response object (GraphRAG expects .content)
    class Response:
        def __init__(self, text: str):
            self.content = text

    def invoke(self, *args, **kwargs):
        """
        Universal invoke method.
        """
        if not args:
            raise ValueError("invoke() called without prompt")

        prompt = args[0]
        text = self.generate(prompt)
        return self.Response(text)
