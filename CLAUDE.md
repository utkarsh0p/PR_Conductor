# PR Conductor

Automated, context-aware code review service for GitHub Pull Requests using LLMs.

## Architecture

Three components:

```
pr-conductor-cli (npm package)     frontend (Vite + vanilla JS)     backend (FastAPI + Python)
       │                                  │                                │
       │ adds workflow file               │ OAuth login + registration     │ review logic + API
       │ to user's repo                   │                                │
       └──────────────────────────────────┴────────────────────────────────┘
                                          │
                                     MongoDB Atlas
                                  (stores user tokens)
```

### User Flow

1. User visits frontend → clicks "Login with GitHub" → OAuth flow captures GitHub token
2. User enters Gemini API key → clicks Register
3. Backend generates a UUID `secret_key`, stores `{ secret_key, github_token, gemini_key }` in MongoDB
4. Frontend displays the secret key with instructions to add it as a GitHub repo secret (`PR_CONDUCTOR_SECRET`)
5. User runs `npx pr-conductor` in their repo → adds the workflow file
6. When a PR is opened, the workflow sends `{ repo, pr_number, title, secret_key }` to the backend
7. Backend looks up the user's tokens from DB using `secret_key`, fetches the diff, sends to Gemini, posts review comments on the PR

## Project Structure

```
PR_Conductor/
├── backend/                  # FastAPI backend
│   ├── main.py               # All endpoints: /auth/github, /auth/github/callback, /register, /review
│   ├── parse_diff.py         # Parses unified diff format to extract added lines
│   ├── context_builder.py    # Fetches repo README for LLM context
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Container config
│   └── .env                  # Environment variables (not committed)
│
├── frontend/                 # Vite vanilla JS frontend
│   ├── index.html
│   └── src/
│       ├── main.js           # OAuth flow handling, registration form, setup guide UI
│       └── style.css         # GitHub dark theme styling
│
├── pr-conductor-cli/         # npm package (published as `pr-conductor`)
│   ├── package.json          # npm config, bin entry
│   ├── bin/cli.js            # CLI script that copies workflow template
│   └── templates/reviewer.yml # GitHub Actions workflow template
│
└── .github/workflows/        # This repo's own workflow (legacy, from initial version)
    └── reviewer.yml
```

## Backend Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/auth/github` | Redirects user to GitHub OAuth authorization page |
| GET | `/auth/github/callback` | Receives OAuth code from GitHub, exchanges for access token, redirects to frontend with token |
| POST | `/register` | Accepts `{ github_token, gemini_key }`, generates UUID secret key, stores in MongoDB, returns secret key |
| POST | `/review` | Accepts `{ repo, pr_number, title, secret_key }`, looks up tokens from DB, fetches PR diff, runs LLM review, posts comments on PR |

## Environment Variables (backend/.env)

```
MONGO_URI=mongodb+srv://...           # MongoDB Atlas connection string
GITHUB_CLIENT_ID=Ov23liGBd65t9wluT8sw # GitHub OAuth App client ID
GITHUB_CLIENT_SECRET=...              # GitHub OAuth App client secret
FRONTEND_URL=http://localhost:5173    # Frontend URL for OAuth redirect
```

## Running Locally

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# runs on http://localhost:8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
# runs on http://localhost:5173
```

## Key Technical Details

- LLM: Google Gemini (`models/gemini-3-flash-preview`) via LangChain with structured output
- Structured output schema: `ReviewResult` with max 5 `ReviewComment` objects (file, line, severity, message)
- Review focus: bugs, logic errors, security. Ignores: formatting, style, comments
- Comments are posted as inline PR comments on the exact changed lines. Falls back to a summary comment if inline posting fails
- The `parse_diff.py` extracts only added lines (`+` lines) with their line numbers from unified diff format
- `context_builder.py` fetches the repo's README (first 300 chars) to give the LLM context about the project
- CORS is set to allow all origins (`*`) — restrict this in production
- GitHub OAuth scope: `repo` (read/write access to repos, PRs, issues)

## Database (MongoDB Atlas)

Database: `pr-conductor`
Collection: `users`

Document shape:
```json
{
  "secret_key": "uuid-v4-string",
  "github_token": "gho_xxxx",
  "gemini_key": "AIza_xxxx",
  "created_at": "datetime"
}
```

Lookup is done by `secret_key` field. No indexes created yet — add one on `secret_key` for production.

## npm Package

- Package name: `pr-conductor` (published on npmjs.com)
- Current version: 1.1.0
- Account: utkarsh0p on npm
- 2FA: enabled via phone security key
- The CLI copies `templates/reviewer.yml` into the user's `.github/workflows/` directory

## Things to Change When Deploying

1. **`frontend/src/main.js`**: Change `API_URL` from `http://localhost:8000` to your backend domain
2. **`backend/.env`**: Update `FRONTEND_URL` from `http://localhost:5173` to your frontend domain
3. **`pr-conductor-cli/templates/reviewer.yml`**: Replace `https://your-pr-conductor-backend.com` with your actual backend URL, then bump version and `npm publish`
4. **GitHub OAuth App settings** (github.com/settings/developers): Update Homepage URL and Callback URL to production domains
5. **CORS**: Restrict `allow_origins` from `["*"]` to your frontend domain only
6. **MongoDB**: Add index on `secret_key` field for performance
7. **HTTPS**: Backend must use HTTPS in production (tokens are sent over the network)
8. **Encrypt tokens**: GitHub tokens and Gemini keys are stored as plain text in MongoDB — encrypt them for production

## GitHub OAuth App

- Name: CodeSentinal (can be renamed to PR Conductor in GitHub Developer Settings)
- Client ID: Ov23liGBd65t9wluT8sw
- Callback URL (local): http://localhost:8000/auth/github/callback
- Scope: repo
