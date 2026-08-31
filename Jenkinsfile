pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(false)
    }

    environment {
        GITHUB_REPO = 'demirorsvolkan/todo'

        BACKEND_DIR = 'backend'
        FRONTEND_DIR = 'frontend'

        // Docker Hub'daki İKİ AYRI repository
        DOCKERHUB_BACKEND_REPO = 'volkandemirors/todo-backend'
        DOCKERHUB_FRONTEND_REPO = 'volkandemirors/todo-frontend'
    }

    stages {

        stage('01 - Checkout') {
            steps {
                checkout scm
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
                echo '========== 03 - GITHUB AUTHENTICATION =========='

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
                                https://api.github.com/user
                        )

                        echo "HTTP status: $HTTP_CODE"

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
                echo '========== 04 - GITHUB REPOSITORY ACCESS =========='

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
                                -o /tmp/github_repo.json \
                                -w "%{http_code}" \
                                -H "Authorization: Bearer $GITHUB_TOKEN" \
                                -H "Accept: application/vnd.github+json" \
                                https://api.github.com/repos/demirorsvolkan/todo
                        )

                        echo "GitHub repository HTTP status: $HTTP_STATUS"

                        if [ "$HTTP_STATUS" != "200" ]; then
                            cat /tmp/github_repo.json
                            exit 1
                        fi

                        echo "GitHub repository access OK."
                    '''
                }
            }
        }

        stage('05 - Find Last Component Tags') {
            steps {
                script {

                    env.BACKEND_TAG = sh(
                        script: '''
                            git tag -l 'backend/v*' \
                                --sort=-version:refname \
                                | head -n 1
                        ''',
                        returnStdout: true
                    ).trim()

                    env.FRONTEND_TAG = sh(
                        script: '''
                            git tag -l 'frontend/v*' \
                                --sort=-version:refname \
                                | head -n 1
                        ''',
                        returnStdout: true
                    ).trim()

                    echo """
========== LAST COMPONENT TAGS ==========
Backend  : ${env.BACKEND_TAG ?: 'YOK'}
Frontend : ${env.FRONTEND_TAG ?: 'YOK'}
"""
                }
            }
        }

        stage('06 - Resolve Reference Commits') {
            steps {
                script {

                    if (env.BACKEND_TAG) {
                        env.BACKEND_BASE_SHA = sh(
                            script: "git rev-list -n 1 '${env.BACKEND_TAG}'",
                            returnStdout: true
                        ).trim()
                    } else {
                        env.BACKEND_BASE_SHA = ''
                    }

                    if (env.FRONTEND_TAG) {
                        env.FRONTEND_BASE_SHA = sh(
                            script: "git rev-list -n 1 '${env.FRONTEND_TAG}'",
                            returnStdout: true
                        ).trim()
                    } else {
                        env.FRONTEND_BASE_SHA = ''
                    }

                    echo """
========== REFERENCE COMMITS ==========
Backend base   : ${env.BACKEND_BASE_SHA ?: 'YOK'}
Frontend base  : ${env.FRONTEND_BASE_SHA ?: 'YOK'}
Current        : ${env.CURRENT_SHA}
"""
                }
            }
        }

        stage('07 - Detect Backend Changes') {
            steps {
                script {

                    if (!env.BACKEND_BASE_SHA) {

                        echo 'Backend için daha önce oluşturulmuş tag yok.'
                        echo 'Backend değişikliği var kabul ediliyor.'

                        env.BACKEND_CHANGED = 'true'

                    } else {

                        def result = sh(
                            script: """
                                git diff --name-only \
                                    '${env.BACKEND_BASE_SHA}' \
                                    '${env.CURRENT_SHA}' \
                                    -- '${env.BACKEND_DIR}'
                            """,
                            returnStdout: true
                        ).trim()

                        echo """
========== BACKEND DIFF ==========
${result ?: 'Değişiklik yok.'}
"""

                        env.BACKEND_CHANGED =
                            result ? 'true' : 'false'
                    }
                }
            }
        }

        stage('08 - Detect Frontend Changes') {
            steps {
                script {

                    if (!env.FRONTEND_BASE_SHA) {

                        echo 'Frontend için daha önce oluşturulmuş tag yok.'
                        echo 'Frontend değişikliği var kabul ediliyor.'

                        env.FRONTEND_CHANGED = 'true'

                    } else {

                        def result = sh(
                            script: """
                                git diff --name-only \
                                    '${env.FRONTEND_BASE_SHA}' \
                                    '${env.CURRENT_SHA}' \
                                    -- '${env.FRONTEND_DIR}'
                            """,
                            returnStdout: true
                        ).trim()

                        echo """
========== FRONTEND DIFF ==========
${result ?: 'Değişiklik yok.'}
"""

                        env.FRONTEND_CHANGED =
                            result ? 'true' : 'false'
                    }
                }
            }
        }

        stage('09 - Change Summary') {
            steps {
                echo """
========== CHANGE SUMMARY ==========

Backend changed  : ${env.BACKEND_CHANGED}
Frontend changed : ${env.FRONTEND_CHANGED}

=====================================
"""
            }
        }

        stage('10 - Stop If Nothing Changed') {
            when {
                expression {
                    env.BACKEND_CHANGED != 'true' &&
                    env.FRONTEND_CHANGED != 'true'
                }
            }

            steps {
                echo '''
==================================================
Backend veya frontend değişikliği bulunamadı.
Docker image oluşturulmayacak.
==================================================
'''
            }
        }




stage('11 - Calculate Next Versions') {
    steps {
        script {

            /*
             * =========================================================
             * Conventional Commit Version Rules
             * =========================================================
             *
             * fix: something
             * fix(api): something
             *                         -> PATCH
             *
             * feat: something
             * feat(api): something
             *                         -> MINOR
             *
             * feat!: something
             * feat(api)!: something
             * fix!: something
             *                         -> MAJOR
             *
             * BREAKING CHANGE: something
             * BREAKING-CHANGE: something
             *                         -> MAJOR
             *
             * Priority:
             *
             * MAJOR > MINOR > PATCH
             *
             * =========================================================
             */


            // =========================================================
            // BACKEND
            // =========================================================

            if (env.BACKEND_CHANGED == 'true') {

                if (env.BACKEND_TAG?.trim()) {

                    def backendRegex =
                        '^backend/v([0-9]+)\\.([0-9]+)\\.([0-9]+)-sha\\.([0-9a-fA-F]+)$'

                    if (!env.BACKEND_TAG.matches(backendRegex)) {
                        error(
                            "Geçersiz backend tag formatı: ${env.BACKEND_TAG}"
                        )
                    }

                    def match = env.BACKEND_TAG =~ backendRegex

                    int major = match[0][1] as int
                    int minor = match[0][2] as int
                    int patch = match[0][3] as int


                    // -------------------------------------------------
                    // Backend commit mesajlarını al
                    // Son backend tag'ından mevcut commit'e kadar
                    // SADECE backend dizinine dokunan commitler.
                    // -------------------------------------------------

                    def backendCommits = sh(
                        script: """
                            git log \
                                --format=%B%x1e \
                                '${env.BACKEND_BASE_SHA}..${env.CURRENT_SHA}' \
                                -- '${env.BACKEND_DIR}'
                        """,
                        returnStdout: true
                    ).trim()


                    echo """
========== BACKEND COMMITS SINCE LAST TAG ==========

${backendCommits ?: 'Commit bulunamadı.'}

=====================================================
"""


                    // -------------------------------------------------
                    // Regex patternleri
                    // String olarak tanımlıyoruz.
                    // Böylece Jenkins Groovy parser problemlerinden
                    // kaçınıyoruz.
                    // -------------------------------------------------

                    def majorCommitPattern =
                        '(?m)^(feat|fix|refactor|perf|chore|docs|style|test|build|ci)(\\([^)]*\\))?!:'

                    def breakingChangePattern =
                        '(?m)^BREAKING[ -]CHANGE[ ]*:'

                    def minorCommitPattern =
                        '(?m)^feat(\\([^)]*\\))?:'

                    def patchCommitPattern =
                        '(?m)^fix(\\([^)]*\\))?:'


                    String backendBump = 'patch'


                    // -------------------------------------------------
                    // MAJOR
                    // -------------------------------------------------

                    if (
                        backendCommits.find(majorCommitPattern) ||
                        backendCommits.find(breakingChangePattern)
                    ) {

                        backendBump = 'major'


                    // -------------------------------------------------
                    // MINOR
                    // -------------------------------------------------

                    } else if (
                        backendCommits.find(minorCommitPattern)
                    ) {

                        backendBump = 'minor'


                    // -------------------------------------------------
                    // PATCH
                    // -------------------------------------------------

                    } else if (
                        backendCommits.find(patchCommitPattern)
                    ) {

                        backendBump = 'patch'
                    }


                    echo "Backend version bump: ${backendBump.toUpperCase()}"


                    // -------------------------------------------------
                    // Version artır
                    // -------------------------------------------------

                    switch (backendBump) {

                        case 'major':

                            major++
                            minor = 0
                            patch = 0

                            break


                        case 'minor':

                            minor++
                            patch = 0

                            break


                        case 'patch':

                        default:

                            patch++

                            break
                    }


                    env.BACKEND_VERSION =
                        "v${major}.${minor}.${patch}"

                } else {

                    /*
                     * Daha önce backend tag'ı yoksa
                     * başlangıç versiyonu.
                     */
                    env.BACKEND_VERSION = 'v1.0.0'
                }


                // -----------------------------------------------------
                // Backend Docker / Git tag değerleri
                // -----------------------------------------------------

                env.BACKEND_FULL_TAG =
                    "backend/${env.BACKEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"

                env.BACKEND_DOCKER_VERSION_TAG =
                    env.BACKEND_VERSION

                env.BACKEND_DOCKER_SHA_TAG =
                    "sha-${env.CURRENT_SHORT_SHA}"
            }


            // =========================================================
            // FRONTEND
            // =========================================================

            if (env.FRONTEND_CHANGED == 'true') {

                if (env.FRONTEND_TAG?.trim()) {

                    def frontendRegex =
                        '^frontend/v([0-9]+)\\.([0-9]+)\\.([0-9]+)-sha\\.([0-9a-fA-F]+)$'

                    if (!env.FRONTEND_TAG.matches(frontendRegex)) {
                        error(
                            "Geçersiz frontend tag formatı: ${env.FRONTEND_TAG}"
                        )
                    }

                    def match = env.FRONTEND_TAG =~ frontendRegex

                    int major = match[0][1] as int
                    int minor = match[0][2] as int
                    int patch = match[0][3] as int


                    // -------------------------------------------------
                    // Frontend commit mesajlarını al
                    // Son frontend tag'ından mevcut commit'e kadar
                    // SADECE frontend dizinine dokunan commitler.
                    // -------------------------------------------------

                    def frontendCommits = sh(
                        script: """
                            git log \
                                --format=%B%x1e \
                                '${env.FRONTEND_BASE_SHA}..${env.CURRENT_SHA}' \
                                -- '${env.FRONTEND_DIR}'
                        """,
                        returnStdout: true
                    ).trim()


                    echo """
========== FRONTEND COMMITS SINCE LAST TAG ==========

${frontendCommits ?: 'Commit bulunamadı.'}

======================================================
"""


                    // -------------------------------------------------
                    // Regex patternleri
                    // -------------------------------------------------

                    def majorCommitPattern =
                        '(?m)^(feat|fix|refactor|perf|chore|docs|style|test|build|ci)(\\([^)]*\\))?!:'

                    def breakingChangePattern =
                        '(?m)^BREAKING[ -]CHANGE[ ]*:'

                    def minorCommitPattern =
                        '(?m)^feat(\\([^)]*\\))?:'

                    def patchCommitPattern =
                        '(?m)^fix(\\([^)]*\\))?:'


                    String frontendBump = 'patch'


                    // -------------------------------------------------
                    // MAJOR
                    // -------------------------------------------------

                    if (
                        frontendCommits.find(majorCommitPattern) ||
                        frontendCommits.find(breakingChangePattern)
                    ) {

                        frontendBump = 'major'


                    // -------------------------------------------------
                    // MINOR
                    // -------------------------------------------------

                    } else if (
                        frontendCommits.find(minorCommitPattern)
                    ) {

                        frontendBump = 'minor'


                    // -------------------------------------------------
                    // PATCH
                    // -------------------------------------------------

                    } else if (
                        frontendCommits.find(patchCommitPattern)
                    ) {

                        frontendBump = 'patch'
                    }


                    echo "Frontend version bump: ${frontendBump.toUpperCase()}"


                    // -------------------------------------------------
                    // Version artır
                    // -------------------------------------------------

                    switch (frontendBump) {

                        case 'major':

                            major++
                            minor = 0
                            patch = 0

                            break


                        case 'minor':

                            minor++
                            patch = 0

                            break


                        case 'patch':

                        default:

                            patch++

                            break
                    }


                    env.FRONTEND_VERSION =
                        "v${major}.${minor}.${patch}"

                } else {

                    /*
                     * Daha önce frontend tag'ı yoksa
                     * başlangıç versiyonu.
                     */
                    env.FRONTEND_VERSION = 'v1.0.0'
                }


                // -----------------------------------------------------
                // Frontend Docker / Git tag değerleri
                // -----------------------------------------------------

                env.FRONTEND_FULL_TAG =
                    "frontend/${env.FRONTEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"

                env.FRONTEND_DOCKER_VERSION_TAG =
                    env.FRONTEND_VERSION

                env.FRONTEND_DOCKER_SHA_TAG =
                    "sha-${env.CURRENT_SHORT_SHA}"
            }


            // =========================================================
            // RESULT
            // =========================================================

            echo """
========== NEXT VERSIONS ==========

Backend:
  Version : ${env.BACKEND_VERSION ?: 'BUILD YOK'}
  Git Tag : ${env.BACKEND_FULL_TAG ?: 'BUILD YOK'}

Frontend:
  Version : ${env.FRONTEND_VERSION ?: 'BUILD YOK'}
  Git Tag : ${env.FRONTEND_FULL_TAG ?: 'BUILD YOK'}

====================================
"""
        }
    }
}




        stage('12 - Docker Image Build') {
            steps {
                script {

                    if (env.BACKEND_CHANGED == 'true') {

                        sh """
                            docker build \
                                -t '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_VERSION_TAG}' \
                                -t '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_SHA_TAG}' \
                                '${BACKEND_DIR}'
                        """
                    }

                    if (env.FRONTEND_CHANGED == 'true') {

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

        stage('13 - Docker Hub Push') {
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

                        if (env.BACKEND_CHANGED == 'true') {

                            sh """
                                docker push \
                                    '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_VERSION_TAG}'

                                docker push \
                                    '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_SHA_TAG}'
                            """
                        }

                        if (env.FRONTEND_CHANGED == 'true') {

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

        stage('14 - Create GitHub Tags') {
            steps {
                script {

                    withCredentials([
                        string(
                            credentialsId: 'github-token',
                            variable: 'GITHUB_TOKEN'
                        )
                    ]) {

                        if (env.BACKEND_CHANGED == 'true') {

                            sh """
                                curl \
                                    -sS \
                                    -X POST \
                                    -H "Authorization: Bearer \$GITHUB_TOKEN" \
                                    -H "Accept: application/vnd.github+json" \
                                    https://api.github.com/repos/${GITHUB_REPO}/git/refs \
                                    -d '{
                                        "ref":"refs/tags/${env.BACKEND_FULL_TAG}",
                                        "sha":"${env.CURRENT_SHA}"
                                    }'
                            """
                        }

                        if (env.FRONTEND_CHANGED == 'true') {

                            sh """
                                curl \
                                    -sS \
                                    -X POST \
                                    -H "Authorization: Bearer \$GITHUB_TOKEN" \
                                    -H "Accept: application/vnd.github+json" \
                                    https://api.github.com/repos/${GITHUB_REPO}/git/refs \
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

Backend changed:
${env.BACKEND_CHANGED ?: 'N/A'}

Frontend changed:
${env.FRONTEND_CHANGED ?: 'N/A'}

Backend tag:
${env.BACKEND_FULL_TAG ?: 'N/A'}

Frontend tag:
${env.FRONTEND_FULL_TAG ?: 'N/A'}

========================================
"""
        }
    }
}
