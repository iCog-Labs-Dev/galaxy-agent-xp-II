# build_bridge_dict.py
import pandas as pd
import json

def build():
    df = pd.read_csv("data/latest/workflow-connections.csv", sep='|', engine='python')
    # Standardize column names
    df.columns = [c.strip() for c in df.columns]
    all_ids = pd.concat([df['in_tool'], df['out_tool']]).dropna().unique()
    
    mapping = {}
    for full_id in all_ids:
        full_id = full_id.strip()
        # Galaxy Logic: Use second-to-last part for Toolshed tools
        if "/" in full_id:
            parts = full_id.split("/")
            # If the ID ends in a version (e.g., /1.0.1), grab the name before it
            short_name = parts[-2] if len(parts) > 1 else parts[-1]
        else:
            short_name = full_id
        
        mapping[short_name] = full_id
    
    with open("log/data/tool_id_dict.txt", "w") as f:
        json.dump(mapping, f, indent=4)
    print("✅ Bridge dictionary standardized to Galaxy logic.")

if __name__ == "__main__": build()