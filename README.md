# PR Conductor

PR Conductor is an automated code review service that analyzes GitHub Pull Requests using LLMs and posts contextual, inline review comments directly on your PRs. It catches bugs, logic errors, and security issues before they reach production.

## How It Works

```
PR Opened on GitHub
        |
        v
GitHub Actions workflow triggers
        |
        v
Sends PR metadata + secret key to PR Conductor backend
        |
        v
Backend fetches the diff via GitHub API
        |
        v
Diff is parsed, repo context (README) is extracted
        |
        v
Everything is sent to Google Gemini with structured output constraints
        |
        v
Gemini returns up to 5 review comments (file, line, severity, message)
        |
        v
Comments are posted as inline review comments on the PR
```

## Features

- **Inline PR Comments** — Review comments are posted on the exact lines that changed, not as a generic wall of text.
- **Structured LLM Output** — Uses Pydantic schemas with LangChain to enforce consistent, parseable responses from the LLM.
- **Severity Levels** — Each comment is tagged as `low`, `medium`, or `high` severity so you can prioritize what matters.
- **Focused Reviews** — Configured to catch bugs, logic errors, and security issues while ignoring formatting and style nitpicks.
- **Multi-User Support** — Each user authenticates via GitHub OAuth, provides their own Gemini API key, and receives a unique secret key for their repos.
- **Zero Config for Reviewers** — Once set up, reviews happen automatically on every new PR with no manual intervention.

## Architecture

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│   Frontend (Vite)    │     │  Backend (FastAPI)    │     │  MongoDB Atlas   │
│                      │     │                      │     │                  │
│  - GitHub OAuth      │────>│  - /auth/github       │     │  - User tokens   │
│  - Gemini key input  │     │  - /auth/callback     │<───>│  - Gemini keys   │
│  - Secret key display│<────│  - /register          │     │  - Secret keys   │
│  - Setup guide       │     │  - /review            │     │                  │
└──────────────────────┘     └──────────────────────┘     └──────────────────┘
                                      ^
                                      |
                             GitHub Actions Workflow
                             (triggered on PR open)
```

| Component | Tech Stack | Purpose |
|-----------|-----------|---------|
| Frontend | Vite + Vanilla JS | User registration, OAuth flow, setup instructions |
| Backend | FastAPI + Python | OAuth handling, user management, PR review logic, GitHub API integration |
| Database | MongoDB Atlas | Stores user credentials linked to unique secret keys |
| LLM | Google Gemini Flash via LangChain | Code review analysis with structured output |
| CLI | Node.js (npm package) | Adds the GitHub Actions workflow to user repos |

## Getting Started

### 1. Register

Visit [frontend.cember.in](https://frontend.cember.in) and sign in with your GitHub account. Enter your [Gemini API key](https://aistudio.google.com/apikey) and you'll receive a unique secret key.

### 2. Add the Secret Key to Your Repo

Go to your GitHub repository:

**Settings** > **Secrets and variables** > **Actions** > **New repository secret**

- Name: `PR_CONDUCTOR_SECRET`
- Value: *(paste the secret key you received)*

### 3. Install the Workflow

```bash
npx pr-conductor
```

This adds a GitHub Actions workflow file to your repo that triggers on every new pull request.

### 4. Open a PR

That's it. Open a pull request and PR Conductor will automatically review the changes and post inline comments.

## Project Structure

```
PR_Conductor/
├── backend/
│   ├── main.py               # FastAPI app — all endpoints
│   ├── parse_diff.py          # Unified diff parser
│   ├── context_builder.py     # Repo context extraction (README)
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container
│   └── docker-compose.yml     # Backend deployment config
│
├── frontend/
│   ├── src/
│   │   ├── main.js            # OAuth flow, registration, setup guide
│   │   └── style.css          # GitHub-themed dark UI
│   ├── index.html
│   ├── Dockerfile             # Frontend container
│   └── docker-compose.yml     # Frontend deployment config
│
├── pr-conductor-cli/
│   ├── bin/cli.js             # CLI entry point
│   ├── templates/reviewer.yml # GitHub Actions workflow template
│   └── package.json           # npm package config
│
└── .github/workflows/
    └── reviewer.yml           # This repo's own PR Conductor workflow
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/auth/github` | Redirects to GitHub OAuth authorization |
| `GET` | `/auth/github/callback` | Handles OAuth callback, exchanges code for token |
| `POST` | `/register` | Stores user credentials, returns unique secret key |
| `POST` | `/review` | Receives PR data, runs LLM review, posts comments |

### POST /review

**Request body** (sent by the GitHub Actions workflow):

```json
{
  "repo": "username/repo-name",
  "pr_number": 4,
  "title": "Fix authentication bug",
  "secret_key": "uuid-v4-string"
}
```

**What happens:**

1. Validates the secret key against the database
2. Retrieves the user's GitHub token and Gemini API key
3. Fetches changed files from the GitHub API
4. Parses the unified diff to extract added lines with line numbers
5. Fetches repo context (README excerpt)
6. Sends everything to Gemini with structured output constraints
7. Posts up to 5 inline review comments on the PR

**Response:**

```json
{
  "msg": "review completed",
  "comments_posted": 3
}
```

## Review Output Schema

The LLM is constrained to return structured output matching this schema:

```python
class ReviewComment:
    file: str                              # e.g. "src/auth.py"
    line: int                              # e.g. 42
    severity: "low" | "medium" | "high"    # priority level
    message: str                           # review comment text

class ReviewResult:
    comments: List[ReviewComment]          # max 5 comments per review
```

Reviews focus on **bugs, logic errors, and security**. Formatting, style, and comment-related issues are explicitly ignored.

## Deployment

The frontend and backend are deployed as separate Docker containers behind Nginx reverse proxies.

```bash
# Backend
cd backend
docker compose up -d --build

# Frontend
cd frontend
docker compose up -d --build
```

### Environment Variables (backend/.env)

```
MONGO_URI=mongodb+srv://...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
FRONTEND_URL=https://frontend.cember.in
```

### Nginx Configuration

Each subdomain proxies to its respective container:

- `frontend.cember.in` -> `localhost:5173`
- `backend.cember.in` -> `localhost:8000`

SSL is handled via Certbot/Let's Encrypt.

## npm Package

PR Conductor is available as an npm package for easy workflow installation:

```bash
npx pr-conductor
```

- **Package name:** [pr-conductor](https://www.npmjs.com/package/pr-conductor)
- **Current version:** 1.2.0

## Requirements

- Python 3.11+
- Node.js 20+
- Docker
- MongoDB Atlas account
- GitHub OAuth App
- Gemini API key

## License

MIT
