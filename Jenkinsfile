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
    string(name: 'DOCKERHUB_ORG', defaultValue: 'ayush81080', description: 'Docker Hub namespace')
    string(name: 'IMAGE_TAG', defaultValue: 'auto', description: 'Image tag to build and deploy. Use auto for the Git commit SHA.')
    string(name: 'K8S_NAMESPACE', defaultValue: 'job-platform', description: 'Target Kubernetes namespace')
    booleanParam(name: 'PUSH_IMAGES', defaultValue: true, description: 'Push built images to Docker Hub')
    booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: true, description: 'Deploy images to Kubernetes')
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Resolve Image Tags') {
      steps {
        script {
          def requestedTag = params.IMAGE_TAG?.trim()
          env.RESOLVED_IMAGE_TAG = (requestedTag && requestedTag != 'auto')
              ? requestedTag
              : sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim()
          env.ORDER_API_IMAGE = "${params.DOCKERHUB_ORG}/order-api:${env.RESOLVED_IMAGE_TAG}"
          env.WORKER_IMAGE = "${params.DOCKERHUB_ORG}/job-worker:${env.RESOLVED_IMAGE_TAG}"
          env.HEALER_IMAGE = "${params.DOCKERHUB_ORG}/healing-controller:${env.RESOLVED_IMAGE_TAG}"
          echo "Resolved image tag: ${env.RESOLVED_IMAGE_TAG}"
        }
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
        sh 'kubectl -n "$K8S_NAMESPACE" rollout status deployment/redis --timeout=180s'
        sh 'kubectl -n "$K8S_NAMESPACE" rollout status deployment/redpanda --timeout=180s'
        sh 'kubectl -n "$K8S_NAMESPACE" wait --for=condition=complete job/redpanda-topic-init --timeout=180s'
        sh 'kubectl -n "$K8S_NAMESPACE" set image deployment/order-api order-api="$ORDER_API_IMAGE"'
        sh 'kubectl -n "$K8S_NAMESPACE" set image deployment/job-worker worker="$WORKER_IMAGE"'
        sh 'kubectl -n "$K8S_NAMESPACE" set image deployment/healing-controller healing-controller="$HEALER_IMAGE"'
        sh 'kubectl -n "$K8S_NAMESPACE" rollout restart deployment/job-worker'
        sh 'kubectl -n "$K8S_NAMESPACE" rollout status deployment/order-api --timeout=240s'
        sh 'kubectl -n "$K8S_NAMESPACE" rollout status deployment/job-worker --timeout=240s'
        sh 'kubectl -n "$K8S_NAMESPACE" rollout status deployment/healing-controller --timeout=240s'
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
