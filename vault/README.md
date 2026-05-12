# Vault Integration

Vault is used to store sensitive values such as API tokens and Redis passwords.
The Kubernetes deployments are annotated for Vault Agent injection. When the
Vault injector is installed, it writes a file at:

```text
/vault/secrets/platform.env
```

The services load this file automatically during startup.

Local dev setup:

```bash
docker compose up vault
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=dev-root-token
./vault/scripts/bootstrap-vault.sh
```

Kubernetes setup requires the Vault Helm chart or Vault injector to be installed
in the cluster. The included script creates the KV path, policy, and Kubernetes
auth role.

