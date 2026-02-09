from bioblend.galaxy import GalaxyInstance
import csv

api_key = "bcdfedaffa33cc26f876f4e8ecbe2815"
workflow_id = "7b48649b0ce3950f"

# gi = GalaxyInstance(url="https://usegalaxy.org/", key=api_key)

# EU Instance details
URL = "https://usegalaxy.org/"
API_KEY = "bcdfedaffa33cc26f876f4e8ecbe2815" 
gi = GalaxyInstance(url=URL, key=API_KEY)

# 1. Get ALL published workflows (this can be thousands)
print("Fetching published workflows list...")
published_wfs = gi.workflows.get_workflows(published=True)
print(f"Found {len(published_wfs)} published workflows.")

# 2. Open a CSV to save connections
with open('eu_workflow_connections.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['source_tool', 'target_tool', 'workflow_id'])

    for wf_info in published_wfs[:100]: # Limit to first 100 for testing
        try:
            wf = gi.workflows.export_workflow_dict(wf_info['id'])
            steps = wf['steps']
            
            for step_id, step in steps.items():
                target_tool = step.get('tool_id') or "Input"
                connections = step.get('input_connections', {})
                
                for input_name, conn in connections.items():
                    conn_list = conn if isinstance(conn, list) else [conn]
                    for c in conn_list:
                        source_id = str(c['id'])
                        source_tool = steps[source_id].get('tool_id') or "Input"
                        
                        # Save the connection
                        writer.writerow([source_tool, target_tool, wf_info['id']])
            
            print(f"Processed: {wf_info['name']}")
        except Exception as e:
            print(f"Skipping {wf_info['id']} due to error: {e}")

print("Done! Data saved to eu_workflow_connections.csv")