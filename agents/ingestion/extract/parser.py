import re

class WorkflowParser:
    INPUT_PATTERNS = [
        r"##\s*Inputs(?:.*?)(?=##\s*Outputs|##\s*[A-Z]|$)",
        r"#\s*Inputs(?:.*?)(?=#\s*Outputs|#\s*[A-Z]|$)",
        r"Inputs\s*\n[-\d\.\)\s\w\W]*?(?=Outputs|$)"
    ]

    OUTPUT_PATTERNS = [
        r"##\s*Outputs(?:.*)",
        r"#\s*Outputs(?:.*)",
        r"Outputs\s*\n[-\d\.\)\s\w\W]*"
    ]

    def extract_io(self, readme: str):
        if not readme:
            return [], []

        inputs = []
        outputs = []

        # Extract blocks
        input_block = self._extract_block(self.INPUT_PATTERNS, readme)
        output_block = self._extract_block(self.OUTPUT_PATTERNS, readme)

        # Parse list items from blocks
        if input_block:
            inputs = self._extract_list_items(input_block)

        if output_block:
            outputs = self._extract_list_items(output_block)

        return inputs, outputs

    def _extract_block(self, patterns, text):
        for p in patterns:
            match = re.search(p, text, flags=re.S | re.I)
            if match:
                return match.group(0)
        return ""

    def _extract_list_items(self, block: str):
        lines = block.split("\n")
        items = []
        for line in lines:
            line = line.strip()
            if re.match(r"^(\d+[\.\)])\s+", line) or \
               re.match(r"^[-*•]\s+", line):
                # Remove markdown bullets/numbers
                line = re.sub(r"^[-*•]\s+", "", line)
                line = re.sub(r"^\d+[\.\)]\s+", "", line)
                items.append(line.strip())
        return items

    # ------------------- Canonical text for embedding -------------------
    def build_workflow_text(self, workflow: dict) -> str:
        """
        Build canonical text for embedding a workflow entity.
        """
        repo = workflow.get("workflow_repository", "")
        category = workflow.get("category", "")
        readme = workflow.get("readme_cleaned", "")

        # Extract inputs and outputs
        inputs, outputs = self.extract_io(readme)

        tools = workflow.get("tool_names", [])

        text_parts = [
            f"Repository: {repo}",
            f"Category: {category}",
            f"Description: {readme}",
            f"Tools: {', '.join(tools)}",
            f"Inputs: {', '.join(inputs)}",
            f"Outputs: {', '.join(outputs)}"
        ]

        return " ".join(filter(None, text_parts))
