import os
import json
import uuid
import requests
from typing import List, Literal
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from pymongo import MongoClient

from parse_diff import parse_diff
from context_builder import build_context

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["pr-conductor"]
users_collection = db["users"]

class RegisterRequest(BaseModel):
    gemini_key: str
    github_token: str


class ReviewComment(BaseModel):
    file: str
    line: int
    severity: Literal["low", "medium", "high"]
    message: str


class ReviewResult(BaseModel):
    comments: List[ReviewComment] = Field(default_factory=list, max_length=5)


def get_latest_commit_sha(repo: str, pr_number: int, headers: dict) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()["head"]["sha"]


def post_pr_summary(repo: str, pr_number: int, comments: List[ReviewComment], headers: dict):
    if not comments:
        return

    body = "🤖 **Automated Review Summary**\n\n"
    for c in comments:
        body += f"- `{c.file}:{c.line}` ({c.severity}): {c.message}\n"

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    requests.post(url, headers=headers, json={"body": body})


def post_inline_comments(repo: str, pr_number: int, comments: List[ReviewComment], valid_lines: set, headers: dict):
    if not comments:
        return

    commit_sha = get_latest_commit_sha(repo, pr_number, headers)
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
        r = requests.post(url, headers=headers, json=payload)

        if r.status_code in (200, 201):
            posted.append(c)

    if not posted:
        post_pr_summary(repo, pr_number, comments, headers)


@app.get("/auth/github")
async def github_login():
    return RedirectResponse(f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=repo")


@app.get("/auth/github/callback")
async def github_callback(code: str):
    r = requests.post(
        "https://github.com/login/oauth/access_token",
        json={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=20,
    )

    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="GitHub OAuth failed")

    data = r.json()
    access_token = data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")

    from urllib.parse import quote
    return RedirectResponse(f"{FRONTEND_URL}?github_token={quote(access_token)}")


@app.post("/register")
async def register(data: RegisterRequest):
    secret_key = str(uuid.uuid4())

    users_collection.insert_one({
        "secret_key": secret_key,
        "github_token": data.github_token,
        "gemini_key": data.gemini_key,
        "created_at": datetime.now()
    })

    return {"secret_key": secret_key}


@app.post("/review")
async def review(request: Request):
    payload = await request.json()

    repo = payload["repo"]
    pr_number = int(payload["pr_number"])
    title = payload.get("title", "")
    secret_key = payload.get("secret_key")

    if not secret_key:
        raise HTTPException(status_code=401, detail="Missing secret_key")

    user = users_collection.find_one({"secret_key": secret_key})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid secret_key")

    github_token = user["github_token"]
    gemini_key = user["gemini_key"]

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }

    llm = ChatGoogleGenerativeAI(
        model="models/gemini-3-flash-preview",
        temperature=0,
        google_api_key=gemini_key
    )
    structured_llm = llm.with_structured_output(ReviewResult)

    files_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    r = requests.get(files_url, headers=headers, timeout=20)
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

    context = build_context(repo, headers)

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
        valid_lines=valid_lines,
        headers=headers
    )

    return {
        "msg": "review completed",
        "comments_posted": len(llm_result.comments)
    }
