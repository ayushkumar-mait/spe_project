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

The seed job is refreshed from `infra/jenkins/init.groovy.d` on Jenkins startup,
so rerunning `./scripts/start-jenkins.sh` updates the job SCM URL and polling
settings without deleting Jenkins data.

That job reads the root `Jenkinsfile` from this repository. The pipeline supports
both GitHub webhooks and SCM polling. The webhook gives near-instant builds when
Jenkins has a stable public URL. The polling trigger is the laptop-friendly
fallback: Jenkins checks GitHub every few minutes, so you do not need to update
the ngrok URL every time it changes.

```groovy
triggers {
  githubPush()
  pollSCM('H/2 * * * *')
}
```

## Real GitHub + Docker Hub Setup

1. Push this repository to GitHub. The local Jenkins seed job points directly to:

```text
https://github.com/ayushkumar-mait/spe_project.git
```

2. In Jenkins, create a Docker Hub credential:

```text
ID: dockerhub-creds
Type: Username with password
```

3. Ensure the Jenkins controller or agent can run:

```bash
docker version
kubectl config current-context
./scripts/run-python-tests.sh
mvn -f services/order-api/pom.xml test
```

4. Optional: configure the GitHub repository webhook if Jenkins has a stable
public URL:

```text
http://<jenkins-host>/github-webhook/
```

If you are using temporary ngrok URLs, you can skip the webhook and rely on
`pollSCM('H/2 * * * *')`. Jenkins will trigger after it detects a new commit on
GitHub, usually within about two minutes.

5. Set pipeline parameters:

```text
DOCKERHUB_ORG=ayush81080
IMAGE_TAG=auto
K8S_NAMESPACE=job-platform
PUSH_IMAGES=true
DEPLOY_TO_K8S=true
```

These are now the defaults in the `Jenkinsfile`, so webhook and SCM polling
builds automatically test, build, push Docker Hub images, deploy to Kubernetes,
and verify rollouts. `IMAGE_TAG=auto` tags images with the Git commit SHA. For a
laptop-only build, manually override `PUSH_IMAGES=false` and `DEPLOY_TO_K8S=false`.

## What Jenkins Controls

The `Jenkinsfile` controls the full CI/CD process:

1. Checkout from GitHub or local SCM.
2. Run Python tests and Spring Boot Order API tests.
3. Build service Docker images, including `order-api`.
4. Push images to Docker Hub.
5. Deploy manifests to Kubernetes.
6. Update running deployments with new images.
7. Verify rollout status.

## Useful Commands

```bash
docker compose -f docker-compose.jenkins.yml logs -f jenkins
docker compose -f docker-compose.jenkins.yml down
```
