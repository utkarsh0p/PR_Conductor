#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const workflowDir = path.join(process.cwd(), ".github", "workflows");
const templatePath = path.join(__dirname, "..", "templates", "reviewer.yml");
const destPath = path.join(workflowDir, "pr-conductor.yml");

const SETUP_URL = "https://frontend.cember.in/";

if (fs.existsSync(destPath)) {
  console.log("");
  console.log("  \x1b[33mℹ\x1b[0m  Workflow already exists at .github/workflows/pr-conductor.yml");
  console.log("");
  console.log("  Complete setup at: \x1b[36m" + SETUP_URL + "\x1b[0m");
  console.log("");
  process.exit(0);
}

fs.mkdirSync(workflowDir, { recursive: true });
fs.copyFileSync(templatePath, destPath);

console.log("");
console.log("  \x1b[32m✓\x1b[0m  PR Conductor workflow added!");
console.log("");
console.log("  \x1b[90m┌─────────────────────────────────────────────┐\x1b[0m");
console.log("  \x1b[90m│\x1b[0m                                             \x1b[90m│\x1b[0m");
console.log("  \x1b[90m│\x1b[0m   Complete setup at:                        \x1b[90m│\x1b[0m");
console.log("  \x1b[90m│\x1b[0m   \x1b[36m" + SETUP_URL + "\x1b[0m              \x1b[90m│\x1b[0m");
console.log("  \x1b[90m│\x1b[0m                                             \x1b[90m│\x1b[0m");
console.log("  \x1b[90m│\x1b[0m   Sign in with GitHub, add your Gemini      \x1b[90m│\x1b[0m");
console.log("  \x1b[90m│\x1b[0m   API key, and get your secret key.         \x1b[90m│\x1b[0m");
console.log("  \x1b[90m│\x1b[0m                                             \x1b[90m│\x1b[0m");
console.log("  \x1b[90m└─────────────────────────────────────────────┘\x1b[0m");
console.log("");
