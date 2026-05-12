# Project Report Draft

## Title

Automated Chaos Testing and Self-Healing Microservices Platform

## Domain

DevOps, AIOps, cloud-native reliability engineering, and distributed systems.

## Problem Statement

Modern microservice systems must remain available during frequent deployments,
load spikes, infrastructure failures, and network instability. Manual deployment
and manual recovery are slow and error-prone. This project designs and implements
an automated DevOps framework that builds, tests, deploys, monitors, breaks, and
self-heals a distributed job processing application.

## Objectives

- Automate the SDLC using GitHub, Jenkins, Docker, Docker Hub, and Kubernetes.
- Build a distributed microservices application suitable for reliability testing.
- Introduce chaos engineering using LitmusChaos.
- Collect and visualize application logs using ELK.
- Implement self-healing using Kubernetes and a custom controller.
- Demonstrate scalability through Horizontal Pod Autoscaling.
- Add advanced DevOps features: Vault, Ansible roles, and rolling updates.

## Application Overview

The application is a distributed job processing system:

- Job API accepts user job requests.
- Redpanda provides a Kafka-compatible job queue.
- Worker pods process jobs asynchronously.
- Redis stores job status and metrics.
- Healing Controller observes Redis metrics and acts through the Kubernetes API.

## Methodology

1. Develop Python microservices with structured logging.
2. Containerize services using Docker.
3. Use Docker Compose for local integration testing.
4. Create Kubernetes manifests for deployments, services, HPA, RBAC, and PDB.
5. Configure Jenkins CI/CD pipeline for build, test, push, and deploy.
6. Deploy ELK stack and Filebeat for logs.
7. Use LitmusChaos experiments to inject failures.
8. Use Vault for secret storage and Ansible for modular deployment.

## CI/CD Pipeline

The Jenkins pipeline contains these stages:

1. Checkout from GitHub.
2. Run automated unit tests.
3. Build Docker images for API, worker, and healing controller.
4. Push images to Docker Hub.
5. Apply Kubernetes manifests.
6. Update Kubernetes deployments with new images.
7. Verify rollout status.

## Chaos Engineering

The following chaos experiments are included:

- Pod delete: deletes worker pods to test Deployment recovery.
- CPU stress: increases worker CPU usage to test HPA scaling.
- Network delay: delays worker network traffic to test queue buffering and
  system resilience.

## Monitoring and Logging

Each service writes JSON logs with fields such as service name, event name, job
ID, trace ID, status, and error details. Logstash parses these logs and forwards
them to Elasticsearch. Kibana dashboards can show job submissions, failures,
completion trends, and healing actions.

## Self-Healing Design

The platform uses two recovery layers:

- Kubernetes recovery: restart crashed containers, recreate deleted pods, and
  perform rolling updates.
- Custom controller recovery: inspect job backlog and failures, then scale or
  restart the worker deployment.

Decision rules:

- If backlog exceeds threshold, increase worker replicas.
- If failures exceed threshold, trigger rolling restart.
- If backlog clears, scale back to minimum replicas.

## Scalability and High Availability

Worker and API deployments define CPU requests and HorizontalPodAutoscalers.
PodDisruptionBudgets protect availability during voluntary disruptions. Rolling
updates use `maxUnavailable: 0` to avoid downtime during image updates.

## Security

Vault stores sensitive credentials under `secret/data/job-platform`. Kubernetes
Vault Agent annotations inject the secret file into pods. The application loads
the injected file during startup, avoiding hardcoded credentials.

## Expected Results

- Jobs are accepted and processed asynchronously.
- Jenkins automates testing, image creation, image push, and Kubernetes rollout.
- Logs appear in Elasticsearch and can be visualized in Kibana.
- Worker pod deletion is recovered by Kubernetes.
- CPU pressure causes HPA scaling.
- Backlog or failure thresholds trigger custom healing actions.
- Rolling updates complete without service outage.

## Future Scope

- Replace Redis status storage with PostgreSQL for durable audit history.
- Add Prometheus metrics and alerting.
- Add canary deployment using Argo Rollouts or Flagger.
- Add queue lag based autoscaling using KEDA.
- Add OpenTelemetry tracing across API, queue, and workers.

