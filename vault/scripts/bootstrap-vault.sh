#!/usr/bin/env bash
set -euo pipefail

export VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
export VAULT_TOKEN="${VAULT_TOKEN:-dev-root-token}"

vault secrets enable -path=secret kv-v2 2>/dev/null || true
vault kv put secret/job-platform \
  api_token="${API_TOKEN:-demo-api-token}" \
  redis_password="${REDIS_PASSWORD:-demo-redis-password}"

vault policy write job-platform vault/policies/job-platform.hcl

if kubectl get ns job-platform >/dev/null 2>&1; then
  vault auth enable kubernetes 2>/dev/null || true
  vault write auth/kubernetes/config \
    kubernetes_host="https://kubernetes.default.svc" \
    disable_iss_validation=true

  vault write auth/kubernetes/role/job-platform \
    bound_service_account_names="default,healing-controller" \
    bound_service_account_namespaces="job-platform" \
    policies="job-platform" \
    ttl="24h"
fi

vault kv get secret/job-platform

