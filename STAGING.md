# Staging Deployment Guide

This guide covers deploying the Disease Dashboard to **fly.io staging environment** for verification before moving forward in the deployment pipeline.

## Quick Access

**For reviewers/testers**: Click the link below to access the staging environment:

```
https://disease-dashboard-staging.fly.dev/?key=YOUR_API_KEY_HERE
```

Replace `YOUR_API_KEY_HERE` with the API key provided to you.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Deployment](#deployment)
- [Accessing the Staging Environment](#accessing-the-staging-environment)
- [Sharing Access](#sharing-access)
- [API Usage](#api-usage)
- [Management Commands](#management-commands)
- [Troubleshooting](#troubleshooting)

## Prerequisites

1. **Install flyctl** (Fly.io CLI):
   ```bash
   # macOS
   brew install flyctl

   # Linux
   curl -L https://fly.io/install.sh | sh

   # Windows
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Authenticate with Fly.io**:
   ```bash
   fly auth login
   ```

3. **Verify installation**:
   ```bash
   fly version
   ```

## Initial Setup

### 1. Generate API Key for Staging

Generate a secure API key that will be used to protect the staging environment:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Save this key securely - you'll need it for deployment and sharing with team members.

**Example output**:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

### 2. Launch Fly.io App

If this is your first deployment, create the app on Fly.io:

```bash
fly apps create disease-dashboard-staging
```

Or if the app name in `fly.toml` is already taken, choose a different name:

```bash
fly apps create disease-dashboard-staging-yourname
```

Then update `fly.toml` with your chosen app name.

### 3. Set Secrets

Set the API key as a secret (never commit this to git):

```bash
fly secrets set API_KEYS="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2"
```

**Note**: You can set multiple API keys by comma-separating them:
```bash
fly secrets set API_KEYS="key1,key2,key3"
```

## Deployment

Deploy the application to Fly.io:

```bash
fly deploy
```

The deployment process will:
1. Build the Docker image with multi-stage build
2. Compile frontend assets (CSS + JavaScript)
3. Install Python dependencies with uv
4. Deploy to Fly.io infrastructure
5. Run health checks
6. Make the app available

**First deployment** takes ~2-3 minutes. Subsequent deployments are faster.

### Monitor Deployment

Watch logs during deployment:
```bash
fly logs
```

Check deployment status:
```bash
fly status
```

## Accessing the Staging Environment

The staging environment supports **two authentication methods**:

### Method 1: Query Parameter (Web Browser) - RECOMMENDED FOR SHARING

Simply add `?key=<api-key>` to any URL:

```
https://disease-dashboard-staging.fly.dev/?key=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

**How it works**:
- The middleware extracts the key from the URL
- Automatically injects it as an `Authorization: Bearer` header
- Works for all pages and navigation
- Perfect for sharing with team members via Slack, email, etc.

**Advantages**:
- ✅ No browser extensions needed
- ✅ Works on all browsers and devices
- ✅ Easy to share via copy-paste
- ✅ Persists across page navigation within the app

### Method 2: Authorization Header (API/Programmatic)

Use the standard Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://disease-dashboard-staging.fly.dev/api/diseases
```

**When to use**:
- API calls from scripts, applications, or automation
- Testing with curl, httpie, or Postman
- CI/CD pipelines
- Integration tests

## Sharing Access

### For Web UI Access

Send team members a message like:

```
Hi team,

The staging environment is ready for testing!

Access the dashboard here:
https://disease-dashboard-staging.fly.dev/?key=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

This link includes the authentication key and will give you full access to the staging environment.

Please verify:
- Data visualizations load correctly
- All disease pages are accessible
- Charts render properly
- No errors in the console

Thanks!
```

### For API Access

For developers who need API access, provide:

```
API Base URL: https://disease-dashboard-staging.fly.dev
API Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

Usage:
curl -H "Authorization: Bearer a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2" \
  https://disease-dashboard-staging.fly.dev/api/diseases
```

### Security Considerations

⚠️ **Important Security Notes**:

1. **Query Parameter Visibility**:
   - Query parameters appear in browser history
   - May appear in server logs
   - Can be shared via URL
   - Use only for **staging/testing**, not production

2. **HTTPS**: Always use HTTPS (enforced by fly.toml)

3. **Key Rotation**: Rotate staging keys regularly:
   ```bash
   # Generate new key
   python -c "import secrets; print(secrets.token_hex(32))"

   # Update in Fly.io
   fly secrets set API_KEYS="new-key-here"
   ```

4. **Limit Access**: Only share with team members who need access

## API Usage

### Available Endpoints

All endpoints require authentication (either query param or Bearer token).

**Health Check**:
```bash
curl "https://disease-dashboard-staging.fly.dev/api/health?key=YOUR_KEY"
```

**List Diseases**:
```bash
curl "https://disease-dashboard-staging.fly.dev/api/diseases?key=YOUR_KEY"
```

**Get Statistics**:
```bash
curl "https://disease-dashboard-staging.fly.dev/api/stats?key=YOUR_KEY"
```

**National Time Series**:
```bash
curl "https://disease-dashboard-staging.fly.dev/api/timeseries/national/measles?key=YOUR_KEY"
```

**State Time Series**:
```bash
curl "https://disease-dashboard-staging.fly.dev/api/timeseries/states/measles?key=YOUR_KEY"
```

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `https://disease-dashboard-staging.fly.dev/docs?key=YOUR_KEY`
- **ReDoc**: `https://disease-dashboard-staging.fly.dev/redoc?key=YOUR_KEY`

## Management Commands

### View Logs

Real-time logs:
```bash
fly logs
```

Historical logs:
```bash
fly logs --since 1h
```

### SSH into Container

For debugging:
```bash
fly ssh console
```

### Check App Status

```bash
fly status
```

### View Configuration

```bash
fly config show
```

### List Secrets

```bash
fly secrets list
```

### Scale Resources

If needed, scale the VM:
```bash
fly scale memory 1024  # Increase to 1GB RAM
fly scale vm shared-cpu-2x  # 2 CPUs
```

### Restart App

```bash
fly apps restart disease-dashboard-staging
```

### Destroy App

When no longer needed:
```bash
fly apps destroy disease-dashboard-staging
```

## Troubleshooting

### App Not Starting

Check logs for errors:
```bash
fly logs
```

Common issues:
- Missing secrets: Verify `API_KEYS` is set
- Build failures: Check Dockerfile and dependencies
- Port conflicts: Ensure app listens on port 8000

### Authentication Issues

**401 Unauthorized**:
- Verify API key is correct
- Check key is set in secrets: `fly secrets list`
- Ensure key matches what you're using in URL/header

**Key not working**:
```bash
# Regenerate and set new key
python -c "import secrets; print(secrets.token_hex(32))"
fly secrets set API_KEYS="new-key-here"
fly apps restart disease-dashboard-staging
```

### Performance Issues

Monitor resource usage:
```bash
fly status
fly logs
```

Scale up if needed:
```bash
fly scale memory 1024
```

### Database Issues

Check data directory exists:
```bash
fly ssh console
ls -la /app/us_disease_tracker_data/data/states/
```

### Build Failures

View build logs:
```bash
fly deploy --verbose
```

Test locally with Docker:
```bash
docker build -t disease-dashboard .
docker run -p 8000:8000 -e API_KEYS="test-key" disease-dashboard
```

## Staging Workflow

### Typical Staging Workflow

1. **Developer pushes changes** to `main` branch
2. **Deploy to staging**:
   ```bash
   fly deploy
   ```
3. **Share staging URL** with team:
   ```
   https://disease-dashboard-staging.fly.dev/?key=STAGING_KEY
   ```
4. **Team verifies** functionality, visuals, performance
5. **If approved**, promote to production
6. **If issues found**, fix and redeploy to staging

### Auto-Stop/Start

The staging environment is configured to:
- **Auto-stop** when idle (saves costs)
- **Auto-start** when accessed (first request may be slower)

This is controlled in `fly.toml`:
```toml
auto_stop_machines = 'stop'
auto_start_machines = true
min_machines_running = 0
```

### Cost Optimization

Staging uses minimal resources:
- 512MB RAM
- 1 shared CPU
- Auto-stop when idle
- Estimated cost: ~$1-5/month (depending on usage)

## Next Steps

After staging verification:
1. Create production app: `fly apps create disease-dashboard-prod`
2. Use separate API keys for production
3. Update DNS for custom domain
4. Configure production secrets
5. Deploy to production: `fly deploy --app disease-dashboard-prod`

## Support

- **Fly.io Docs**: https://fly.io/docs/
- **Fly.io Community**: https://community.fly.io/
- **App Issues**: Open a GitHub issue in the project repository
