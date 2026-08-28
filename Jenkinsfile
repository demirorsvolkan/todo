pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(false)
    }

    environment {
        BACKEND_DIR = 'backend'
        FRONTEND_DIR = 'frontend'

        // Jenkins Credentials
        GITHUB_CREDENTIALS = 'github-credentials'
        DOCKER_CREDENTIALS = 'dockerhub-credentials'

        // Docker Hub repository
        DOCKERHUB_REPO = 'YOUR_DOCKERHUB_USERNAME/YOUR_REPOSITORY'
    }

    stages {

        // ============================================================
        // 01 - Checkout
        // ============================================================
        stage('01 - Checkout') {
            steps {
                checkout scm

                sh '''
                    git fetch --all --tags --prune
                '''
            }
        }

        // ============================================================
        // 02 - Current Commit
        // ============================================================
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

        // ============================================================
        // 03 - GitHub Authentication
        // ============================================================
        stage('03 - GitHub Authentication') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: env.GITHUB_CREDENTIALS,
                        usernameVariable: 'GITHUB_USER',
                        passwordVariable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        git config user.name "$GITHUB_USER"
                        git config user.email "$GITHUB_USER@users.noreply.github.com"

                        git remote set-url origin \
                          "https://${GITHUB_USER}:${GITHUB_TOKEN}@$(git remote get-url origin | sed -E 's#https://##' | sed 's#^[^/]*/##')"
                    '''
                }
            }
        }

        // ============================================================
        // 04 - Find Last Backend / Frontend Version
        // ============================================================
        stage('04 - Find Last Component Versions') {
            steps {
                script {

                    /*
                     * SADECE bizim formatımızdaki tag'lar alınır.
                     *
                     * backend/v1.2.4-sha.a1b2c3d
                     * frontend/v1.3.0-sha.f91e82a
                     */

                    env.LAST_BACKEND_TAG = sh(
                        script: '''
                            git tag -l 'backend/v*' |
                            grep -E '^backend/v[0-9]+\\.[0-9]+\\.[0-9]+-sha\\.[0-9a-fA-F]+$' |
                            sort -V |
                            tail -n 1 || true
                        ''',
                        returnStdout: true
                    ).trim()

                    env.LAST_FRONTEND_TAG = sh(
                        script: '''
                            git tag -l 'frontend/v*' |
                            grep -E '^frontend/v[0-9]+\\.[0-9]+\\.[0-9]+-sha\\.[0-9a-fA-F]+$' |
                            sort -V |
                            tail -n 1 || true
                        ''',
                        returnStdout: true
                    ).trim()

                    echo """
========== LAST COMPONENT TAGS ==========
Last Backend Tag  : ${env.LAST_BACKEND_TAG ?: 'NONE'}
Last Frontend Tag : ${env.LAST_FRONTEND_TAG ?: 'NONE'}
"""
                }
            }
        }

        // ============================================================
        // 05 - Detect Backend Changes
        // ============================================================
        stage('05 - Detect Backend Changes') {
            steps {
                script {

                    if (!env.LAST_BACKEND_TAG) {

                        echo 'No previous backend version found.'

                        /*
                         * İlk backend versiyonu.
                         * Backend klasöründe dosya varsa build edilir.
                         */
                        def backendFiles = sh(
                            script: '''
                                git ls-tree -r --name-only HEAD -- backend/ |
                                grep -v '^$' || true
                            ''',
                            returnStdout: true
                        ).trim()

                        env.BACKEND_CHANGED =
                            backendFiles ? 'true' : 'false'

                        env.BACKEND_BASE_COMMIT = ''

                    } else {

                        /*
                         * ÇOK ÖNEMLİ:
                         *
                         * Önceki commit değil,
                         * son backend version tag'ının GERÇEK TARGET COMMIT'i
                         * başlangıç noktasıdır.
                         */
                        env.BACKEND_BASE_COMMIT = sh(
                            script: "git rev-list -n 1 '${env.LAST_BACKEND_TAG}'",
                            returnStdout: true
                        ).trim()

                        def changed = sh(
                            script: """
                                git diff --name-only \
                                '${env.BACKEND_BASE_COMMIT}' \
                                '${env.CURRENT_SHA}' \
                                -- '${env.BACKEND_DIR}/'
                            """,
                            returnStdout: true
                        ).trim()

                        env.BACKEND_CHANGED =
                            changed ? 'true' : 'false'

                        echo """
========== BACKEND CHANGE CHECK ==========
Previous Tag    : ${env.LAST_BACKEND_TAG}
Previous Commit : ${env.BACKEND_BASE_COMMIT}
Current Commit  : ${env.CURRENT_SHA}

Changed Files:
${changed ?: 'NONE'}

Backend Changed: ${env.BACKEND_CHANGED}
"""
                    }
                }
            }
        }

        // ============================================================
        // 06 - Detect Frontend Changes
        // ============================================================
        stage('06 - Detect Frontend Changes') {
            steps {
                script {

                    if (!env.LAST_FRONTEND_TAG) {

                        echo 'No previous frontend version found.'

                        def frontendFiles = sh(
                            script: '''
                                git ls-tree -r --name-only HEAD -- frontend/ |
                                grep -v '^$' || true
                            ''',
                            returnStdout: true
                        ).trim()

                        env.FRONTEND_CHANGED =
                            frontendFiles ? 'true' : 'false'

                        env.FRONTEND_BASE_COMMIT = ''

                    } else {

                        env.FRONTEND_BASE_COMMIT = sh(
                            script: "git rev-list -n 1 '${env.LAST_FRONTEND_TAG}'",
                            returnStdout: true
                        ).trim()

                        def changed = sh(
                            script: """
                                git diff --name-only \
                                '${env.FRONTEND_BASE_COMMIT}' \
                                '${env.CURRENT_SHA}' \
                                -- '${env.FRONTEND_DIR}/'
                            """,
                            returnStdout: true
                        ).trim()

                        env.FRONTEND_CHANGED =
                            changed ? 'true' : 'false'

                        echo """
========== FRONTEND CHANGE CHECK ==========
Previous Tag    : ${env.LAST_FRONTEND_TAG}
Previous Commit : ${env.FRONTEND_BASE_COMMIT}
Current Commit  : ${env.CURRENT_SHA}

Changed Files:
${changed ?: 'NONE'}

Frontend Changed: ${env.FRONTEND_CHANGED}
"""
                    }
                }
            }
        }

        // ============================================================
        // 07 - Calculate Versions
        // ============================================================
        stage('07 - Calculate Versions') {
            steps {
                script {

                    if (env.BACKEND_CHANGED == 'true') {

                        if (env.LAST_BACKEND_TAG) {

                            def matcher = (
                                env.LAST_BACKEND_TAG =~
                                /^backend\/v([0-9]+)\.([0-9]+)\.([0-9]+)-sha\.[0-9a-fA-F]+$/
                            )

                            if (!matcher.matches()) {
                                error(
                                    "Invalid backend tag: ${env.LAST_BACKEND_TAG}"
                                )
                            }

                            def major = matcher[0][1].toInteger()
                            def minor = matcher[0][2].toInteger()
                            def patch = matcher[0][3].toInteger()

                            patch++

                            env.BACKEND_VERSION =
                                "v${major}.${minor}.${patch}"

                        } else {
                            env.BACKEND_VERSION = 'v1.0.0'
                        }

                        env.BACKEND_TAG =
                            "backend/${env.BACKEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"

                    }

                    if (env.FRONTEND_CHANGED == 'true') {

                        if (env.LAST_FRONTEND_TAG) {

                            def matcher = (
                                env.LAST_FRONTEND_TAG =~
                                /^frontend\/v([0-9]+)\.([0-9]+)\.([0-9]+)-sha\.[0-9a-fA-F]+$/
                            )

                            if (!matcher.matches()) {
                                error(
                                    "Invalid frontend tag: ${env.LAST_FRONTEND_TAG}"
                                )
                            }

                            def major = matcher[0][1].toInteger()
                            def minor = matcher[0][2].toInteger()
                            def patch = matcher[0][3].toInteger()

                            patch++

                            env.FRONTEND_VERSION =
                                "v${major}.${minor}.${patch}"

                        } else {
                            env.FRONTEND_VERSION = 'v1.0.0'
                        }

                        env.FRONTEND_TAG =
                            "frontend/${env.FRONTEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"
                    }

                    echo """
========== VERSION RESULT ==========
Backend Changed  : ${env.BACKEND_CHANGED}
Backend Version  : ${env.BACKEND_VERSION ?: 'NONE'}
Backend Tag      : ${env.BACKEND_TAG ?: 'NONE'}

Frontend Changed : ${env.FRONTEND_CHANGED}
Frontend Version : ${env.FRONTEND_VERSION ?: 'NONE'}
Frontend Tag     : ${env.FRONTEND_TAG ?: 'NONE'}
"""
                }
            }
        }

        // ============================================================
        // 08 - Docker Hub Validation
        // ============================================================
        stage('08 - Docker Hub Validation') {
            steps {
                script {

                    /*
                     * Burada Docker Hub'daki image metadata'sını
                     * kontrol ediyoruz.
                     *
                     * Amaç:
                     *
                     * v1.2.5 -> başka SHA ile daha önce kullanılmışsa FAIL
                     *
                     * Aynı version + aynı SHA ise:
                     * tekrar build/push yapma.
                     */

                    withCredentials([
                        usernamePassword(
                            credentialsId: env.DOCKER_CREDENTIALS,
                            usernameVariable: 'DOCKER_USER',
                            passwordVariable: 'DOCKER_PASSWORD'
                        )
                    ]) {

                        sh '''
                            echo "$DOCKER_PASSWORD" |
                            docker login \
                              -u "$DOCKER_USER" \
                              --password-stdin
                        '''

                        if (env.BACKEND_CHANGED == 'true') {

                            def backendVersionImage =
                                "${DOCKERHUB_REPO}-backend:${env.BACKEND_VERSION}"

                            def backendShaImage =
                                "${DOCKERHUB_REPO}-backend:sha.${env.CURRENT_SHORT_SHA}"

                            echo "Checking Docker Hub:"
                            echo "${backendVersionImage}"
                            echo "${backendShaImage}"

                            /*
                             * Image yoksa normal şekilde devam edilir.
                             *
                             * Image varsa SHA label'ı okunmaya çalışılır.
                             */
                            def versionExists = sh(
                                script: """
                                    docker manifest inspect \
                                    '${backendVersionImage}' \
                                    >/dev/null 2>&1
                                """,
                                returnStatus: true
                            ) == 0

                            if (versionExists) {
                                error(
                                    "Backend version ${env.BACKEND_VERSION} already exists on Docker Hub. " +
                                    "A version cannot be reused for another commit."
                                )
                            }
                        }

                        if (env.FRONTEND_CHANGED == 'true') {

                            def frontendVersionImage =
                                "${DOCKERHUB_REPO}-frontend:${env.FRONTEND_VERSION}"

                            def versionExists = sh(
                                script: """
                                    docker manifest inspect \
                                    '${frontendVersionImage}' \
                                    >/dev/null 2>&1
                                """,
                                returnStatus: true
                            ) == 0

                            if (versionExists) {
                                error(
                                    "Frontend version ${env.FRONTEND_VERSION} already exists on Docker Hub. " +
                                    "A version cannot be reused for another commit."
                                )
                            }
                        }
                    }
                }
            }
        }

        // ============================================================
        // 09 - Build Backend
        // ============================================================
        stage('09 - Build Backend') {
            when {
                expression {
                    env.BACKEND_CHANGED == 'true'
                }
            }

            steps {
                script {

                    def versionImage =
                        "${DOCKERHUB_REPO}-backend:${env.BACKEND_VERSION}"

                    def shaImage =
                        "${DOCKERHUB_REPO}-backend:sha.${env.CURRENT_SHORT_SHA}"

                    sh """
                        docker build \
                            -t '${versionImage}' \
                            -t '${shaImage}' \
                            '${BACKEND_DIR}'
                    """
                }
            }
        }

        // ============================================================
        // 10 - Build Frontend
        // ============================================================
        stage('10 - Build Frontend') {
            when {
                expression {
                    env.FRONTEND_CHANGED == 'true'
                }
            }

            steps {
                script {

                    def versionImage =
                        "${DOCKERHUB_REPO}-frontend:${env.FRONTEND_VERSION}"

                    def shaImage =
                        "${DOCKERHUB_REPO}-frontend:sha.${env.CURRENT_SHORT_SHA}"

                    sh """
                        docker build \
                            -t '${versionImage}' \
                            -t '${shaImage}' \
                            '${FRONTEND_DIR}'
                    """
                }
            }
        }

        // ============================================================
        // 11 - Push Backend
        // ============================================================
        stage('11 - Push Backend') {
            when {
                expression {
                    env.BACKEND_CHANGED == 'true'
                }
            }

            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: env.DOCKER_CREDENTIALS,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {

                    sh """
                        docker push \
                            '${DOCKERHUB_REPO}-backend:${env.BACKEND_VERSION}'

                        docker push \
                            '${DOCKERHUB_REPO}-backend:sha.${env.CURRENT_SHORT_SHA}'
                    """
                }
            }
        }

        // ============================================================
        // 12 - Push Frontend
        // ============================================================
        stage('12 - Push Frontend') {
            when {
                expression {
                    env.FRONTEND_CHANGED == 'true'
                }
            }

            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: env.DOCKER_CREDENTIALS,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {

                    sh """
                        docker push \
                            '${DOCKERHUB_REPO}-frontend:${env.FRONTEND_VERSION}'

                        docker push \
                            '${DOCKERHUB_REPO}-frontend:sha.${env.CURRENT_SHORT_SHA}'
                    """
                }
            }
        }

        // ============================================================
        // 13 - Create GitHub Tags
        // ============================================================
        stage('13 - Create GitHub Tags') {
            steps {
                script {

                    if (env.BACKEND_CHANGED == 'true') {

                        sh """
                            git tag \
                                '${env.BACKEND_TAG}' \
                                '${env.CURRENT_SHA}'

                            git push origin \
                                '${env.BACKEND_TAG}'
                        """
                    }

                    if (env.FRONTEND_CHANGED == 'true') {

                        sh """
                            git tag \
                                '${env.FRONTEND_TAG}' \
                                '${env.CURRENT_SHA}'

                            git push origin \
                                '${env.FRONTEND_TAG}'
                        """
                    }

                    echo """
========== TAG RESULT ==========
Backend  : ${env.BACKEND_TAG ?: 'NO TAG'}
Frontend : ${env.FRONTEND_TAG ?: 'NO TAG'}
"""
                }
            }
        }
    }

    // ================================================================
    // POST
    // ================================================================
    post {

        always {
            sh '''
                docker logout || true
            '''

            echo """
========== PIPELINE SUMMARY ==========

Current Commit : ${CURRENT_SHA}
Short SHA      : ${CURRENT_SHORT_SHA}

Backend Changed  : ${BACKEND_CHANGED}
Backend Version  : ${BACKEND_VERSION}
Backend Tag      : ${BACKEND_TAG}

Frontend Changed : ${FRONTEND_CHANGED}
Frontend Version : ${FRONTEND_VERSION}
Frontend Tag     : ${FRONTEND_TAG}
"""
        }

        success {
            echo 'Versioning pipeline completed successfully.'
        }

        failure {
            echo 'Versioning pipeline FAILED.'
        }
    }
}
