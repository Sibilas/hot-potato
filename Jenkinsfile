pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = 'hot-potato'
        DOCKER_IMAGE_TAG = 'latest'
        CONTAINER_NAME = 'hotpotato'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker stop ${CONTAINER_NAME} || true" 
                    sh "docker rm ${CONTAINER_NAME} || true"
                    sh "docker compose up -d --build"
                }
            }
        }
    }
}
