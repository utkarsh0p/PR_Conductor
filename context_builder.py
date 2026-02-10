import base64
import requests

def fetch_readme(repo: str, headers: dict) -> str:
    url = f"https://api.github.com/repos/{repo}/readme"

    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code != 200:
        return ""

    data = r.json()
    content = data.get("content", "")
    if not content:
        return ""

    text = base64.b64decode(content).decode("utf-8", errors="ignore")
    return text.replace("\n", " ").replace("\r", " ")


def build_context(repo: str, headers: dict) -> dict:
    readme = fetch_readme(repo, headers)

    return {
        "readme_excerpt": " ".join(readme.split())[:300]
    }

