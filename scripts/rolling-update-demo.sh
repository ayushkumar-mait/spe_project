#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${1:-job-platform}"
IMAGE="${2:-your-dockerhub-username/job-worker:dev}"

kubectl -n "$NAMESPACE" set image deployment/job-worker worker="$IMAGE"
kubectl -n "$NAMESPACE" rollout status deployment/job-worker --timeout=180s
kubectl -n "$NAMESPACE" get pods -l app=job-worker

