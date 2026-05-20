# LitmusChaos Experiments

Install LitmusChaos first:

```bash
./scripts/install-litmus.sh
```

The installer applies the Litmus operator, creates the `litmus-admin` service
account in the `job-platform` namespace, and installs the `pod-delete`,
`pod-cpu-hog`, and `pod-network-latency` ChaosExperiment resources used by this
project. The YAML files in `chaos/experiments` create ChaosEngine resources that
target the `job-worker` pods.

Run the reliable viva/demo pod-delete experiment:

```bash
./scripts/run-litmus-pod-delete.sh
```

Useful checks during a chaos run:

```bash
kubectl -n job-platform get pods -w
kubectl -n job-platform get hpa
kubectl -n job-platform logs deploy/healing-controller -f
curl http://localhost:8000/metrics
```
