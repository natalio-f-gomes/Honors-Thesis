#!/bin/bash



git init
  # Stage all changes except what's in .gitignore
git add .

  # Commit with current timestamp
COMMIT_MESSAGE="Update on $(date +"%Y-%m-%d %H:%M:%S")"
git commit -m "$COMMIT_MESSAGE"

  # Push to the current branch on origin
git push origin HEAD

echo "✅ Code pushed to GitHub successfully!"

