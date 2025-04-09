pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = 'hot-potato'
        DOCKER_IMAGE_TAG = 'latest'
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
                    sh "docker compose up -d --build"
                }
            }
        }
    }
}
