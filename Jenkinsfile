pipeline {
  agent any

  triggers {
    githubPush()
    pollSCM('H/2 * * * *')
  }

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  parameters {
    string(name: 'DOCKERHUB_ORG', defaultValue: 'your-dockerhub-username', description: 'Docker Hub namespace')
    string(name: 'IMAGE_TAG', defaultValue: 'dev', description: 'Image tag to build and deploy')
    string(name: 'K8S_NAMESPACE', defaultValue: 'job-platform', description: 'Target Kubernetes namespace')
    booleanParam(name: 'PUSH_IMAGES', defaultValue: false, description: 'Push built images to Docker Hub')
    booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: false, description: 'Deploy images to Kubernetes')
  }

  environment {
    ORDER_API_IMAGE = "${params.DOCKERHUB_ORG}/order-api:${params.IMAGE_TAG}"
    WORKER_IMAGE = "${params.DOCKERHUB_ORG}/job-worker:${params.IMAGE_TAG}"
    HEALER_IMAGE = "${params.DOCKERHUB_ORG}/healing-controller:${params.IMAGE_TAG}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Unit Tests') {
      steps {
        sh './scripts/run-python-tests.sh'
        sh 'mvn -q -f services/order-api/pom.xml test'
      }
    }

    stage('Build Docker Images') {
      steps {
        sh 'docker build -f services/order-api/Dockerfile -t "$ORDER_API_IMAGE" .'
        sh 'docker build -f services/worker/Dockerfile -t "$WORKER_IMAGE" .'
        sh 'docker build -f services/healing-controller/Dockerfile -t "$HEALER_IMAGE" .'
      }
    }

    stage('Push Images to Docker Hub') {
      when {
        expression { return params.PUSH_IMAGES }
      }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
          sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin'
          sh 'docker push "$ORDER_API_IMAGE"'
          sh 'docker push "$WORKER_IMAGE"'
          sh 'docker push "$HEALER_IMAGE"'
        }
      }
    }

    stage('Deploy to Kubernetes') {
      when {
        expression { return params.DEPLOY_TO_K8S }
      }
      steps {
        sh 'kubectl apply -k k8s/base'
        sh 'kubectl -n "$K8S_NAMESPACE" set image deployment/order-api order-api="$ORDER_API_IMAGE"'
        sh 'kubectl -n "$K8S_NAMESPACE" set image deployment/job-worker worker="$WORKER_IMAGE"'
        sh 'kubectl -n "$K8S_NAMESPACE" set image deployment/healing-controller healing-controller="$HEALER_IMAGE"'
        sh 'kubectl -n "$K8S_NAMESPACE" rollout status deployment/order-api --timeout=180s'
        sh 'kubectl -n "$K8S_NAMESPACE" rollout status deployment/job-worker --timeout=180s'
        sh 'kubectl -n "$K8S_NAMESPACE" rollout status deployment/healing-controller --timeout=180s'
      }
    }
  }

  post {
    always {
      sh 'docker images | grep -E "order-api|job-worker|healing-controller" || true'
      sh 'kubectl -n "$K8S_NAMESPACE" get deploy,pod,svc,hpa || true'
    }
  }
}
