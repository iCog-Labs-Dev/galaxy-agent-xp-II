class Normalizer:
    def normalize_tool(self, name):
        return name.strip().lower().title()

    def normalize_category(self, name):
        return name.strip().lower()
