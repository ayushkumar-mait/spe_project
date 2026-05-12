# LitmusChaos Experiments

Install LitmusChaos first:

```bash
kubectl apply -f https://litmuschaos.github.io/litmus/litmus-operator-v3.0.0.yaml
```

Then install the experiment definitions from the Litmus hub for `pod-delete`,
`pod-cpu-hog`, and `pod-network-latency`, or use the Litmus portal to select the
same experiments. The YAML files in `chaos/experiments` create ChaosEngine
resources that target the `job-worker` pods.

Useful checks during a chaos run:

```bash
kubectl -n job-platform get pods -w
kubectl -n job-platform get hpa
kubectl -n job-platform logs deploy/healing-controller -f
curl http://localhost:8000/metrics
```

