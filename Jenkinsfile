pipeline {

    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    environment {
        GITHUB_REPO = 'demirorsvolkan/todo'

        BACKEND_DIR = 'backend'
        FRONTEND_DIR = 'frontend'

        DOCKERHUB_BACKEND_REPO = 'volkandemirors/todo-backend'
        DOCKERHUB_FRONTEND_REPO = 'volkandemirors/todo-frontend'
    }

    stages {

        stage('01 - Checkout') {
            steps {
                checkout scm

                sh '''
                    set -eu
                    git fetch --tags --force
                '''
            }
        }

        stage('02 - Current Commit') {
            steps {
                script {

                    env.CURRENT_SHA = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    env.CURRENT_SHORT_SHA = sh(
                        script: 'git rev-parse --short=7 HEAD',
                        returnStdout: true
                    ).trim()

                    echo """
========== CURRENT COMMIT ==========

Current SHA : ${env.CURRENT_SHA}
Short SHA   : ${env.CURRENT_SHORT_SHA}

"""
                }
            }
        }

        stage('03 - Versioning') {
            steps {
                script {

                    def versioningOutput = sh(
                        script: 'python3 scripts/versioning.py',
                        returnStdout: true
                    ).trim()

                    echo """
========== VERSIONING OUTPUT ==========

${versioningOutput}

========================================
"""

                    versioningOutput
                        .readLines()
                        .each { line ->

                            def separatorIndex = line.indexOf('=')

                            if (separatorIndex > 0) {

                                def key = line
                                    .substring(0, separatorIndex)
                                    .trim()

                                def value = line
                                    .substring(separatorIndex + 1)
                                    .trim()

                                env."${key.toUpperCase()}" = value
                            }
                        }

                    echo """
========== VERSIONING RESULT ==========

Backend:
  Release : ${env.BACKEND_RELEASE}
  Version : ${env.BACKEND_VERSION ?: 'NO RELEASE'}
  Bump    : ${env.BACKEND_BUMP}
  Tag     : ${env.BACKEND_PREVIOUS_TAG ?: 'YOK'}
  Files   : ${env.BACKEND_CHANGED_FILES}

Frontend:
  Release : ${env.FRONTEND_RELEASE}
  Version : ${env.FRONTEND_VERSION ?: 'NO RELEASE'}
  Bump    : ${env.FRONTEND_BUMP}
  Tag     : ${env.FRONTEND_PREVIOUS_TAG ?: 'YOK'}
  Files   : ${env.FRONTEND_CHANGED_FILES}

========================================
"""
                }
            }
        }

        stage('04 - Prepare Release Metadata') {
            steps {
                script {

                    if (env.BACKEND_RELEASE == 'true') {

                        env.BACKEND_FULL_TAG =
                            "backend/${env.BACKEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"

                        env.BACKEND_DOCKER_VERSION_TAG =
                            env.BACKEND_VERSION

                        env.BACKEND_DOCKER_SHA_TAG =
                            "sha-${env.CURRENT_SHORT_SHA}"
                    }

                    if (env.FRONTEND_RELEASE == 'true') {

                        env.FRONTEND_FULL_TAG =
                            "frontend/${env.FRONTEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"

                        env.FRONTEND_DOCKER_VERSION_TAG =
                            env.FRONTEND_VERSION

                        env.FRONTEND_DOCKER_SHA_TAG =
                            "sha-${env.CURRENT_SHORT_SHA}"
                    }

                    echo """
========== RELEASE METADATA ==========

Backend:
  Release : ${env.BACKEND_RELEASE}
  Version : ${env.BACKEND_VERSION ?: 'NO BUILD'}
  Git Tag : ${env.BACKEND_FULL_TAG ?: 'NO BUILD'}

Frontend:
  Release : ${env.FRONTEND_RELEASE}
  Version : ${env.FRONTEND_VERSION ?: 'NO BUILD'}
  Git Tag : ${env.FRONTEND_FULL_TAG ?: 'NO BUILD'}

========================================
"""
                }
            }
        }

        stage('05 - Release Check') {
            when {
                expression {
                    env.BACKEND_RELEASE == 'true' ||
                    env.FRONTEND_RELEASE == 'true'
                }
            }

            steps {
                echo '''
==================================================

Release gerektiren değişiklik bulundu.

Docker image oluşturma,
Docker Hub push
ve GitHub tag işlemleri başlatılacak.

==================================================
'''
            }
        }

        stage('06 - Docker Image Build') {
            when {
                expression {
                    env.BACKEND_RELEASE == 'true' ||
                    env.FRONTEND_RELEASE == 'true'
                }
            }

            steps {
                script {

                    if (env.BACKEND_RELEASE == 'true') {

                        echo '========== BUILD BACKEND IMAGE =========='

                        sh """
                            docker build \
                                -t '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_VERSION_TAG}' \
                                -t '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_SHA_TAG}' \
                                '${BACKEND_DIR}'
                        """
                    }

                    if (env.FRONTEND_RELEASE == 'true') {

                        echo '========== BUILD FRONTEND IMAGE =========='

                        sh """
                            docker build \
                                -t '${DOCKERHUB_FRONTEND_REPO}:${env.FRONTEND_DOCKER_VERSION_TAG}' \
                                -t '${DOCKERHUB_FRONTEND_REPO}:${env.FRONTEND_DOCKER_SHA_TAG}' \
                                '${FRONTEND_DIR}'
                        """
                    }
                }
            }
        }

        stage('07 - Docker Hub Push') {
            when {
                expression {
                    env.BACKEND_RELEASE == 'true' ||
                    env.FRONTEND_RELEASE == 'true'
                }
            }

            steps {
                script {

                    withCredentials([
                        usernamePassword(
                            credentialsId: 'dockerhub-credentials',
                            usernameVariable: 'DOCKER_USERNAME',
                            passwordVariable: 'DOCKER_PASSWORD'
                        )
                    ]) {

                        sh '''
                            set -eu
                            set +x

                            echo "$DOCKER_PASSWORD" |
                                docker login \
                                    -u "$DOCKER_USERNAME" \
                                    --password-stdin
                        '''

                        if (env.BACKEND_RELEASE == 'true') {

                            sh """
                                docker push \
                                    '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_VERSION_TAG}'

                                docker push \
                                    '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_SHA_TAG}'
                            """
                        }

                        if (env.FRONTEND_RELEASE == 'true') {

                            sh """
                                docker push \
                                    '${DOCKERHUB_FRONTEND_REPO}:${env.FRONTEND_DOCKER_VERSION_TAG}'

                                docker push \
                                    '${DOCKERHUB_FRONTEND_REPO}:${env.FRONTEND_DOCKER_SHA_TAG}'
                            """
                        }

                        sh 'docker logout'
                    }
                }
            }
        }

        stage('08 - Create GitHub Tags') {
            when {
                expression {
                    env.BACKEND_RELEASE == 'true' ||
                    env.FRONTEND_RELEASE == 'true'
                }
            }

            steps {
                script {

                    withCredentials([
                        string(
                            credentialsId: 'github-token',
                            variable: 'GITHUB_TOKEN'
                        )
                    ]) {

                        if (env.BACKEND_RELEASE == 'true') {

                            sh """
                                curl \
                                    -sS \
                                    -f \
                                    -X POST \
                                    -H "Authorization: Bearer \\$GITHUB_TOKEN" \
                                    -H "Accept: application/vnd.github+json" \
                                    "https://api.github.com/repos/${GITHUB_REPO}/git/refs" \
                                    -d '{
                                        "ref":"refs/tags/${env.BACKEND_FULL_TAG}",
                                        "sha":"${env.CURRENT_SHA}"
                                    }'
                            """
                        }

                        if (env.FRONTEND_RELEASE == 'true') {

                            sh """
                                curl \
                                    -sS \
                                    -f \
                                    -X POST \
                                    -H "Authorization: Bearer \\$GITHUB_TOKEN" \
                                    -H "Accept: application/vnd.github+json" \
                                    "https://api.github.com/repos/${GITHUB_REPO}/git/refs" \
                                    -d '{
                                        "ref":"refs/tags/${env.FRONTEND_FULL_TAG}",
                                        "sha":"${env.CURRENT_SHA}"
                                    }'
                            """
                        }
                    }
                }
            }
        }
    }

    post {

        always {

            echo """
========================================

 Jenkins Versioning Pipeline Finished

========================================

Commit:
${env.CURRENT_SHA ?: 'N/A'}

Backend:
  Changed : ${env.BACKEND_CHANGED_FILES ?: '0'}
  Release : ${env.BACKEND_RELEASE ?: 'N/A'}
  Version : ${env.BACKEND_VERSION ?: 'N/A'}
  Tag     : ${env.BACKEND_FULL_TAG ?: 'N/A'}

Frontend:
  Changed : ${env.FRONTEND_CHANGED_FILES ?: '0'}
  Release : ${env.FRONTEND_RELEASE ?: 'N/A'}
  Version : ${env.FRONTEND_VERSION ?: 'N/A'}
  Tag     : ${env.FRONTEND_FULL_TAG ?: 'N/A'}

========================================
"""
        }
    }
}