FROM jenkins/jenkins:lts-jdk17

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
      gnupg \
      python3 \
      python3-pip \
      python3-pytest \
      docker-cli \
      docker.io \
    && curl -fsSL "https://dl.k8s.io/release/v1.31.0/bin/linux/arm64/kubectl" -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER jenkins

COPY infra/jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY infra/jenkins/casc.yaml /usr/share/jenkins/ref/casc.yaml
COPY infra/jenkins/init.groovy.d/seed-platform-job.groovy /usr/share/jenkins/ref/init.groovy.d/seed-platform-job.groovy
