import re
import unicodedata

class Normalizer:
    def normalize_tool(self, name: str):
        if not name:
            return None
        name = self._clean_text(name)
        return name.strip()

    def normalize_category(self, name: str):
        if not name:
            return None
        name = self._clean_text(name)
        return name.lower().strip()

    def normalize_readme(self, text: str):
        if not text:
            return ""

        text = self._clean_text(text)

        
        text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)        
        text = re.sub(r"\[[^\]]*\]\([^)]+\)", r"\1", text)       
        text = re.sub(r"`([^`]*)`", r"\1", text)              
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)            
        text = re.sub(r"__([^_]+)__", r"\1", text)                 
        text = re.sub(r"[*#>-]", " ", text)                      

        # Remove repeated whitespace
        return re.sub(r"\s+", " ", text).strip()

    def _clean_text(self, text: str):
        """Normalize Unicode, remove garbage characters."""
        if not isinstance(text, str):
            return str(text)

        text = unicodedata.normalize("NFKD", text)
        text = text.replace("\ufeff", "")
        return text

    def build_tool_text(self, tool: dict) -> str:
        """
        Build canonical text for embedding a Tool.
        """
        name = self.normalize_tool(tool.get("name", ""))
        tool_id = tool.get("id", "")
        description = self.normalize_readme(tool.get("description", ""))
        help_text = self.normalize_readme(tool.get("help", ""))
        categories = ", ".join(filter(None, [self.normalize_category(c) for c in tool.get("categories", [])]))
        version = tool.get("version", "")

        text_parts = [f"Name: {name}", f"ID: {tool_id}", f"Description: {description}",
                      f"Help: {help_text}", f"Categories: {categories}", f"Version: {version}"]

        return " ".join(filter(None, text_parts))

    def build_workflow_text(self, wf: dict) -> str:
        """
        Build canonical text for embedding a Workflow.
        """
        repo = self.normalize_tool(wf.get("workflow_repository", ""))
        category = self.normalize_category(wf.get("category", ""))
        readme = self.normalize_readme(wf.get("readme_cleaned", ""))
        tools = ", ".join([self.normalize_tool(t) for t in wf.get("tool_names", [])])

        text_parts = [f"Repository: {repo}", f"Category: {category}", f"Description: {readme}", f"Tools: {tools}"]

        return " ".join(filter(None, text_parts))
