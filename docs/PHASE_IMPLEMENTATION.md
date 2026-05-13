# Phase Implementation Map

| Phase | Project Implementation |
| --- | --- |
| 1. Application Setup | Spring Boot Order API, Worker, Healing Controller, shared models, structured logging |
| 2. Version Control | Repository-ready structure with `.gitignore`; push this folder to GitHub |
| 3. CI/CD Pipeline | `Jenkinsfile` with GitHub trigger, tests, Docker build/push, Kubernetes deploy |
| 4. Containerization | Dockerfiles for each service and `docker-compose.yml` for local testing |
| 5. Kubernetes Deployment | Deployments, Services, ConfigMap, RBAC, PDB, HPA in `k8s/base` |
| 6. Chaos Engineering | LitmusChaos pod delete, CPU stress, and network delay experiments |
| 7. Monitoring and Logging | ELK stack, Logstash pipeline, Filebeat DaemonSet, Kibana setup |
| 8. Self-Healing | Kubernetes restart behavior plus custom backlog/failure healing controller |
| 9. Scalability | Worker and API HorizontalPodAutoscalers |
| 10. Security | Vault policy, bootstrap script, and Vault Agent injection annotations |
| 11. Modular Deployment | Ansible roles for app, Kubernetes, monitoring, and Vault |
| 12. Live Patching | Rolling update strategy and rollout demo script |

## Application Layer

The project uses a delivery order processing system:

```text
Customer -> Order API -> Kafka/Redpanda Queue -> Worker Pods -> Redis Status Store
```

This aligns strongly with chaos engineering because failures are observable:

- worker pod killed: queue backlog grows
- CPU stress: HPA scales workers
- network delay: processing latency increases
- high failed jobs: healing controller restarts workers
