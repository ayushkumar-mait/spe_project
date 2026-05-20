PROJECT := automated-chaos-testing-self-healing-microservices-platform
NAMESPACE ?= job-platform
DOCKERHUB_ORG ?= your-dockerhub-username
IMAGE_TAG ?= dev

.PHONY: test compose-up compose-down observability-up observability-down build k8s-apply k8s-status load litmus-install litmus-pod-delete chaos-pod-delete rolling-update

test:
	./scripts/run-python-tests.sh
	mvn -q -f services/order-api/pom.xml test

compose-up:
	docker compose up --build --scale worker=3

compose-down:
	docker compose down -v

observability-up:
	./scripts/start-observability.sh

observability-down:
	docker compose stop elasticsearch logstash kibana

build:
	docker build -f services/order-api/Dockerfile -t $(DOCKERHUB_ORG)/order-api:$(IMAGE_TAG) .
	docker build -f services/worker/Dockerfile -t $(DOCKERHUB_ORG)/job-worker:$(IMAGE_TAG) .
	docker build -f services/healing-controller/Dockerfile -t $(DOCKERHUB_ORG)/healing-controller:$(IMAGE_TAG) .

k8s-apply:
	kubectl apply -k k8s/base

k8s-status:
	kubectl -n $(NAMESPACE) get deploy,pod,svc,hpa

load:
	python3 tools/load-generator/load_generator.py --jobs 50 --concurrency 10 --url http://localhost:8000

litmus-install:
	./scripts/install-litmus.sh

litmus-pod-delete:
	./scripts/run-litmus-pod-delete.sh

chaos-pod-delete:
	kubectl apply -f chaos/experiments/pod-delete-worker.yaml

rolling-update:
	./scripts/rolling-update-demo.sh $(NAMESPACE) $(DOCKERHUB_ORG)/job-worker:$(IMAGE_TAG)
