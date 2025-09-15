import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

GITHUB_API_URL = "https://api.github.com/repos/galaxyproject/iwc/contents/workflows"
RAW_BASE_URL = "https://raw.githubusercontent.com/galaxyproject/iwc/main/workflows"

# MAX_WORKFLOWS = 5 # Uncomment to limit the number of workflows processed
MAX_WORKFLOWS = None # Set to None to process all workflows

github_token = os.getenv("GITHUB_TOKEN")
if github_token:
    HEADERS = {
        "Authorization": f"token {github_token}"
    }
else:    
    print("⚠️ No GITHUB_TOKEN found in environment variables. Using unauthenticated requests may hit rate limits.")
    HEADERS = {}
     
def github_api_get(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def fetch_file_content(path):
    raw_url = f"{RAW_BASE_URL}/{path}"
    resp = requests.get(raw_url, headers=HEADERS)
    resp.raise_for_status()
    return resp.text

def parse_ga_content(ga_text):
    try:
        data = json.loads(ga_text)
        workflow_name = data.get("name", "unknown")
        steps = data.get("steps", {})
        number_of_steps = len(steps)
        tools_used = []

        for step in steps.values():
            if step.get("type") != "tool":
                continue

            tool_id = step.get("tool_id", "")
            name = step.get("name", "")
            version = step.get("tool_version", "")
            repo = step.get("tool_shed_repository", {})

            tool_info = {
                "id": tool_id,
                "name": name,
                "version": version,
                "owner": repo.get("owner", ""),
                "category": repo.get("name", ""),
                "tool_shed_url": repo.get("tool_shed", "")
            }

            if tool_info not in tools_used:
                tools_used.append(tool_info)

        return {
            "workflow_name": workflow_name,
            "number_of_steps": number_of_steps,
            "tools_used": tools_used,
        }
    except Exception as e:
        print(f"❌ Failed to parse .ga JSON: {e}")
        return {}

def scan_repo(category, repo_name):
    base_path = f"{category}/{repo_name}"
    url = f"{GITHUB_API_URL}/{category}/{repo_name}"
    try:
        repo_contents = github_api_get(url)
    except Exception as e:
        print(f"⚠️ Failed to get repo contents for {base_path}: {e}")
        return None

    workflow_files = []
    planemo_tests = []
    files_present = set()
    directories_present = set()
    readme_content = None

    for item in repo_contents:
        name = item["name"]
        if item["type"] == "file":
            files_present.add(name)
            if name.endswith(".ga"):
                ga_text = fetch_file_content(f"{base_path}/{name}")
                ga_info = parse_ga_content(ga_text)
                
                # Add file name and raw download URL
                raw_url = f"{RAW_BASE_URL}/{base_path}/{name}"
                ga_info.update({
                    "file_name": name,
                    "raw_download_url": raw_url
                })
                
                workflow_files.append(ga_info)

                test_file = name.replace(".ga", "-tests.yml")
                if test_file in [f["name"] for f in repo_contents if f["type"] == "file"]:
                    planemo_tests.append(test_file)

            if name == "README.md":
                try:
                    readme_content = fetch_file_content(f"{base_path}/{name}")
                except Exception as e:
                    print(f"⚠️ Failed to fetch README for {base_path}: {e}")
                    readme_content = None

        elif item["type"] == "dir":
            directories_present.add(name)

    repo_data = {
        "category": category.lower(),
        "workflow_repository": repo_name.lower(),
        "workflow_files": workflow_files,
        "planemo_tests": planemo_tests,
        "has_test_data": "test-data" in directories_present,
        "has_dockstore_yml": ".dockstore.yml" in files_present,
        "has_readme": "README.md" in files_present,
        "readme_content": readme_content,
        "has_changelog": "CHANGELOG.md" in files_present,
    }
    return repo_data

def main():
    print("🔍 Fetching top-level categories...")
    categories = github_api_get(GITHUB_API_URL)
    all_data = []
    workflow_count = 0

    for cat in categories:
        if cat["type"] != "dir":
            continue
        category = cat["name"]
        print(f"\n📂 Scanning category: {category}")
        try:
            repos = github_api_get(f"{GITHUB_API_URL}/{category}")
        except Exception as e:
            print(f"⚠️ Failed to get contents for {category}: {e}")
            continue

        for repo in repos:
            if repo["type"] != "dir":
                continue
            if MAX_WORKFLOWS is not None and workflow_count >= MAX_WORKFLOWS:
                print(f"\n✅ Reached MAX_WORKFLOWS limit: {MAX_WORKFLOWS}")
                break

            repo_name = repo["name"]
            print(f"  📁 Scanning workflow repo: {repo_name}")
            repo_data = scan_repo(category, repo_name)
            if repo_data:
                all_data.append(repo_data)
                workflow_count += 1

        if MAX_WORKFLOWS is not None and workflow_count >= MAX_WORKFLOWS:
            break

    # Save output with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"galaxy_iwc_workflows_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\n📦 Saved summary to {output_file}")

if __name__ == "__main__":
    main()