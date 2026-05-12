# Jenkins Runbook

## Local Jenkins Controller

Start Docker Desktop, then run:

```bash
cd /Users/ayushkumar/Documents/Codex/automated-chaos-testing-self-healing-microservices-platform
./scripts/start-jenkins.sh
```

Open:

```text
http://localhost:8080
```

Local demo login:

```text
Username: admin
Password: admin
```

The local setup automatically creates a pipeline job:

```text
automated-chaos-platform
```

That job reads the root `Jenkinsfile` from this repository. It also has a local
SCM polling trigger for laptop demos. The real GitHub webhook trigger is declared
inside the `Jenkinsfile` with:

```groovy
triggers {
  githubPush()
}
```

## Real GitHub + Docker Hub Setup

1. Push this repository to GitHub.
2. In Jenkins, create a Docker Hub credential:

```text
ID: dockerhub-creds
Type: Username with password
```

3. Ensure the Jenkins controller or agent can run:

```bash
docker version
kubectl config current-context
python3 -m pytest
```

4. Configure the GitHub repository webhook:

```text
http://<jenkins-host>/github-webhook/
```

5. Set pipeline parameters:

```text
DOCKERHUB_ORG=<your Docker Hub username>
IMAGE_TAG=<build tag>
K8S_NAMESPACE=job-platform
PUSH_IMAGES=true
DEPLOY_TO_K8S=true
```

For the laptop-only Jenkins demo, leave `PUSH_IMAGES=false` and
`DEPLOY_TO_K8S=false`. Jenkins will still checkout, test, and build all Docker
images. Enable both flags when Docker Hub credentials and Kubernetes context are
ready.

## What Jenkins Controls

The `Jenkinsfile` controls the full CI/CD process:

1. Checkout from GitHub or local SCM.
2. Install test dependency and run unit tests.
3. Build service Docker images.
4. Push images to Docker Hub.
5. Deploy manifests to Kubernetes.
6. Update running deployments with new images.
7. Verify rollout status.

## Useful Commands

```bash
docker compose -f docker-compose.jenkins.yml logs -f jenkins
docker compose -f docker-compose.jenkins.yml down
```
