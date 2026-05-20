#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Cleaning old pod-delete run, if present..."
kubectl -n job-platform delete chaosengine worker-pod-delete --ignore-not-found=true
kubectl -n job-platform delete chaosresult worker-pod-delete-pod-delete --ignore-not-found=true
kubectl -n job-platform delete pod worker-pod-delete-runner --ignore-not-found=true || true
kubectl -n job-platform delete job -l name=pod-delete --ignore-not-found=true || true
kubectl -n job-platform delete pod -l name=pod-delete --ignore-not-found=true || true
kubectl -n job-platform rollout status deployment/job-worker --timeout=180s

echo "Starting Litmus pod-delete experiment..."
kubectl apply -f chaos/experiments/pod-delete-worker.yaml

echo "Watch with:"
echo "  kubectl -n job-platform get pods -w"
echo "  kubectl -n job-platform get chaosengine,chaosresult"
echo
echo "Waiting for ChaosResult verdict..."
for _ in $(seq 1 120); do
  verdict="$(kubectl -n job-platform get chaosresult worker-pod-delete-pod-delete -o jsonpath='{.status.experimentStatus.verdict}' 2>/dev/null || true)"
  if [ -n "$verdict" ] && [ "$verdict" != "Awaited" ]; then
    echo "Chaos verdict: $verdict"
    kubectl -n job-platform get chaosengine,chaosresult
    kubectl -n job-platform describe chaosresult worker-pod-delete-pod-delete | sed -n '1,180p'
    exit 0
  fi
  sleep 5
done

echo "Timed out waiting for pod-delete verdict. Diagnostics:" >&2
kubectl -n job-platform get pods,job,chaosengine,chaosresult -o wide >&2 || true
kubectl -n job-platform logs -l app.kubernetes.io/component=experiment-job --tail=120 >&2 || true
exit 1
