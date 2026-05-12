# Kibana Dashboard Setup

Use Kibana to create a data view for:

```text
job-platform-logs-*
```

Recommended dashboard panels:

1. Count of logs by `app.event`.
2. Count of failures where `app.event: job_processing_failed`.
3. Job submissions over time where `app.event: job_submitted`.
4. Healing actions where `app.event: healing_action_selected`.
5. Logs table with `app.job_id`, `app.trace_id`, `app.service`, `app.message`.

For the viva/demo, open Kibana and filter by:

```text
project: automated-chaos-testing-self-healing-microservices-platform
```

