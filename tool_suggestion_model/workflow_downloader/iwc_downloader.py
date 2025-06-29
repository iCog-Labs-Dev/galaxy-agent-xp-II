import requests
import json
import os

GITHUB_API_URL = "https://api.github.com/repos/galaxyproject/iwc/contents/workflows"
RAW_BASE_URL = "https://raw.githubusercontent.com/galaxyproject/iwc/main/workflows"

HEADERS = {
    # We will add a personal access token here if needed for higher rate limits:
    # "Authorization": "token YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
}

def github_api_get(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def fetch_file_content(path):
    # fetch raw file content via raw.githubusercontent.com
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
            tool_id = step.get("tool_id") or step.get("tool_shed") or None
            if tool_id and tool_id not in tools_used:
                tools_used.append(tool_id)
        return {
            "workflow_name": workflow_name,
            "number_of_steps": number_of_steps,
            "tools_used": tools_used,
        }
    except Exception as e:
        print(f"Failed to parse .ga JSON: {e}")
        return {}

def scan_repo(category, repo_name):
    base_path = f"{category}/{repo_name}"
    url = f"{GITHUB_API_URL}/{category}/{repo_name}"
    try:
        repo_contents = github_api_get(url)
    except Exception as e:
        print(f"Failed to get repo contents for {base_path}: {e}")
        return None

    workflow_files = []
    planemo_tests = []
    files_present = set()
    directories_present = set()

    for item in repo_contents:
        name = item["name"]
        if item["type"] == "file":
            files_present.add(name)
            if name.endswith(".ga"):
                # fetch .ga content and parse
                ga_text = fetch_file_content(f"{base_path}/{name}")
                ga_info = parse_ga_content(ga_text)
                ga_info["file_name"] = name
                workflow_files.append(ga_info)
                # check corresponding tests file
                test_file = name.replace(".ga", "-tests.yml")
                if test_file in [f["name"] for f in repo_contents if f["type"] == "file"]:
                    planemo_tests.append(test_file)
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
        "has_changelog": "CHANGELOG.md" in files_present,
    }
    return repo_data

def main():
    print("Fetching top-level categories...")
    categories = github_api_get(GITHUB_API_URL)
    all_data = []

    for cat in categories:
        if cat["type"] != "dir":
            continue
        category = cat["name"]
        print(f"Scanning category: {category}")
        try:
            repos = github_api_get(f"{GITHUB_API_URL}/{category}")
        except Exception as e:
            print(f"Failed to get category contents {category}: {e}")
            continue

        for repo in repos:
            if repo["type"] != "dir":
                continue
            repo_name = repo["name"]
            print(f"  Scanning workflow repo: {repo_name}")
            repo_data = scan_repo(category, repo_name)
            if repo_data:
                all_data.append(repo_data)

    # Save output
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "iwc_workflows_summary.json")
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved summary to {output_file}")

if __name__ == "__main__":
    main()
