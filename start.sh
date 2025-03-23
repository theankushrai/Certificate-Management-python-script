#!/bin/bash

set -e  # Exit on any error

# echo "🔧 Updating packages..."
# sudo apt-get update && sudo apt-get install -y unzip jq

# # ====== Install Vault if not found ======
# if ! [ -x "$(command -v vault)" ]; then
#     echo "📦 Installing Vault..."
#     VAULT_VERSION="1.15.3"
#     wget https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip
#     unzip vault_${VAULT_VERSION}_linux_amd64.zip
#     sudo mv vault /usr/local/bin/
#     rm vault_${VAULT_VERSION}_linux_amd64.zip
# else
#     echo "✅ Vault already installed."
# fi

# ====== Kill Existing Vault (if running) ======
pkill vault || true

# ====== Start Vault ======
echo "🚀 Starting Vault in dev mode..."
nohup vault server -dev -dev-listen-address="0.0.0.0:8200" > vault.log 2>&1 &

# ====== Wait for Vault to Start ======
sleep 5

# ====== Extract Root Token ======
ROOT_TOKEN=$(strings vault.log | grep "Root Token:" | awk '{print $NF}')
if [ -z "$ROOT_TOKEN" ]; then
    echo "❌ Failed to extract root token. Exiting."
    exit 1
fi
echo "🔑 Root Token: $ROOT_TOKEN"

# ====== Export Environment Variables ======
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="$ROOT_TOKEN"
# echo "export VAULT_ADDR=http://127.0.0.1:8200" >> ~/.bashrc
# echo "export VAULT_TOKEN=$ROOT_TOKEN" >> ~/.bashrc

# ====== Authenticate with Vault ======
vault login "$ROOT_TOKEN"

# ====== Check Existing Secrets Engines ======
if ! vault secrets list | grep -q "certs/"; then
    echo "🛠️ Enabling KV v2 at 'certs/'..."
    vault secrets enable -path=certs kv-v2
else
    echo "✅ KV v2 at 'certs/' already enabled."
fi

# ====== Check Vault Status ======
echo "📊 Vault Status:"
vault status

echo "🎉 Vault is ready at: $VAULT_ADDR"
echo "🔐 Use this token to authenticate: $ROOT_TOKEN"
