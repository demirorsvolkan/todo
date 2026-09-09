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

        stage('03 - GitHub Authentication') {
            steps {
                echo '========== GITHUB AUTHENTICATION =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {

                    sh '''
                        set -eu
                        set +x

                        test -n "$GITHUB_TOKEN"

                        HTTP_CODE=$(
                            curl \
                                -sS \
                                -o /tmp/github-user.json \
                                -w '%{http_code}' \
                                -H "Authorization: Bearer $GITHUB_TOKEN" \
                                -H "Accept: application/vnd.github+json" \
                                -H "X-GitHub-Api-Version: 2022-11-28" \
                                https://api.github.com/user
                        )

                        echo "GitHub authentication HTTP status: $HTTP_CODE"

                        if [ "$HTTP_CODE" != "200" ]; then
                            echo "GitHub authentication FAILED."
                            cat /tmp/github-user.json || true
                            exit 1
                        fi

                        echo "GitHub authentication OK."
                    '''
                }
            }
        }

        stage('04 - GitHub Repository Access') {
            steps {
                echo '========== GITHUB REPOSITORY ACCESS =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {

                    sh '''
                        set -eu
                        set +x

                        HTTP_STATUS=$(
                            curl \
                                -sS \
                                -o /tmp/github-repo.json \
                                -w "%{http_code}" \
                                -H "Authorization: Bearer $GITHUB_TOKEN" \
                                -H "Accept: application/vnd.github+json" \
                                -H "X-GitHub-Api-Version: 2022-11-28" \
                                "https://api.github.com/repos/$GITHUB_REPO"
                        )

                        echo "GitHub repository HTTP status: $HTTP_STATUS"

                        if [ "$HTTP_STATUS" != "200" ]; then
                            echo "GitHub repository access FAILED."
                            cat /tmp/github-repo.json || true
                            exit 1
                        fi

                        echo "GitHub repository access OK."
                    '''
                }
            }
        }

        stage('05 - Versioning') {
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

        stage('06 - Prepare Release Metadata') {
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

        stage('07 - Release Check') {
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

        stage('08 - Docker Image Build') {
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

        stage('09 - Docker Hub Push') {
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

        stage('10 - Create GitHub Tags') {
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

                            sh '''
                                set -eu
                                set +x

                                curl \
                                    -sS \
                                    -f \
                                    -X POST \
                                    -H "Authorization: Bearer $GITHUB_TOKEN" \
                                    -H "Accept: application/vnd.github+json" \
                                    -H "X-GitHub-Api-Version: 2022-11-28" \
                                    "https://api.github.com/repos/$GITHUB_REPO/git/refs" \
                                    -d '{
                                        "ref":"refs/tags/'"${BACKEND_FULL_TAG}"'",
                                        "sha":"'"${CURRENT_SHA}"'"
                                    }'
                            '''
                        }

                        if (env.FRONTEND_RELEASE == 'true') {

                            sh '''
                                set -eu
                                set +x

                                curl \
                                    -sS \
                                    -f \
                                    -X POST \
                                    -H "Authorization: Bearer $GITHUB_TOKEN" \
                                    -H "Accept: application/vnd.github+json" \
                                    -H "X-GitHub-Api-Version: 2022-11-28" \
                                    "https://api.github.com/repos/$GITHUB_REPO/git/refs" \
                                    -d '{
                                        "ref":"refs/tags/'"${FRONTEND_FULL_TAG}"'",
                                        "sha":"'"${CURRENT_SHA}"'"
                                    }'
                            '''
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