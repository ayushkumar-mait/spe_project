# Final Evaluation Runbook

This runbook maps the course PDF requirements to the exact commands to run.
Do not push to GitHub until you are ready for the final remote/demo setup.

## 1. Local Readiness Check

```bash
cd /Users/ayushkumar/Documents/Codex/automated-chaos-testing-self-healing-microservices-platform
./scripts/final-evaluation-check.sh
```

This validates:

- Git/Jenkins trigger files
- Python and Spring Boot tests
- Docker Compose files
- Kubernetes manifests and HPA
- Ansible syntax
- ELK/Filebeat files
- Vault policy and Vault-injected env loading

## 2. Local Jenkins Build

Start Jenkins:

```bash
./scripts/start-jenkins.sh
```

Open:

```text
http://localhost:8080
admin / admin
```

Run `automated-chaos-platform` with:

```text
DOCKERHUB_ORG=local
IMAGE_TAG=jenkins-local
PUSH_IMAGES=false
DEPLOY_TO_K8S=false
```

This proves checkout, automated tests, and Docker image builds locally.

## 3. Local Runtime Demo

```bash
docker compose -p chaos-demo -f docker-compose.demo.yml up -d --scale worker=3
```

Open:

```text
http://localhost:8000/docs
```

Submit one order:

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customerName":"Ayush","restaurantName":"Campus Canteen","pickupAddress":"Block A","deliveryAddress":"Hostel Gate","items":["Paneer Roll","Cold Coffee"],"priority":5,"estimatedDistanceKm":2.5,"simulateSeconds":2}'
```

Generate load:

```bash
python3 tools/load-generator/load_generator.py --url http://localhost:8000 --jobs 30 --concurrency 5
curl http://localhost:8000/metrics
docker compose -p chaos-demo -f docker-compose.demo.yml logs --tail=30 healing-controller
```

## 4. Full Docker Compose With ELK And Vault

```bash
docker compose up --build --scale worker=3
```

Open:

```text
Order API: http://localhost:8000/docs
Kibana:    http://localhost:5601
Vault:     http://localhost:8200
```

Create Kibana data view:

```text
job-platform-logs-*
```

Search for:

```text
order_submitted OR job_processing_completed OR healing_action_selected
```

## 5. Full GitHub, Docker Hub, Kubernetes Demo

Only do this when ready to push remote.

1. Create a GitHub repo.
2. Add the remote:

```bash
git remote add origin <your-github-repo-url>
git push -u origin main
```

3. In Jenkins, add Docker Hub credentials:

```text
ID: dockerhub-creds
Type: Username with password
```

4. Configure GitHub webhook:

```text
http://<jenkins-host>/github-webhook/
```

5. Run Jenkins with:

```text
DOCKERHUB_ORG=<your-dockerhub-username>
IMAGE_TAG=v1
PUSH_IMAGES=true
DEPLOY_TO_K8S=true
```

This proves:

- GitHub push trigger
- Jenkins checkout/build/test
- Docker Hub push
- Kubernetes deployment
- Rolling rollout verification

## 6. Kubernetes Monitoring, Vault, And Chaos

Deploy ELK/Filebeat:

```bash
kubectl apply -f observability/k8s/elk-stack.yaml
kubectl apply -f observability/k8s/filebeat-daemonset.yaml
kubectl -n observability port-forward svc/kibana 5601:5601
```

Bootstrap Vault after Vault injector is installed:

```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=dev-root-token
./vault/scripts/bootstrap-vault.sh
```

Run a chaos experiment:

```bash
kubectl apply -f chaos/experiments/pod-delete-worker.yaml
kubectl -n job-platform get pods -w
kubectl -n job-platform logs deploy/healing-controller -f
```

## 7. What To Say In Demo

The application is a Spring Boot delivery order system. Orders are placed through
`order-api`, queued in Redpanda/Kafka, processed by workers, stored in Redis, and
observed by ELK. Jenkins automates tests, image builds, Docker Hub push, and
Kubernetes deployment. Kubernetes HPA, rolling updates, Vault, Ansible, and a
self-healing controller complete the DevOps framework.
