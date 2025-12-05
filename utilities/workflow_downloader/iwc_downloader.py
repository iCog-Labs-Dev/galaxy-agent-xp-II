import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------
#   ENV CONFIG (NO MORE HARD-CODING)
# --------------------------------------
GITHUB_API_URL = "https://api.github.com/repos/galaxyproject/iwc/contents/workflows"
RAW_BASE_URL = "https://raw.githubusercontent.com/galaxyproject/iwc/main/workflows"

MAX_WORKFLOWS = 2

github_token = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {github_token}"} if github_token else {}


def github_api_get(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def fetch_raw(path):
    url = f"{RAW_BASE_URL}/{path}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.text


# --------------------------------------
#   PARSE GA FILE
# --------------------------------------
def parse_ga_file(ga_text, file_name, raw_download_url):
    """
    ga_text: raw text from *.ga file (JSON)
    file_name: name of the GA file
    raw_download_url: GitHub raw URL
    """

    try:
        ga_dict = json.loads(ga_text)
    except json.JSONDecodeError:
        print(f"⚠️ Cannot parse GA file: {file_name}")
        return None

    workflow_name = ga_dict.get("name", file_name)
    steps = ga_dict.get("steps", {})

    step_list = []
    tools_used = []

    for step_id, step in steps.items():
        tool_id = step.get("tool_id")
        tool_version = step.get("tool_version")
        tool_shed_repo = step.get("tool_shed_repository", {}) or {}

        step_info = {
            "id": step_id,
            "name": step.get("name"),
            "tool_id": tool_id,
            "tool_version": tool_version,
            "tool_shed_repository": {
                "owner": tool_shed_repo.get("owner"),
                "name": tool_shed_repo.get("name"),
                "tool_shed": tool_shed_repo.get("tool_shed_url"),
            },
        }
        step_list.append(step_info)

        # required for schema
        if tool_id:
            tools_used.append({
                "id": tool_id,
                "name": step.get("name") or "",
                "version": tool_version or "",
                "owner": tool_shed_repo.get("owner") or "",
                "category": tool_shed_repo.get("name") or "",
                "tool_shed_url": tool_shed_repo.get("tool_shed_url") or "",
            })

    return {
        "workflow_name": workflow_name,
        "number_of_steps": len(step_list),
        "file_name": file_name,
        "raw_download_url": raw_download_url,
        "steps": step_list,
        "tools_used": tools_used,
    }


# --------------------------------------
#   SCAN INDIVIDUAL REPO
# --------------------------------------
def scan_repo(category, repo_name):
    base_path = f"{category}/{repo_name}"
    url = f"{GITHUB_API_URL}/{category}/{repo_name}"

    try:
        repo_contents = github_api_get(url)
    except Exception as e:
        print(f"⚠️ Failed to scan repo '{repo_name}': {e}")
        return None

    workflow_files = []
    files_present = set()
    directories_present = set()
    readme_content = None

    for item in repo_contents:
        name = item["name"]

        if item["type"] == "file":
            files_present.add(name)

            if name.endswith(".ga"):
                path = f"{base_path}/{name}"
                ga_text = fetch_raw(path)

                # FIXED: properly call with all 3 arguments
                parsed = parse_ga_file(
                    ga_text,
                    file_name=name,
                    raw_download_url=f"{RAW_BASE_URL}/{path}"
                )

                if parsed:
                    workflow_files.append(parsed)

            if name == "README.md":
                try:
                    readme_content = fetch_raw(f"{base_path}/{name}")
                except:
                    readme_content = None

        elif item["type"] == "dir":
            directories_present.add(name)

    return {
        "category": category.lower(),
        "workflow_repository": repo_name.lower(),
        "workflow_files": workflow_files,
        "has_test_data": "test-data" in directories_present,
        "has_readme": "README.md" in files_present,
        "has_dockstore_yml": ".dockstore.yml" in files_present,
        "has_changelog": "CHANGELOG.md" in files_present,
        "readme_content": readme_content,
    }


# --------------------------------------
#   MAIN RUNNER
# --------------------------------------
def main():
    print("🔍 Fetching workflow categories...")
    categories = github_api_get(GITHUB_API_URL)
    all_data = []
    count = 0

    for cat in categories:
        if cat["type"] != "dir":
            continue

        category = cat["name"]
        print(f"\n📂 Category: {category}")

        repos = github_api_get(f"{GITHUB_API_URL}/{category}")

        for repo in repos:
            if repo["type"] != "dir":
                continue

            if MAX_WORKFLOWS is not None and count >= MAX_WORKFLOWS:
                break

            repo_name = repo["name"]
            print(f"  📁 Repo: {repo_name}")

            repo_data = scan_repo(category, repo_name)
            if repo_data:
                all_data.append(repo_data)
                count += 1

        if MAX_WORKFLOWS is not None and count >= MAX_WORKFLOWS:
            break

    # save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(
        output_dir, f"galaxy_iwc_workflows_{timestamp}.json"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\n📦 Saved complete workflow dump to: {output_file}")


if __name__ == "__main__":
    main()
