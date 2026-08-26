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
                sh 'docker build -t todo-backend:latest ./backend'
            }
        }
    }

    post {
        success {
            echo 'GitHub → Jenkins → Docker → Backend Build başarılı!'
        }
    }
}
