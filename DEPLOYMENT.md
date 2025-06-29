# Azure App Service Deployment Guide

This guide will help you deploy the Kambo Chatbot to Azure App Services using GitHub Actions.

## Prerequisites

1. **Azure Account**: You need an active Azure subscription
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Azure CLI** (optional): For local Azure management

## Step 1: Create Azure App Service

### Option A: Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Web App" and select it
4. Fill in the basic information:
   - **Resource Group**: Create new or use existing
   - **Name**: `kambo-chatbot-app` (or your preferred name)
   - **Publish**: Code
   - **Runtime stack**: Python 3.11
   - **Operating System**: Linux (recommended)
   - **Region**: Choose closest to your users
   - **App Service Plan**: Choose appropriate tier (B1 for testing, P1V2 for production)

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group
az group create --name kambo-chatbot-rg --location eastus

# Create app service plan
az appservice plan create --name kambo-chatbot-plan --resource-group kambo-chatbot-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group kambo-chatbot-rg --plan kambo-chatbot-plan --name kambo-chatbot-app --runtime "PYTHON|3.11"
```

## Step 2: Configure Environment Variables

In the Azure Portal:

1. Go to your App Service
2. Navigate to **Settings** > **Configuration**
3. Add the following Application Settings:

```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
DATABASE_URL=sqlite:///./kambo_chatbot.db
APP_NAME=Kambo Chatbot
DEBUG=False
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your_secret_key_here
```

## Step 3: Get Publish Profile

1. In your Azure App Service, go to **Overview**
2. Click **Get publish profile**
3. Download the `.publishsettings` file
4. Open the file and copy the `publishUrl`, `userName`, and `userPWD` values

## Step 4: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add the following secret:
   - **Name**: `AZURE_WEBAPP_PUBLISH_PROFILE`
   - **Value**: Paste the entire content of the `.publishsettings` file

## Step 5: Update GitHub Actions Workflow

1. Open `.github/workflows/azure-deploy.yml`
2. Update the `AZURE_WEBAPP_NAME` environment variable to match your app name:

```yaml
env:
  AZURE_WEBAPP_NAME: your-app-name-here
```

## Step 6: Deploy

1. Commit and push your changes to the `main` or `master` branch
2. Go to your GitHub repository's **Actions** tab
3. You should see the deployment workflow running
4. Monitor the deployment progress

## Step 7: Verify Deployment

1. Once deployment is complete, visit your app URL: `https://your-app-name.azurewebsites.net`
2. Test the health endpoint: `https://your-app-name.azurewebsites.net/health`
3. Check the API documentation: `https://your-app-name.azurewebsites.net/docs`

## Troubleshooting

### Common Issues

1. **Deployment Fails**: Check the GitHub Actions logs for specific error messages
2. **App Won't Start**: Check the Azure App Service logs in the portal
3. **Environment Variables**: Ensure all required environment variables are set in Azure
4. **Port Issues**: The app should use the `PORT` environment variable provided by Azure

### Logs

- **GitHub Actions**: Check the Actions tab in your repository
- **Azure App Service**: Go to your app service > **Monitoring** > **Log stream**
- **Application Logs**: Check the stdout logs in the Azure portal

### Performance Optimization

1. **Database**: Consider using Azure SQL Database instead of SQLite for production
2. **Caching**: Implement Redis caching for better performance
3. **CDN**: Use Azure CDN for static content
4. **Scaling**: Configure auto-scaling rules in your App Service Plan

## Security Considerations

1. **HTTPS**: Azure App Service provides HTTPS by default
2. **Environment Variables**: Never commit sensitive data to your repository
3. **API Keys**: Rotate API keys regularly
4. **Rate Limiting**: Implement proper rate limiting for production use

## Monitoring

1. **Application Insights**: Enable Application Insights for monitoring
2. **Health Checks**: Use the `/health` endpoint for monitoring
3. **Alerts**: Set up Azure Monitor alerts for critical metrics

## Cost Optimization

1. **App Service Plan**: Choose the right tier for your needs
2. **Auto-scaling**: Configure auto-scaling to optimize costs
3. **Reserved Instances**: Consider reserved instances for long-term deployments 