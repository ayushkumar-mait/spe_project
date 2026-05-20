#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Installing LitmusChaos operator..."
kubectl apply -f https://litmuschaos.github.io/litmus/litmus-operator-v3.0.0.yaml

echo "Waiting for LitmusChaos CRDs..."
kubectl wait --for=condition=Established crd/chaosengines.litmuschaos.io --timeout=180s
kubectl wait --for=condition=Established crd/chaosexperiments.litmuschaos.io --timeout=180s
kubectl wait --for=condition=Established crd/chaosresults.litmuschaos.io --timeout=180s

echo "Waiting for Litmus operator..."
kubectl -n litmus rollout status deployment/chaos-operator-ce --timeout=240s

echo "Installing project Litmus RBAC and ChaosExperiment resources..."
kubectl apply -k chaos/litmus

echo "Litmus is ready for the job-platform namespace:"
kubectl -n litmus get deploy,pod
kubectl -n job-platform get serviceaccount litmus-admin
kubectl -n job-platform get chaosexperiments
