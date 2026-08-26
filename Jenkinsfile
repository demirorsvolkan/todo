pipeline {
    agent any

    stages {
        stage('Checkout Test') {
            steps {
                echo 'GitHub repository Jenkins workspace ine geldi.'
                sh 'ls -la'
            }
        }

        stage('Docker Test') {
            steps {
                echo 'Jenkins Docker bağlantısı test ediliyor.'
                sh 'docker --version'
                sh 'docker ps'
            }
        }

        stage('Build Backend Image') {
            steps {
                echo 'Backend Docker image oluşturuluyor.'
                sh 'docker build -t volkandemirors/todo-backend:latest ./backend'
            }
        }

        stage('Build Frontend Image') {
            steps {
                echo 'Frontend Docker image oluşturuluyor.'
                sh 'docker build -t volkandemirors/todo-frontend:latest ./frontend'
            }
        }

        stage('Docker Image Test') {
            steps {
                echo 'Oluşturulan Docker imageları kontrol ediliyor.'
                sh 'docker images | grep todo'
            }
        }

        stage('Docker Hub Login') {
            steps {
                echo 'Docker Hub giriş yapılıyor.'

                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {
                    sh 'echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin'
                }
            }
        }

        stage('Push Images') {
            steps {
                echo 'Docker imageları Docker Huba gönderiliyor.'

                sh 'docker push volkandemirors/todo-backend:latest'
                sh 'docker push volkandemirors/todo-frontend:latest'
            }
        }
    }

    post {
        success {
            echo 'GitHub → Jenkins → Docker → Docker Hub başarılı!'
        }

        always {
            sh 'docker logout || true'
        }
    }
}
