# Sync files to S3
Write-Host "Syncing files to S3..." -ForegroundColor Green
aws s3 sync . s3://resume-analyzer.net/ --exclude ".git/*" --exclude "*.json" --exclude "*.ps1"


aws cloudfront create-invalidation --distribution-id E15FFX9Y2U7A5U --paths "/*"

Write-Host "Deployment complete!" -ForegroundColor Green

