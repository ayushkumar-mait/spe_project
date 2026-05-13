# Architecture

## Component View

```mermaid
flowchart TB
    subgraph Dev["DevOps Automation"]
        G["GitHub Push"] --> J["Jenkins Pipeline"]
        J --> T["Unit Tests"]
        T --> D["Docker Build"]
        D --> DH["Docker Hub"]
        DH --> KD["kubectl Deploy"]
    end

    subgraph K8S["Kubernetes Cluster"]
        API["Spring Boot Order API Deployment"]
        Q["Redpanda / Kafka Queue"]
        REDIS["Redis Order/Job Store"]
        WORKER["Worker Deployment"]
        HPA["Horizontal Pod Autoscaler"]
        HEAL["Self-Healing Controller"]
        API --> Q
        API --> REDIS
        Q --> WORKER
        WORKER --> REDIS
        HPA --> WORKER
        HEAL --> WORKER
    end

    subgraph OBS["Observability and Reliability"]
        L["Filebeat / Docker GELF"] --> LS["Logstash"]
        LS --> ES["Elasticsearch"]
        ES --> KB["Kibana"]
        LC["LitmusChaos"] --> WORKER
    end

    KD --> K8S
    K8S --> L
```

## Runtime Flow

1. A customer or load generator sends `POST /orders`.
2. The Spring Boot Order API creates an order ID, stores status in Redis, and
   publishes a `delivery_order` task to Kafka/Redpanda.
3. Worker pods consume delivery-order tasks from the queue and update Redis with `running`,
   `completed`, or `failed`.
4. Logs are emitted as JSON and collected by ELK.
5. LitmusChaos injects pod deletion, CPU pressure, or network delay.
6. Kubernetes liveness probes, Deployment controllers, and HPA recover basic
   failures.
7. The custom healing controller reads job metrics from Redis and triggers
   scale/restart actions through the Kubernetes API.

## Self-Healing Rules

The controller evaluates this state every `HEALING_INTERVAL_SECONDS`:

```text
queued orders + running orders = backlog
failed orders = failure count
current replicas = worker deployment replica count
```

Actions:

- Backlog above `HEALING_QUEUED_THRESHOLD`: scale worker replicas upward.
- Failed orders above `HEALING_FAILED_THRESHOLD`: trigger a rolling restart.
- Backlog cleared: scale workers back to `HEALING_MIN_REPLICAS`.

Kubernetes also provides built-in recovery:

- Liveness probes restart unhealthy containers.
- Deployment controller recreates deleted pods.
- HPA scales pods when CPU utilization rises.
- Rolling update strategy keeps at least one old pod running during upgrades.

## Failure Scenarios

| Scenario | Injection | Expected Recovery |
| --- | --- | --- |
| Worker pod deleted | Litmus `pod-delete` | Deployment recreates pod |
| Worker CPU stress | Litmus `pod-cpu-hog` | HPA increases replicas |
| Network delay | Litmus `pod-network-latency` | Queue buffers jobs; workers resume |
| Many failed orders | Delivery orders with `forceFail=true` | Healing controller restarts workers |
| High order backlog | Load generator | Healing controller and HPA scale workers |
