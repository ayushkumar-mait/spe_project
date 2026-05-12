# Demo Guide

## 1. Local Validation

```bash
cd automated-chaos-testing-self-healing-microservices-platform
python3 -m pytest
```

Explain that these tests validate:

- job model and Redis repository behavior
- worker job processing logic
- self-healing decision policy

## 2. Docker Compose Demo

```bash
docker compose up --build --scale worker=3
```

Open another terminal:

```bash
curl http://localhost:8000/healthz
python3 tools/load-generator/load_generator.py --jobs 30 --concurrency 5
curl http://localhost:8000/metrics
```

Open Kibana:

```text
http://localhost:5601
```

Create a data view:

```text
job-platform-logs-*
```

Search:

```text
app.event: job_submitted OR app.event: job_processing_completed
```

## 3. Kubernetes Deployment

```bash
kubectl apply -k k8s/base
kubectl -n job-platform get deploy,pod,svc,hpa
kubectl -n job-platform port-forward svc/job-api 8000:8000
```

Generate load:

```bash
python3 tools/load-generator/load_generator.py --jobs 100 --concurrency 20
kubectl -n job-platform get hpa -w
```

## 4. Monitoring Deployment

```bash
kubectl apply -f observability/k8s/elk-stack.yaml
kubectl apply -f observability/k8s/filebeat-daemonset.yaml
kubectl -n observability port-forward svc/kibana 5601:5601
```

Use Kibana to visualize:

- logs by service
- job submissions
- processing failures
- healing actions

## 5. Chaos Engineering Demo

```bash
kubectl apply -f chaos/experiments/pod-delete-worker.yaml
kubectl -n job-platform get pods -w
```

Show recovery:

```bash
kubectl -n job-platform get deploy job-worker
kubectl -n job-platform logs deploy/healing-controller -f
curl http://localhost:8000/metrics
```

Optional CPU stress:

```bash
kubectl apply -f chaos/experiments/cpu-stress-worker.yaml
kubectl -n job-platform get hpa -w
```

## 6. Self-Healing Demo Without Litmus

Submit flaky jobs:

```bash
for i in $(seq 1 20); do
  curl -s -X POST http://localhost:8000/submit-job \
    -H "Content-Type: application/json" \
    -d '{"job_type":"flaky","payload":{"failure_rate":0.8,"seconds":0.1},"priority":8}'
done
```

Then watch:

```bash
kubectl -n job-platform logs deploy/healing-controller -f
kubectl -n job-platform rollout history deployment/job-worker
```

## 7. Rolling Update Demo

```bash
kubectl -n job-platform set image deployment/job-worker worker=your-dockerhub-username/job-worker:v2
kubectl -n job-platform rollout status deployment/job-worker
```

Explain that `maxUnavailable: 0` keeps the service available while new pods come
up.

## 8. Ansible Demo

```bash
cd ansible
ansible-playbook site.yml -e dockerhub_org=your-dockerhub-username -e image_tag=dev
```

Explain the roles:

- `k8s-role`: applies core Kubernetes resources
- `app-role`: updates images and waits for rollouts
- `monitoring-role`: deploys ELK and Filebeat
- `vault-role`: validates Vault integration assets

## 9. Jenkins Demo

Start local Jenkins:

```bash
./scripts/start-jenkins.sh
```

Open:

```text
http://localhost:8080
```

Run the seeded job:

```text
automated-chaos-platform
```

For a laptop-only run, keep:

```text
PUSH_IMAGES=false
DEPLOY_TO_K8S=false
```

For the complete CI/CD run with Docker Hub and Kubernetes, set both values to
`true` after adding the `dockerhub-creds` credential and Kubernetes context.

Show the `Jenkinsfile` stages:

1. Checkout from GitHub.
2. Run unit tests.
3. Build Docker images.
4. Push images to Docker Hub.
5. Apply Kubernetes manifests.
6. Set images and wait for rollout.
