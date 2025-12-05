# Deploying Disease Dashboard to Azure Container Apps

This guide covers deploying the Disease Dashboard to Azure Container Apps with GitHub Actions CI/CD.

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- An Azure subscription
- GitHub repository with this code

## 1. Azure Resource Setup

### Login to Azure

```bash
az login
```

### Set Variables

```bash
# Customize these values
RESOURCE_GROUP="disease-dashboard-rg"
LOCATION="eastus"
ACR_NAME="diseasedashboardacr"  # Must be globally unique, lowercase, no hyphens
CONTAINER_APP_NAME="disease-dashboard"
ENVIRONMENT_NAME="disease-dashboard-env"
```

### Create Resource Group

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

## 2. Create Service Principal for GitHub Actions

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

## 3. Configure GitHub Repository

### Add Secrets

Go to your GitHub repository > Settings > Secrets and variables > Actions

Add this **secret**:

| Name | Value |
|------|-------|
| `AZURE_CREDENTIALS` | The entire JSON output from the service principal creation |

### Add Variables

Go to Settings > Secrets and variables > Actions > Variables tab

Add these **variables**:

| Name | Value |
|------|-------|
| `AZURE_CONTAINER_REGISTRY` | Your ACR name (e.g., `diseasedashboardacr`) |
| `CONTAINER_APP_NAME` | `disease-dashboard` |
| `RESOURCE_GROUP` | Your resource group name |

## 4. First-Time Deployment (Manual)

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

## 5. Configure Staging Authentication

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

## 6. Automated Deployments

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
