# Rubric Mapping

| Evaluation Requirement | Implemented Artifact |
| --- | --- |
| Version control with Git/GitHub | Repository-ready structure, `.gitignore`, Jenkins GitHub trigger instructions |
| Jenkins fetches and builds updated code | `Jenkinsfile` checkout and build stages |
| Automated tests | `pytest.ini`, tests for shared models, worker processor, and healing policy |
| Docker images | Dockerfiles for Job API, Worker, and Healing Controller |
| Push images to Docker Hub | `Jenkinsfile` Docker Hub push stage |
| Deploy generated images | `Jenkinsfile` Kubernetes deploy stage, `k8s/base` manifests |
| Refresh shows new changes seamlessly | Kubernetes rolling update strategy and rollout verification |
| Docker Compose | `docker-compose.yml` with app, queue, Redis, ELK, Vault |
| Kubernetes orchestration | Deployments, Services, ConfigMap, RBAC, PDB, HPA |
| ELK logging | Logstash pipeline, Docker GELF logging, Kubernetes Filebeat DaemonSet |
| Kibana visualization | Kibana setup instructions and recommended dashboard panels |
| Vault secure storage | Vault KV policy, bootstrap script, Vault Agent annotations |
| Ansible modular roles | `app-role`, `k8s-role`, `monitoring-role`, `vault-role` |
| HPA scalability | `job-worker-hpa` and `job-api-hpa` |
| Live patching / zero downtime | Rolling update strategy with `maxUnavailable: 0` |
| Innovation | LitmusChaos plus custom self-healing controller for backlog/failure recovery |
| Domain-specific project | DevOps/AIOps reliability platform for distributed job processing |

## Marks Strategy

Working project:

- Run local Docker Compose demo.
- Show Jenkins pipeline stages.
- Deploy to Kubernetes and show pods/services/HPA.
- Submit jobs and show status/metrics.
- Open Kibana and show application logs.

Advanced features:

- Show Vault policy and injected secret annotations.
- Show Ansible roles.
- Show HPA behavior.

Innovation:

- Run chaos experiment.
- Show self-healing controller logs and Kubernetes recovery.

