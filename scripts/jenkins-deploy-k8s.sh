#!/usr/bin/env bash
set -euo pipefail

: "${K8S_NAMESPACE:=job-platform}"
: "${ORDER_API_IMAGE:?ORDER_API_IMAGE is required}"
: "${WORKER_IMAGE:?WORKER_IMAGE is required}"
: "${HEALER_IMAGE:?HEALER_IMAGE is required}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Deploying to Kubernetes namespace: ${K8S_NAMESPACE}"
echo "Order API image: ${ORDER_API_IMAGE}"
echo "Worker image: ${WORKER_IMAGE}"
echo "Healing controller image: ${HEALER_IMAGE}"

tmp_render="$(mktemp)"
cleanup() {
  rm -f "$tmp_render"
}
trap cleanup EXIT

if kubectl get namespace "$K8S_NAMESPACE" >/dev/null 2>&1; then
  kubectl -n "$K8S_NAMESPACE" delete job redpanda-topic-init --ignore-not-found=true
  kubectl -n "$K8S_NAMESPACE" wait --for=delete job/redpanda-topic-init --timeout=90s || true
fi

kubectl kustomize k8s/base \
  | sed \
      -e "s|image: your-dockerhub-username/order-api:dev|image: ${ORDER_API_IMAGE}|g" \
      -e "s|image: your-dockerhub-username/job-worker:dev|image: ${WORKER_IMAGE}|g" \
      -e "s|image: your-dockerhub-username/healing-controller:dev|image: ${HEALER_IMAGE}|g" \
  > "$tmp_render"

echo "Applying rendered Kubernetes manifests with the resolved image tags..."
kubectl apply -f "$tmp_render"

echo "Pausing healing controller during rollout so it cannot restart workers mid-deploy..."
kubectl -n "$K8S_NAMESPACE" scale deployment/healing-controller --replicas=0 || true

echo "Waiting for Redis and Redpanda infrastructure..."
kubectl -n "$K8S_NAMESPACE" rollout status deployment/redis --timeout=240s
kubectl -n "$K8S_NAMESPACE" rollout status deployment/redpanda --timeout=300s

echo "Waiting for Redpanda topic initialization..."
if ! kubectl -n "$K8S_NAMESPACE" wait --for=condition=complete job/redpanda-topic-init --timeout=480s; then
  echo "redpanda-topic-init did not complete. Diagnostics follow." >&2
  kubectl -n "$K8S_NAMESPACE" get pods,job -o wide >&2 || true
  kubectl -n "$K8S_NAMESPACE" describe job redpanda-topic-init >&2 || true
  kubectl -n "$K8S_NAMESPACE" logs job/redpanda-topic-init --all-containers --tail=200 >&2 || true
  kubectl -n "$K8S_NAMESPACE" logs deploy/redpanda --tail=120 >&2 || true
  exit 1
fi
kubectl -n "$K8S_NAMESPACE" logs job/redpanda-topic-init --all-containers --tail=80 || true

echo "Waiting for application rollouts..."
kubectl -n "$K8S_NAMESPACE" rollout status deployment/order-api --timeout=300s
kubectl -n "$K8S_NAMESPACE" rollout status deployment/job-worker --timeout=300s

echo "Resuming healing controller after application rollouts are stable..."
kubectl -n "$K8S_NAMESPACE" scale deployment/healing-controller --replicas=1
kubectl -n "$K8S_NAMESPACE" rollout status deployment/healing-controller --timeout=300s

kubectl -n "$K8S_NAMESPACE" get deploy,pod,svc,hpa,job -o wide
