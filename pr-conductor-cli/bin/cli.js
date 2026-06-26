#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const workflowDir = path.join(process.cwd(), ".github", "workflows");
const templatePath = path.join(__dirname, "..", "templates", "reviewer.yml");
const destPath = path.join(workflowDir, "pr-conductor.yml");

if (fs.existsSync(destPath)) {
  console.log("PR Conductor workflow already exists at .github/workflows/pr-conductor.yml");
  process.exit(0);
}

fs.mkdirSync(workflowDir, { recursive: true });
fs.copyFileSync(templatePath, destPath);

console.log("PR Conductor workflow added to .github/workflows/pr-conductor.yml");
