# Viva Questions

## What is the application layer in this project?

It is a delivery order processing system. Customers place orders through the
Spring Boot Order API, order-processing tasks are placed into a Kafka-compatible
queue, and worker pods process them asynchronously.

## Why is this suitable for chaos engineering?

The system naturally has failure points: API, queue, workers, Redis, and network
communication. Worker deletion, CPU stress, order backlog, and network delay are
realistic failures for this architecture.

## What happens if a worker pod crashes?

Kubernetes recreates the pod because it is managed by a Deployment. Jobs already
in the queue remain available for other workers. The worker also updates Redis so
failures can be observed.

## What is self-healing in this project?

There are two levels:

- Kubernetes self-healing: liveness probes, Deployment restarts, HPA scaling.
- Custom self-healing: the healing controller reads job metrics and triggers
  worker scaling or rolling restarts.

## Why use Kafka or Redpanda?

It decouples order submission from background processing. The API remains responsive even
when workers are slow or temporarily unavailable.

## Why use Redis?

Kafka stores the stream of order-processing tasks, while Redis stores queryable order status and
recent metrics for the API and healing controller.

## How does Jenkins automate SDLC?

A GitHub push triggers Jenkins. Jenkins checks out code, runs tests, builds
Docker images, pushes them to Docker Hub, deploys them to Kubernetes, and verifies
rollout status.

## How does ELK help?

All services emit structured JSON logs. Logstash parses them, Elasticsearch
indexes them, and Kibana visualizes events like job submission, failure,
completion, and healing actions.

## How does HPA work here?

The worker and API deployments have CPU requests and HPA objects. When average
CPU utilization crosses the target threshold, Kubernetes increases pod replicas.

## What is live patching or zero-downtime update here?

Kubernetes rolling update replaces pods gradually. The configuration uses
`maxUnavailable: 0`, so at least the existing pods remain available while new pods
are starting.

## How is Vault used?

Vault stores sensitive values in `secret/data/job-platform`. Kubernetes
deployments include Vault Agent annotations so secrets can be injected into pods
without hardcoding them in YAML or source code.

## What is innovative?

The project combines chaos experiments with a custom healing loop. It does not
only deploy microservices; it observes failures and automatically changes the
runtime state to recover.
