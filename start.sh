#!/bin/bash

set -e  # Exit on any error

# Start Vault in dev mode
echo "🚀 Starting Vault ..."
nohup vault server -dev -dev-listen-address="0.0.0.0:8200" > vault.log 2>&1 &

# Wait for Vault to Start
sleep 5

# Extract Root Token
ROOT_TOKEN=$(cat vault.log | grep "Root Token:" | awk '{print $NF}')
if [ -z "$ROOT_TOKEN" ]; then
    echo "❌ Failed to extract root token. Exiting."
    exit 1
fi

# Save the root token to a file
echo $ROOT_TOKEN > vault_token.txt

# Export Environment Variables
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="$ROOT_TOKEN"

# Authenticate with Vault
vault login "$ROOT_TOKEN"

# Check Existing Secrets Engines
if ! vault secrets list | grep -q "certs/"; then
    echo "🛠️ Enabling KV v2 at 'certs/'..."
    vault secrets enable -path=certs kv-v2
else
    echo "✅ KV v2 at 'certs/' already enabled."
fi

# Check Vault Status
echo "📊 Vault Status:"
vault status

echo "🎉 Vault is ready"

# Start an interactive shell
exec "$SHELL"