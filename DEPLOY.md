# Deploying Disease Dashboard to Azure Container Apps

This guide covers deploying the Disease Dashboard to Azure Container Apps.

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- An Azure subscription
- GitHub repository with this code

## Deployment Options

There are two ways to deploy:

1. **Azure Portal UI** (Quick start) - Use "Source code or artifact" to deploy directly from GitHub
2. **CLI + GitHub Actions** (Automated CI/CD) - Set up ACR and automated deployments

---

## Option A: Deploy via Azure Portal (Quickest)

1. Go to [Azure Portal](https://portal.azure.com) > Create a resource > Container App
2. Configure basics:
   - **Resource group**: Create new or use existing
   - **Container app name**: `disease-dashboard` (lowercase, hyphens allowed)
   - **Region**: Choose your preferred region
3. On deployment source, select **"Source code or artifact"**
4. Connect to your GitHub repository
5. Azure will auto-detect the Dockerfile and build/deploy for you
6. Configure ingress to allow external traffic on port 8000

This approach is simpler but doesn't include automated CI/CD on push.

---

## Option B: CLI Setup with GitHub Actions (Recommended for CI/CD)

### Login to Azure

```bash
az login
```

### Set Variables

```bash
# Customize these values
RESOURCE_GROUP="USDT_web_app"
LOCATION="westus2"
ACR_NAME="diseasedashboardacr"  # Must be globally unique, lowercase, no hyphens
CONTAINER_APP_NAME="disease-dashboard"
ENVIRONMENT_NAME="disease-dashboard-env"
```

### Create Resource Group (skip if using existing)

```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### Create Azure Container Registry

```bash
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true
```

### Create Container Apps Environment

```bash
az containerapp env create \
  --name $ENVIRONMENT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

### Create Service Principal for GitHub Actions

```bash
# Create service principal with Contributor role
az ad sp create-for-rbac \
  --name "github-actions-disease-dashboard" \
  --role Contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth
```

Save the JSON output - you'll need it for the GitHub secret.

### Grant ACR Push Access

```bash
# Get the service principal ID from the JSON output (the "clientId" field)
SP_ID="<clientId from above>"

# Grant AcrPush role
az role assignment create \
  --assignee $SP_ID \
  --role AcrPush \
  --scope $(az acr show --name $ACR_NAME --query id -o tsv)
```

### Configure GitHub Repository

Go to your GitHub repository > Settings > Secrets and variables > Actions

**Add this secret:**

| Name | Value |
|------|-------|
| `AZURE_CREDENTIALS` | The entire JSON output from the service principal creation |

**Add these variables** (Settings > Variables tab):

| Name | Value |
|------|-------|
| `AZURE_CONTAINER_REGISTRY` | Your ACR name (e.g., `diseasedashboardacr`) |
| `CONTAINER_APP_NAME` | `disease-dashboard` |
| `RESOURCE_GROUP` | Your resource group name |

### First-Time Deployment (Manual)

For the initial deployment, create the Container App manually:

```bash
# Build and push image
az acr build \
  --registry $ACR_NAME \
  --image $CONTAINER_APP_NAME:latest \
  .

# Create container app
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --image $ACR_NAME.azurecr.io/$CONTAINER_APP_NAME:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 3
```

---

## Configure Staging Authentication

To protect your staging environment with HTTP Basic Auth:

### Set Environment Variables

```bash
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    STAGING_AUTH_ENABLED=true \
    STAGING_AUTH_USERNAME=admin

# Set password as a secret
az containerapp secret set \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets staging-auth-password=<your-secure-password>

# Reference the secret in environment variable
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars STAGING_AUTH_PASSWORD=secretref:staging-auth-password
```

### Verify Authentication

Visit your Container App URL. You should see a browser login dialog.

## Automated Deployments (GitHub Actions)

After initial setup, pushing to `main` triggers automatic deployment via GitHub Actions.

The workflow:
1. Checks out code
2. Logs into Azure
3. Builds Docker image
4. Pushes to ACR
5. Deploys new revision to Container Apps

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `STAGING_AUTH_ENABLED` | Enable HTTP Basic Auth | `false` |
| `STAGING_AUTH_USERNAME` | Auth username | `admin` |
| `STAGING_AUTH_PASSWORD` | Auth password | (required if enabled) |
| `DEBUG` | Enable debug mode | `false` |

## Useful Commands

```bash
# View logs
az containerapp logs show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow

# Get app URL
az containerapp show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv

# List revisions
az containerapp revision list \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table

# Scale replicas
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 1 \
  --max-replicas 5
```

## Troubleshooting

### Container fails to start

Check logs:
```bash
az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP
```

### Health check failing

The `/health` endpoint is excluded from authentication and should always return 200 OK.

### Authentication not working

1. Verify environment variables are set correctly
2. Check that `STAGING_AUTH_ENABLED` is `true` (string, not boolean)
3. Ensure password secret is properly referenced
