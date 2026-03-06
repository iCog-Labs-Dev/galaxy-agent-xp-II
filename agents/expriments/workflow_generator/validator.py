from bioblend.galaxy import GalaxyInstance

class GalaxyValidator:
    def __init__(self, url, api_key):
        self.gi = GalaxyInstance(url=url, key=api_key)
        self.installed_tools = {}
        self._refresh_tool_cache()

    def _refresh_tool_cache(self):
        """Fetches all installed tools and stores them by their Short Name."""
        print("🔍 Connecting to Galaxy to verify installed tools...")
        tools = self.gi.tools.get_tools()
        for t in tools:
            full_id = t['id']
            # Apply the 'Second-to-Last' Logic
            if "/" in full_id:
                short_name = full_id.split("/")[-2]
            else:
                short_name = full_id
            
            # Store the full ID and version
            self.installed_tools[short_name] = {
                "full_id": full_id,
                "version": t.get('version', '1.0.0')
            }

    def validate_and_fix_chain(self, predicted_chain, tool_mapping):
        """
        Checks each tool in the chain. If not on instance, 
        it tries to find a local alternative or skips it.
        """
        validated_chain = []
        for tool_name in predicted_chain:
            if tool_name in self.installed_tools:
                validated_chain.append(tool_name)
            else:
                print(f"⚠️ Tool '{tool_name}' not found on this Galaxy instance. Skipping...")
                # Optional: Add logic here to find a fuzzy match 
                # (e.g., if 'bwa' is missing, look for 'bwa_mem')
        
        return validated_chain