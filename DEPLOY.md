# Deploying Disease Dashboard to Azure Container Apps

This guide covers deploying the Disease Dashboard to Azure Container Apps using GitHub Container Registry (GHCR).

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- An Azure subscription with Contributor access
- GitHub repository (public)
- `.env` file configured (copy from `.env.example`)

## Architecture

```
GitHub (push to main)
    ↓
GitHub Actions
    └── Build Docker image → Push to GHCR (automatic)

[Manual step when ready to deploy]
    ↓
az containerapp update --image ghcr.io/OWNER/disease-dashboard:SHA
    ↓
Azure Container Apps pulls new image from GHCR
```

## Configuration

All deployment commands read from `.env`. Copy the example and fill in your values:

```bash
cp .env.example .env
# Edit .env with your values
```

Required variables for deployment:
- `AZURE_RESOURCE_GROUP` - Azure resource group name
- `AZURE_LOCATION` - Azure region (e.g., eastus)
- `AZURE_CONTAINER_APP_NAME` - Name for your Container App
- `AZURE_ENVIRONMENT_NAME` - Container Apps environment name
- `GITHUB_OWNER` - Your GitHub username or organization
- `GITHUB_REPO` - Repository name

## Initial Setup

### 1. Login to Azure

```bash
az login
```

### 2. Load environment variables

```bash
source .env
```

### 3. Create Resource Group (skip if using existing)

```bash
az group create --name $AZURE_RESOURCE_GROUP --location $AZURE_LOCATION
```

### 4. Create Container Apps Environment

```bash
az containerapp env create \
  --name $AZURE_ENVIRONMENT_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --location $AZURE_LOCATION
```

### 5. Create Container App

After you've pushed your first image to GHCR (happens automatically on push to main):

```bash
source .env
az containerapp create \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --environment $AZURE_ENVIRONMENT_NAME \
  --image ghcr.io/$GITHUB_OWNER/$GITHUB_REPO:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 3
```

### 6. Make GHCR Package Public

Since the repo is public, make the package public too (no auth needed):

1. Go to GitHub > Your profile > Packages
2. Click on the `disease-dashboard` package
3. Go to Package settings
4. Change visibility to **Public**

## Daily Workflow

### Automatic: Build and Push

Every push to `main` automatically:
1. Builds the Docker image
2. Pushes to GHCR with tags `latest` and the commit SHA

### Manual: Deploy to Azure

When ready to deploy, run the command printed at the end of the GitHub Actions run:

```bash
source .env
az containerapp update \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --image ghcr.io/$GITHUB_OWNER/$GITHUB_REPO:COMMIT_SHA
```

Or deploy the latest:

```bash
source .env
az containerapp update \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --image ghcr.io/$GITHUB_OWNER/$GITHUB_REPO:latest
```

## Configure Staging Authentication

To protect your staging environment with HTTP Basic Auth:

```bash
source .env
az containerapp update \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --set-env-vars \
    STAGING_AUTH_ENABLED=true \
    STAGING_AUTH_USERNAME=admin

# Set password as a secret
az containerapp secret set \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --secrets staging-auth-password=<your-secure-password>

# Reference the secret in environment variable
az containerapp update \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --set-env-vars STAGING_AUTH_PASSWORD=secretref:staging-auth-password
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `STAGING_AUTH_ENABLED` | Enable HTTP Basic Auth | `false` |
| `STAGING_AUTH_USERNAME` | Auth username | `admin` |
| `STAGING_AUTH_PASSWORD` | Auth password | (required if enabled) |
| `DEBUG` | Enable debug mode | `false` |

## Useful Commands

```bash
source .env

# View logs
az containerapp logs show \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --follow

# Get app URL
az containerapp show \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv

# List revisions
az containerapp revision list \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --output table

# Scale replicas
az containerapp update \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --min-replicas 1 \
  --max-replicas 5
```

## TODO: Initialize Database from S3

The container starts with empty data directories. The recommended approach:

1. Build the DuckDB database locally or in a data pipeline
2. Upload the `.duckdb` file to S3/Azure Blob Storage
3. Configure the container to download the database at startup
4. Set up regular syncs or streaming updates to keep the database current

This keeps the container image small and allows data updates without rebuilding.

## Troubleshooting

### Container fails to start

Check logs:
```bash
source .env
az containerapp logs show \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP
```

### Health check failing

The `/health` endpoint is excluded from authentication and should always return 200 OK.

### Authentication not working

1. Verify environment variables are set correctly
2. Check that `STAGING_AUTH_ENABLED` is `true` (string, not boolean)
3. Ensure password secret is properly referenced
