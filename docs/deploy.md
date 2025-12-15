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
    ↓
On startup, app loads CSV data from Azure Blob Storage (via fsspec/adlfs)
    ↓
ETL transforms CSV → DuckDB in-memory database
```

### Data Flow

- **Local development**: CSV files in local directories (`us_disease_tracker_data/`, `nndss_data/`)
- **Deployed environments**: CSV files in Azure Blob Storage, loaded via `DATA_URI` and `NNDSS_DATA_URI` env vars

The app uses [fsspec](https://filesystem-spec.readthedocs.io/) + [adlfs](https://github.com/fsspec/adlfs) for service-agnostic storage access. This means the same code works with local files, Azure Blob, or S3.

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

#### For Staging (password protected)

```bash
source .env

# Generate staging password (save this somewhere secure!)
STAGING_PASSWORD=$(openssl rand -base64 16 | tr -d '=/+' | head -c 20)
echo "Staging password: $STAGING_PASSWORD"

az containerapp create \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --environment $AZURE_ENVIRONMENT_NAME \
  --image ghcr.io/$GITHUB_OWNER/$GITHUB_REPO:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 2.0 \
  --memory 4.0Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars \
    STAGING_AUTH_ENABLED=true \
    STAGING_AUTH_USERNAME=admin \
    STAGING_AUTH_PASSWORD="$STAGING_PASSWORD"
```

#### For Production (public access)

```bash
source .env
az containerapp create \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --environment $AZURE_ENVIRONMENT_NAME \
  --image ghcr.io/$GITHUB_OWNER/$GITHUB_REPO:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 2.0 \
  --memory 4.0Gi \
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

When ready to deploy, use the commit SHA from the GitHub Actions run output:

```bash
source .env
COMMIT_SHA=$(git rev-parse HEAD)
az containerapp update \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --image ghcr.io/$GITHUB_OWNER/$GITHUB_REPO:$COMMIT_SHA
```

**Important:** Always use the commit SHA tag, not `:latest`. Azure Container Apps won't pull a new image if the tag string hasn't changed, even if the underlying image was updated. Using commit SHAs ensures the correct version is deployed and enables easy rollbacks.

## Update Staging Password

To change the staging password on an existing deployment:

```bash
source .env
NEW_PASSWORD=$(openssl rand -base64 16 | tr -d '=/+' | head -c 20)
echo "New password: $NEW_PASSWORD"

az containerapp update \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --set-env-vars STAGING_AUTH_PASSWORD="$NEW_PASSWORD"
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `STAGING_AUTH_ENABLED` | Enable HTTP Basic Auth | `false` |
| `STAGING_AUTH_USERNAME` | Auth username | `admin` |
| `STAGING_AUTH_PASSWORD` | Auth password | (required if enabled) |
| `DEBUG` | Enable debug mode | `false` |
| `AZURE_STORAGE_ACCOUNT` | Azure Blob Storage account name | (empty) |
| `AZURE_STORAGE_KEY` | Azure Blob Storage account key | (empty) |
| `DATA_URI` | Tracker data location (e.g., `az://data/us_disease_tracker_data`) | (empty = local) |
| `NNDSS_DATA_URI` | NNDSS data location (e.g., `az://data/nndss_data`) | (empty = local) |

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

## Azure Blob Storage Setup (Data)

The container loads CSV data from Azure Blob Storage at startup. You need to provision storage and upload data.

### 1. Create Storage Account

```bash
source .env

# Create storage account (name must be globally unique, lowercase, no hyphens)
STORAGE_ACCOUNT_NAME="diseasedashboarddata"  # Change this to something unique

az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --location $AZURE_LOCATION \
  --sku Standard_LRS

# Get the storage account key
STORAGE_KEY=$(az storage account keys list \
  --account-name $STORAGE_ACCOUNT_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --query '[0].value' -o tsv)

echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "Storage Key: $STORAGE_KEY"
```

### 2. Create Container and Upload Data

```bash
# Create a container for the data
az storage container create \
  --name data \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY

# Upload tracker data
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --destination data/us_disease_tracker_data \
  --source us_disease_tracker_data/

# Upload NNDSS data
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --destination data/nndss_data \
  --source nndss_data/
```

### 3. Configure Container App

Add the storage credentials and data URIs to the Container App:

```bash
source .env

az containerapp update \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --set-env-vars \
    AZURE_STORAGE_ACCOUNT="$STORAGE_ACCOUNT_NAME" \
    AZURE_STORAGE_KEY="$STORAGE_KEY" \
    DATA_URI="az://data/us_disease_tracker_data" \
    NNDSS_DATA_URI="az://data/nndss_data"
```

### 4. Verify Data Loading

After updating, check the container logs to verify data is loading:

```bash
az containerapp logs show \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --follow
```

You should see log messages like:
```
Loading data from tracker: az://data/us_disease_tracker_data
Found X total tracker CSV files
Loading data from nndss: az://data/nndss_data
Database initialized with X total records
```

### Updating Data

To update data after initial setup:

```bash
# Re-upload tracker data
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --destination data/us_disease_tracker_data \
  --source us_disease_tracker_data/ \
  --overwrite

# Restart the container to reload data
az containerapp revision restart \
  --name $AZURE_CONTAINER_APP_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --revision $(az containerapp revision list \
    --name $AZURE_CONTAINER_APP_NAME \
    --resource-group $AZURE_RESOURCE_GROUP \
    --query '[0].name' -o tsv)
```

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

### Data not loading from Azure Blob Storage

1. Verify storage credentials are set:
   ```bash
   az containerapp show \
     --name $AZURE_CONTAINER_APP_NAME \
     --resource-group $AZURE_RESOURCE_GROUP \
     --query 'properties.template.containers[0].env' -o table
   ```

2. Check that `DATA_URI` uses correct format: `az://container/path` (not `https://`)

3. Verify data exists in blob storage:
   ```bash
   az storage blob list \
     --account-name $STORAGE_ACCOUNT_NAME \
     --container-name data \
     --prefix us_disease_tracker_data/ \
     --output table
   ```

4. Test storage access locally:
   ```bash
   export AZURE_STORAGE_ACCOUNT="your-account"
   export AZURE_STORAGE_KEY="your-key"
   export DATA_URI="az://data/us_disease_tracker_data"
   uv run python -c "from app.etl.storage import get_filesystem; fs, path = get_filesystem('$DATA_URI'); print(fs.ls(path))"
   ```
