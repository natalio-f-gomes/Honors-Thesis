# Build Lambda Layer with Docker

Write-Host "Building Lambda Layer..." -ForegroundColor Green

# Build Docker image
docker build -t lambda-layer-builder .

# Create container and copy layer
docker create --name temp-layer lambda-layer-builder
docker cp temp-layer:/layer ./layer
docker rm temp-layer

# Create ZIP
Write-Host "Creating layer ZIP..." -ForegroundColor Green
Compress-Archive -Path ./layer/python -DestinationPath lambda-layer.zip -Force

# Cleanup
Remove-Item -Recurse -Force ./layer

Write-Host "Layer built: lambda-layer.zip" -ForegroundColor Green
Write-Host "Upload this to AWS Lambda as a layer" -ForegroundColor Yellow