from bioblend.galaxy import GalaxyInstance
import os
import json
import time

class GalaxyValidator:
    def __init__(self, url, api_key, timeout=15, skip_validation=False, cache_file="", cache_ttl=1800):
        self.gi = GalaxyInstance(url=url, key=api_key)
        self.installed_tools = {}
        self.validation_ready = False
        self.skip_validation = skip_validation
        self.timeout = timeout
        self.cache_file = cache_file
        self.cache_ttl = cache_ttl
        self._refresh_tool_cache()

    def _load_cache(self):
        if not self.cache_file:
            return False
        if not os.path.exists(self.cache_file):
            return False
        try:
            mtime = os.path.getmtime(self.cache_file)
            if (time.time() - mtime) > self.cache_ttl:
                return False
            with open(self.cache_file, "r") as handle:
                payload = json.load(handle)
            tools = payload.get("installed_tools", {})
            if not isinstance(tools, dict) or len(tools) == 0:
                return False
            self.installed_tools = tools
            self.validation_ready = True
            print(f"⚡ Loaded installed tools cache: {self.cache_file}")
            return True
        except Exception:
            return False

    def _save_cache(self):
        if not self.cache_file:
            return
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)
            with open(self.cache_file, "w") as handle:
                json.dump({"installed_tools": self.installed_tools}, handle, indent=2)
        except Exception:
            pass

    def _refresh_tool_cache(self):
        """Fetches all installed tools and stores them by their Short Name."""
        if self.skip_validation:
            print("⏭️ Skipping Galaxy validation by configuration.")
            self.validation_ready = False
            return

        if self._load_cache():
            return

        print("🔍 Connecting to Galaxy to verify installed tools...")
        try:
            # Bioblend supports requests timeout through this value.
            self.gi.timeout = self.timeout
            tools = self.gi.tools.get_tools()
            for t in tools:
                full_id = t['id']
                if "/" in full_id:
                    short_name = full_id.split("/")[-2]
                else:
                    short_name = full_id
                self.installed_tools[short_name] = {
                    "full_id": full_id,
                    "version": t.get('version', '1.0.0')
                }
            self.validation_ready = True
            self._save_cache()
        except Exception as exc:
            print(f"⚠️ Galaxy validation unavailable ({exc}). Continuing without instance validation.")
            self.validation_ready = False

    def validate_and_fix_chain(self, predicted_chain, tool_mapping):
        """
        Checks each tool in the chain. If not on instance, 
        it tries to find a local alternative or skips it.
        """
        if not self.validation_ready:
            return predicted_chain

        validated_chain = []
        for tool_name in predicted_chain:
            if tool_name in self.installed_tools:
                validated_chain.append(tool_name)
            else:
                print(f"⚠️ Tool '{tool_name}' not found on this Galaxy instance. Skipping...")
                # Optional: Add logic here to find a fuzzy match 
                # (e.g., if 'bwa' is missing, look for 'bwa_mem')
        
        return validated_chain