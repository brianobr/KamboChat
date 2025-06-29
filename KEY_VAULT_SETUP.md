# Azure Key Vault Setup Guide

This guide will help you set up Azure Key Vault for secure secret management in your Kambo Chatbot application.

## Why Use Azure Key Vault?

### Security Benefits
- **Encrypted Storage**: All secrets are encrypted at rest and in transit
- **Access Control**: Fine-grained permissions using Azure AD
- **Audit Logging**: Complete audit trail of secret access
- **Automatic Rotation**: Built-in secret rotation capabilities
- **Centralized Management**: Single source of truth for all secrets

### Compliance Benefits
- **HIPAA Compliance**: Suitable for medical applications
- **SOC 2**: Meets security compliance standards
- **GDPR**: Helps with data protection requirements

## Step 1: Create Azure Key Vault

### Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Key Vault" and select it
4. Fill in the basic information:
   - **Resource Group**: Use the same as your App Service
   - **Key vault name**: `kambo-chatbot-vault` (must be globally unique)
   - **Region**: Same as your App Service
   - **Pricing tier**: Standard (recommended)
   - **Days to retain deleted vaults**: 7 (default)

### Using Azure CLI

```bash
# Create Key Vault
az keyvault create \
  --name kambo-chatbot-vault \
  --resource-group kambo-chatbot-rg \
  --location eastus \
  --sku standard \
  --enable-rbac-authorization true
```

## Step 2: Add Secrets to Key Vault

### Using Azure Portal

1. Go to your Key Vault
2. Click **Secrets** in the left menu
3. Click **+ Generate/Import**
4. Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `openai-api-key` | `your_openai_api_key_here` | OpenAI API key |
| `app-secret-key` | `your_app_secret_key_here` | Application secret key |

### Using Azure CLI

```bash
# Add OpenAI API key
az keyvault secret set \
  --vault-name kambo-chatbot-vault \
  --name openai-api-key \
  --value "your_openai_api_key_here"

# Add app secret key
az keyvault secret set \
  --vault-name kambo-chatbot-vault \
  --name app-secret-key \
  --value "your_app_secret_key_here"
```

## Step 3: Enable Managed Identity for App Service

### Using Azure Portal

1. Go to your App Service
2. Navigate to **Settings** > **Identity**
3. Under **System assigned**, click **On**
4. Click **Save**
5. Copy the **Object ID** (you'll need this for permissions)

### Using Azure CLI

```bash
# Enable managed identity
az webapp identity assign \
  --name kambo-chatbot-app \
  --resource-group kambo-chatbot-rg

# Get the principal ID
az webapp identity show \
  --name kambo-chatbot-app \
  --resource-group kambo-chatbot-rg \
  --query principalId \
  --output tsv
```

## Step 4: Grant App Service Access to Key Vault

### Using Azure Portal

1. Go to your Key Vault
2. Click **Access policies** in the left menu
3. Click **+ Create**
4. Configure the access policy:
   - **Secret permissions**: Get, List
   - **Select principal**: Choose your App Service's managed identity
   - **Application**: Leave blank (using managed identity)

### Using Azure CLI

```bash
# Get the principal ID of your App Service
PRINCIPAL_ID=$(az webapp identity show \
  --name kambo-chatbot-app \
  --resource-group kambo-chatbot-rg \
  --query principalId \
  --output tsv)

# Grant access to Key Vault
az keyvault set-policy \
  --name kambo-chatbot-vault \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

## Step 5: Configure App Service Environment Variables

In your Azure App Service, set these environment variables:

### Required Environment Variables

```
AZURE_KEY_VAULT_URL=https://kv-kambohealing-scus.vault.azure.net/
```

### Optional Environment Variables (for fallback)

```
OPENAI_API_KEY=<fallback_openai_key>
SECRET_KEY=<fallback_secret_key>
OPENAI_MODEL=gpt-4
DATABASE_URL=sqlite:///./kambo_chatbot.db
APP_NAME=Kambo Chatbot
DEBUG=False
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

## Step 6: Test Key Vault Integration

### Local Testing

1. Install Azure CLI and login:
```bash
az login
```

2. Set environment variables:
```bash
export AZURE_KEY_VAULT_URL=https://kv-kambohealing-scus.vault.azure.net/
```

3. Test the application:
```bash
python main.py
```

### Azure Testing

1. Deploy your application
2. Check the logs in Azure App Service
3. Verify secrets are being retrieved from Key Vault

## Security Best Practices

### 1. Access Control
- Use Azure RBAC for Key Vault access
- Grant minimum required permissions
- Regularly review access policies

### 2. Secret Management
- Rotate secrets regularly
- Use different secrets for different environments
- Never commit secrets to source code

### 3. Monitoring
- Enable Key Vault logging
- Set up alerts for secret access
- Monitor for unusual access patterns

### 4. Network Security
- Configure Key Vault firewall rules
- Use private endpoints for production
- Restrict access to specific IP ranges

## Troubleshooting

### Common Issues

1. **Access Denied**: Check managed identity permissions
2. **Secret Not Found**: Verify secret names in Key Vault
3. **Authentication Failed**: Ensure managed identity is enabled
4. **Network Issues**: Check firewall and network settings

### Debug Commands

```bash
# Check managed identity
az webapp identity show --name kambo-chatbot-app --resource-group kambo-chatbot-rg

# List Key Vault secrets
az keyvault secret list --vault-name kambo-chatbot-vault

# Test secret retrieval
az keyvault secret show --vault-name kambo-chatbot-vault --name openai-api-key
```

## Cost Considerations

- **Key Vault Standard**: ~$3/month + usage
- **Managed Identity**: Free
- **Network Egress**: Minimal cost for secret retrieval

## Migration from Environment Variables

If you're migrating from environment variables:

1. **Backup**: Export current environment variables
2. **Create Secrets**: Add all secrets to Key Vault
3. **Update Configuration**: Modify app to use Key Vault
4. **Test**: Verify functionality in staging
5. **Deploy**: Update production with new configuration
6. **Cleanup**: Remove secrets from environment variables

## Next Steps

1. **Enable Monitoring**: Set up Application Insights
2. **Implement Rotation**: Configure automatic secret rotation
3. **Add More Secrets**: Store database credentials, API keys, etc.
4. **Security Review**: Regular security assessments 