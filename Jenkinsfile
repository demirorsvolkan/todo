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
             * CONVENTIONAL COMMIT VERSIONING
             * =========================================================
             *
             * MAJOR
             *   feat!:
             *   fix!:
             *   refactor!:
             *   perf!:
             *   chore!:
             *   docs!:
             *   test!:
             *   ci!:
             *   build!:
             *   style!:
             *   BREAKING CHANGE:
             *   BREAKING-CHANGE:
             *
             * MINOR
             *   feat:
             *   feat(scope):
             *
             * PATCH
             *   fix:
             *   fix(scope):
             *   perf:
             *   perf(scope):
             *
             * NO RELEASE
             *   chore:
             *   docs:
             *   refactor:
             *   test:
             *   ci:
             *   build:
             *   style:
             *   unknown / invalid commit
             *
             * Priority:
             *
             *   MAJOR > MINOR > PATCH > NONE
             *
             * IMPORTANT:
             *
             * Only commits after the last component tag are examined.
             *
             * Backend:
             *   BACKEND_BASE_SHA..CURRENT_SHA -- backend
             *
             * Frontend:
             *   FRONTEND_BASE_SHA..CURRENT_SHA -- frontend
             *
             * --first-parent kullanılmaz.
             * Böylece merge commitlerinin arkasındaki gerçek commitler
             * de version hesabına dahil edilir.
             *
             * =========================================================
             */


            // =========================================================
            // BACKEND
            // =========================================================

            if (env.BACKEND_CHANGED == 'true') {

                env.BACKEND_RELEASE = 'false'

                if (env.BACKEND_TAG?.trim()) {

                    /*
                     * -------------------------------------------------
                     * Parse backend version
                     * -------------------------------------------------
                     *
                     * backend/v1.4.7-sha.abc1234
                     *              ↓
                     * v1.4.7
                     */

                    def backendTagVersion =
                        env.BACKEND_TAG
                            .replaceFirst(/^backend\//, '')
                            .replaceFirst(/-sha\..*$/, '')

                    if (!backendTagVersion.startsWith('v')) {
                        error(
                            "Geçersiz backend tag formatı: ${env.BACKEND_TAG}"
                        )
                    }

                    def backendVersionParts =
                        backendTagVersion
                            .substring(1)
                            .split('\\.')

                    if (backendVersionParts.size() != 3) {
                        error(
                            "Geçersiz backend version formatı: ${env.BACKEND_TAG}"
                        )
                    }

                    int major =
                        backendVersionParts[0] as int

                    int minor =
                        backendVersionParts[1] as int

                    int patch =
                        backendVersionParts[2] as int


                    // -------------------------------------------------
                    // Commitleri al
                    //
                    // Format:
                    //
                    // HASH<TAB>SUBJECT
                    //
                    // Body ayrıca ayrı bir komutla kontrol edilecek.
                    // -------------------------------------------------

                    def backendCommitData = sh(
                        script: """
                            git log \
                                --format='%H%x09%s' \
                                '${env.BACKEND_BASE_SHA}..${env.CURRENT_SHA}' \
                                -- '${env.BACKEND_DIR}'
                        """,
                        returnStdout: true
                    ).trim()


                    echo """
========== BACKEND COMMITS SINCE LAST TAG ==========

${backendCommitData ?: 'Commit bulunamadı.'}

=====================================================
"""


                    String backendBump = 'none'


                    if (backendCommitData) {

                        /*
                         * -------------------------------------------------
                         * Commitleri tek tek değerlendir
                         * -------------------------------------------------
                         */

                        backendCommitData
                            .split('\n')
                            .each { line ->

                                if (!line?.trim()) {
                                    return
                                }

                                def separatorIndex =
                                    line.indexOf('\t')

                                if (separatorIndex < 0) {
                                    return
                                }

                                def commitSha =
                                    line.substring(
                                        0,
                                        separatorIndex
                                    ).trim()

                                def commitSubject =
                                    line.substring(
                                        separatorIndex + 1
                                    ).trim()


                                /*
                                 * -------------------------------------------------
                                 * Commit body
                                 * -------------------------------------------------
                                 *
                                 * BREAKING CHANGE body içerisinde bulunabilir.
                                 */

                                def commitBody = sh(
                                    script: """
                                        git show -s \
                                            --format='%b' \
                                            '${commitSha}'
                                    """,
                                    returnStdout: true
                                ).trim()


                                String commitBump = 'none'


                                /*
                                 * =================================================
                                 * MAJOR
                                 * =================================================
                                 */

                                if (
                                    commitSubject ==~ /^(feat|fix|refactor|perf|chore|docs|test|ci|build|style)(\\([^)]*\\))?!:.*$/
                                ) {

                                    commitBump = 'major'

                                } else if (
                                    commitBody.contains('BREAKING CHANGE:') ||
                                    commitBody.contains('BREAKING-CHANGE:')
                                ) {

                                    commitBump = 'major'


                                /*
                                 * =================================================
                                 * MINOR
                                 * =================================================
                                 */

                                } else if (
                                    commitSubject ==~ /^feat(\\([^)]*\\))?:.*$/
                                ) {

                                    commitBump = 'minor'


                                /*
                                 * =================================================
                                 * PATCH
                                 * =================================================
                                 */

                                } else if (
                                    commitSubject ==~ /^fix(\\([^)]*\\))?:.*$/ ||
                                    commitSubject ==~ /^perf(\\([^)]*\\))?:.*$/
                                ) {

                                    commitBump = 'patch'
                                }


                                echo """
Backend commit:
  SHA     : ${commitSha}
  Subject : ${commitSubject}
  Bump    : ${commitBump.toUpperCase()}
"""


                                /*
                                 * -------------------------------------------------
                                 * MAXIMUM BUMP
                                 * -------------------------------------------------
                                 *
                                 * MAJOR > MINOR > PATCH > NONE
                                 * -------------------------------------------------
                                 */

                                if (commitBump == 'major') {

                                    backendBump = 'major'

                                } else if (
                                    commitBump == 'minor' &&
                                    backendBump != 'major'
                                ) {

                                    backendBump = 'minor'

                                } else if (
                                    commitBump == 'patch' &&
                                    backendBump == 'none'
                                ) {

                                    backendBump = 'patch'
                                }
                            }
                    }


                    echo """
========== BACKEND VERSION BUMP ==========
Bump: ${backendBump.toUpperCase()}
===========================================
"""


                    /*
                     * -------------------------------------------------
                     * NO RELEASE
                     * -------------------------------------------------
                     */

                    if (backendBump == 'none') {

                        env.BACKEND_RELEASE = 'false'

                        echo """
========== BACKEND RELEASE ==========
NO BUILD / NO RELEASE

Backend path değişmiş olsa bile
release gerektiren Conventional Commit bulunamadı.

=====================================
"""

                    } else {

                        env.BACKEND_RELEASE = 'true'


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
                                patch++
                                break
                        }


                        env.BACKEND_VERSION =
                            "v${major}.${minor}.${patch}"


                        env.BACKEND_FULL_TAG =
                            "backend/${env.BACKEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"

                        env.BACKEND_DOCKER_VERSION_TAG =
                            env.BACKEND_VERSION

                        env.BACKEND_DOCKER_SHA_TAG =
                            "sha-${env.CURRENT_SHORT_SHA}"
                    }

                } else {

                    /*
                     * -------------------------------------------------
                     * İlk backend release
                     * -------------------------------------------------
                     *
                     * Burada backend değişikliği bulunduğu için
                     * ilk release v1.0.0 olarak oluşturulur.
                     */

                    env.BACKEND_RELEASE = 'true'

                    env.BACKEND_VERSION = 'v1.0.0'

                    env.BACKEND_FULL_TAG =
                        "backend/${env.BACKEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"

                    env.BACKEND_DOCKER_VERSION_TAG =
                        env.BACKEND_VERSION

                    env.BACKEND_DOCKER_SHA_TAG =
                        "sha-${env.CURRENT_SHORT_SHA}"
                }
            }


            // =========================================================
            // FRONTEND
            // =========================================================

            if (env.FRONTEND_CHANGED == 'true') {

                env.FRONTEND_RELEASE = 'false'

                if (env.FRONTEND_TAG?.trim()) {

                    /*
                     * -------------------------------------------------
                     * Parse frontend version
                     * -------------------------------------------------
                     */

                    def frontendTagVersion =
                        env.FRONTEND_TAG
                            .replaceFirst(/^frontend\//, '')
                            .replaceFirst(/-sha\..*$/, '')

                    if (!frontendTagVersion.startsWith('v')) {
                        error(
                            "Geçersiz frontend tag formatı: ${env.FRONTEND_TAG}"
                        )
                    }

                    def frontendVersionParts =
                        frontendTagVersion
                            .substring(1)
                            .split('\\.')

                    if (frontendVersionParts.size() != 3) {
                        error(
                            "Geçersiz frontend version formatı: ${env.FRONTEND_TAG}"
                        )
                    }

                    int major =
                        frontendVersionParts[0] as int

                    int minor =
                        frontendVersionParts[1] as int

                    int patch =
                        frontendVersionParts[2] as int


                    // -------------------------------------------------
                    // Commitleri al
                    // -------------------------------------------------

                    def frontendCommitData = sh(
                        script: """
                            git log \
                                --format='%H%x09%s' \
                                '${env.FRONTEND_BASE_SHA}..${env.CURRENT_SHA}' \
                                -- '${env.FRONTEND_DIR}'
                        """,
                        returnStdout: true
                    ).trim()


                    echo """
========== FRONTEND COMMITS SINCE LAST TAG ==========

${frontendCommitData ?: 'Commit bulunamadı.'}

======================================================
"""


                    String frontendBump = 'none'


                    if (frontendCommitData) {

                        frontendCommitData
                            .split('\n')
                            .each { line ->

                                if (!line?.trim()) {
                                    return
                                }

                                def separatorIndex =
                                    line.indexOf('\t')

                                if (separatorIndex < 0) {
                                    return
                                }

                                def commitSha =
                                    line.substring(
                                        0,
                                        separatorIndex
                                    ).trim()

                                def commitSubject =
                                    line.substring(
                                        separatorIndex + 1
                                    ).trim()


                                /*
                                 * -------------------------------------------------
                                 * Commit body
                                 * -------------------------------------------------
                                 */

                                def commitBody = sh(
                                    script: """
                                        git show -s \
                                            --format='%b' \
                                            '${commitSha}'
                                    """,
                                    returnStdout: true
                                ).trim()


                                String commitBump = 'none'


                                /*
                                 * =================================================
                                 * MAJOR
                                 * =================================================
                                 */

                                if (
                                    commitSubject ==~ /^(feat|fix|refactor|perf|chore|docs|test|ci|build|style)(\\([^)]*\\))?!:.*$/
                                ) {

                                    commitBump = 'major'

                                } else if (
                                    commitBody.contains('BREAKING CHANGE:') ||
                                    commitBody.contains('BREAKING-CHANGE:')
                                ) {

                                    commitBump = 'major'


                                /*
                                 * =================================================
                                 * MINOR
                                 * =================================================
                                 */

                                } else if (
                                    commitSubject ==~ /^feat(\\([^)]*\\))?:.*$/
                                ) {

                                    commitBump = 'minor'


                                /*
                                 * =================================================
                                 * PATCH
                                 * =================================================
                                 */

                                } else if (
                                    commitSubject ==~ /^fix(\\([^)]*\\))?:.*$/ ||
                                    commitSubject ==~ /^perf(\\([^)]*\\))?:.*$/
                                ) {

                                    commitBump = 'patch'
                                }


                                echo """
Frontend commit:
  SHA     : ${commitSha}
  Subject : ${commitSubject}
  Bump    : ${commitBump.toUpperCase()}
"""


                                /*
                                 * -------------------------------------------------
                                 * MAXIMUM BUMP
                                 * -------------------------------------------------
                                 */

                                if (commitBump == 'major') {

                                    frontendBump = 'major'

                                } else if (
                                    commitBump == 'minor' &&
                                    frontendBump != 'major'
                                ) {

                                    frontendBump = 'minor'

                                } else if (
                                    commitBump == 'patch' &&
                                    frontendBump == 'none'
                                ) {

                                    frontendBump = 'patch'
                                }
                            }
                    }


                    echo """
========== FRONTEND VERSION BUMP ==========
Bump: ${frontendBump.toUpperCase()}
============================================
"""


                    /*
                     * -------------------------------------------------
                     * NO RELEASE
                     * -------------------------------------------------
                     */

                    if (frontendBump == 'none') {

                        env.FRONTEND_RELEASE = 'false'

                        echo """
========== FRONTEND RELEASE ==========
NO BUILD / NO RELEASE

Frontend path değişmiş olsa bile
release gerektiren Conventional Commit bulunamadı.

======================================
"""

                    } else {

                        env.FRONTEND_RELEASE = 'true'


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
                                patch++
                                break
                        }


                        env.FRONTEND_VERSION =
                            "v${major}.${minor}.${patch}"


                        env.FRONTEND_FULL_TAG =
                            "frontend/${env.FRONTEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"

                        env.FRONTEND_DOCKER_VERSION_TAG =
                            env.FRONTEND_VERSION

                        env.FRONTEND_DOCKER_SHA_TAG =
                            "sha-${env.CURRENT_SHORT_SHA}"
                    }

                } else {

                    /*
                     * -------------------------------------------------
                     * İlk frontend release
                     * -------------------------------------------------
                     */

                    env.FRONTEND_RELEASE = 'true'

                    env.FRONTEND_VERSION = 'v1.0.0'

                    env.FRONTEND_FULL_TAG =
                        "frontend/${env.FRONTEND_VERSION}-sha.${env.CURRENT_SHORT_SHA}"

                    env.FRONTEND_DOCKER_VERSION_TAG =
                        env.FRONTEND_VERSION

                    env.FRONTEND_DOCKER_SHA_TAG =
                        "sha-${env.CURRENT_SHORT_SHA}"
                }
            }


            // =========================================================
            // RESULT
            // =========================================================

            echo """
========== NEXT VERSIONS ==========

Backend:
  Changed : ${env.BACKEND_CHANGED ?: 'false'}
  Release : ${env.BACKEND_RELEASE ?: 'false'}
  Version : ${env.BACKEND_VERSION ?: 'NO BUILD'}
  Git Tag : ${env.BACKEND_FULL_TAG ?: 'NO BUILD'}

Frontend:
  Changed : ${env.FRONTEND_CHANGED ?: 'false'}
  Release : ${env.FRONTEND_RELEASE ?: 'false'}
  Version : ${env.FRONTEND_VERSION ?: 'NO BUILD'}
  Git Tag : ${env.FRONTEND_FULL_TAG ?: 'NO BUILD'}

====================================
"""
        }
    }
}


stage('12 - Docker Image Build') {
    steps {
        script {

            if (env.BACKEND_RELEASE == 'true') {

                sh """
                    docker build \
                        -t '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_VERSION_TAG}' \
                        -t '${DOCKERHUB_BACKEND_REPO}:${env.BACKEND_DOCKER_SHA_TAG}' \
                        '${BACKEND_DIR}'
                """
            }

            if (env.FRONTEND_RELEASE == 'true') {

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

stage('14 - Create GitHub Tags') {
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

                if (env.FRONTEND_RELEASE == 'true') {

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

Backend release:
${env.BACKEND_RELEASE ?: 'N/A'}

Frontend release:
${env.FRONTEND_RELEASE ?: 'N/A'}

Backend tag:
${env.BACKEND_FULL_TAG ?: 'N/A'}

Frontend tag:
${env.FRONTEND_FULL_TAG ?: 'N/A'}

========================================
"""
    }
}
}
