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
