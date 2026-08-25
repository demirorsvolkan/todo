pipeline {
    agent any

    stages {
        stage('Checkout Test') {
            steps {
                echo 'GitHub repository Jenkins workspace ine geldi.'
                sh 'ls -la'
            }
        }
    }

    post {
        success {
            echo 'GitHub → Jenkins bağlantısı başarılı!'
        }
    }
}
