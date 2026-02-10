import os
import json
import requests
from typing import List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from parse_diff import parse_diff
from context_builder import build_context

load_dotenv()

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN not set")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

class ReviewComment(BaseModel):
    file: str
    line: int
    severity: Literal["low", "medium", "high"]
    message: str


class ReviewResult(BaseModel):
    comments: List[ReviewComment] = Field(default_factory=list, max_length=5)


llm = ChatGoogleGenerativeAI(
    model="models/gemini-3-flash-preview",
    temperature=0
)

structured_llm = llm.with_structured_output(ReviewResult)


def get_latest_commit_sha(repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()["head"]["sha"]


def post_pr_summary(repo: str, pr_number: int, comments: List[ReviewComment]):
    if not comments:
        return

    body = "🤖 **Automated Review Summary**\n\n"
    for c in comments:
        body += f"- `{c.file}:{c.line}` ({c.severity}): {c.message}\n"

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    requests.post(url, headers=HEADERS, json={"body": body})


def post_inline_comments(repo: str, pr_number: int, comments: List[ReviewComment], valid_lines: set):
    if not comments:
        return

    commit_sha = get_latest_commit_sha(repo, pr_number)
    posted = []

    for c in comments:
        if (c.file, c.line) not in valid_lines:
            continue

        payload = {
            "body": f"**Severity: {c.severity.upper()}**\n\n{c.message}",
            "commit_id": commit_sha,
            "path": c.file,
            "line": c.line,
            "side": "RIGHT",
        }

        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
        r = requests.post(url, headers=HEADERS, json=payload)

        if r.status_code in (200, 201):
            posted.append(c)

    if not posted:
        post_pr_summary(repo, pr_number, comments)


@app.post("/review")
async def review(request: Request):
    payload = await request.json()

    repo = payload["repo"]
    pr_number = int(payload["pr_number"])
    title = payload.get("title", "")

    files_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    r = requests.get(files_url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch PR files")

    files = r.json()

    file_changes = []
    valid_lines = set()

    for f in files:
        if f.get("patch"):
            parsed = parse_diff(f["patch"])
            if parsed:
                file_changes.append({
                    "file": f["filename"],
                    "changes": parsed
                })
                for c in parsed:
                    valid_lines.add((f["filename"], c["line"]))

    context = build_context(repo, HEADERS)

    llm_input = {
        "repo": repo,
        "pull_request": {
            "number": pr_number,
            "title": title
        },
        "context": context,
        "changes": file_changes,
        "review_rules": {
            "focus": ["bugs", "logic errors", "security"],
            "ignore": ["formatting", "style", "comments"],
            "max_comments": 5
        }
    }

    llm_result: ReviewResult = structured_llm.invoke(
        json.dumps(llm_input)
    )

    post_inline_comments(
        repo=repo,
        pr_number=pr_number,
        comments=llm_result.comments,
        valid_lines=valid_lines
    )

    return {
        "msg": "review completed",
        "comments_posted": len(llm_result.comments)
    }
