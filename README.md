# PR Conductor

PR Conductor is a backend service that orchestrates automated, context-aware
code reviews for GitHub Pull Requests using LLMs.

## Responsibilities
- Receives PR events
- Fetches diffs and repository context
- Builds review prompts
- Returns structured review feedback

## Requirements
- Python 3.10+
- Docker

## Environment Variables
- GITHUB_TOKEN
- GEMINI_API_KEY

## Run
```bash
docker build -t pr-conductor .
docker run -p 8000:8000 --env-file .env pr-conductor
