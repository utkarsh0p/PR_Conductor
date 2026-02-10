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

## Key point to take care of
- Change the endpoint of instance in the workflow.yml to your endpoint ( backend ) wich has your github_token
- Otherwise it will not post the pr review comment

## Run
```bash
docker build -t pr-conductor .
docker run -p 8000:8000 --env-file .env pr-conductor
