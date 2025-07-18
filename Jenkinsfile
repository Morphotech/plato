project_version=''

pipeline {
    agent {
        label env.agent_label
    }

    environment {
        registryUrl = 'https://registry.hub.docker.com'
        registryCredential = 'vizidox'
    }


    stages {
        stage('Build API'){
            steps {
                script {
                    dockerImage = docker.build("plato-api", "-f Dockerfile --platform linux/amd64,linux/arm64 .")
                }
            }
        }
        stage('Run Tests') {
            steps{
                script{
                    if(!params.get('skipTests', false)) {
                        sh 'docker compose -f docker-compose.ci.yml up -d database'
                        sh 'docker compose -f docker-compose.ci.yml run --rm test-plato'
                    }
                }
            }
        }
        stage('Get project version') {
            steps {
                script {
                    project_version = sh(script: 'docker compose run --rm plato-api poetry version', returnStdout: true).trim().split(' ')[-1]
                }
                sh "echo 'current project version: ${project_version}'"
            }
        }
        stage("Push to Docker Hub and GitHub"){
            steps {
                script {
                    docker.withRegistry( registryUrl, registryCredential ) {
                        dockerImage.push("${project_version}")
                    }
                }
            }
        }
    }
    post {
        cleanup{
            sh "docker compose -f docker-compose.ci.yml down"
            sh "docker image prune -af"
        }
    }
}
