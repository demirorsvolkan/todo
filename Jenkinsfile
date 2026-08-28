pipeline {

    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
        skipDefaultCheckout(true)
    }

    environment {
        GITHUB_REPO = 'demirorsvolkan/todo'

        DOCKER_USER = 'volkandemirors'

        BACKEND_REPO  = 'volkandemirors/todo-backend'
        FRONTEND_REPO = 'volkandemirors/todo-frontend'

        GITHUB_API = 'https://api.github.com'
    }

    stages {

        // ============================================================
        // 01 - CHECKOUT
        // ============================================================

        stage('01 - Checkout') {
            steps {
                echo '========== 01 - CHECKOUT =========='

                checkout scm

                sh '''
                    set -eu

                    echo "Commit:"
                    git rev-parse HEAD

                    echo
                    echo "Commit message:"
                    git log -1 --pretty=%B

                    echo
                    echo "Fetching all branches and tags..."

                    git fetch --force origin '+refs/heads/*:refs/remotes/origin/*'
                    git fetch --tags --force origin
                '''
            }
        }


        // ============================================================
        // 02 - DETERMINE CURRENT COMMIT
        // ============================================================

        stage('02 - Current Commit') {
            steps {
                script {

                    env.CURRENT_SHA = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    env.SHORT_SHA = sh(
                        script: 'git rev-parse --short=7 HEAD',
                        returnStdout: true
                    ).trim()

                    echo '========== CURRENT COMMIT =========='
                    echo "Current SHA : ${env.CURRENT_SHA}"
                    echo "Short SHA   : ${env.SHORT_SHA}"
                }
            }
        }


        // ============================================================
        // 03 - GITHUB AUTHENTICATION
        // ============================================================

        stage('03 - GitHub Authentication') {
            steps {

                echo '========== 03 - GITHUB AUTHENTICATION =========='

                withCredentials([
                    string(
                        credentialsId: 'GITHUB_TOKEN',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {

                    sh '''
                        set -eu
                        set +x

                        STATUS=$(curl -sS \
                            -o /tmp/github-user.json \
                            -w "%{http_code}" \
                            -H "Authorization: Bearer ${GITHUB_TOKEN}" \
                            -H "Accept: application/vnd.github+json" \
                            "${GITHUB_API}/user")

                        echo "GitHub HTTP status: ${STATUS}"

                        test "${STATUS}" = "200"

                        echo "GitHub authentication OK."
                    '''
                }
            }
        }


        // ============================================================
        // 04 - FIND LAST BACKEND RELEASE
        // ============================================================

        stage('04 - Find Last Backend Release') {
            steps {

                echo '========== 04 - LAST BACKEND RELEASE =========='

                withCredentials([
                    string(
                        credentialsId: 'GITHUB_TOKEN',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {

                    script {

                        def result = sh(
                            script: '''
                                set -eu
                                set +x

                                curl -fsSL \
                                    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
                                    -H "Accept: application/vnd.github+json" \
                                    "${GITHUB_API}/repos/${GITHUB_REPO}/git/matching-refs/tags/backend/" \
                                    > /tmp/backend-tags.json

                                python3 - <<'PY'
import json
import re

with open("/tmp/backend-tags.json") as f:
    data = json.load(f)

pattern = re.compile(
    r'^refs/tags/backend/v([0-9]+)\\.([0-9]+)\\.([0-9]+)-sha\\.([0-9a-fA-F]+)$'
)

versions = []

for item in data:
    ref = item.get("ref", "")
    m = pattern.match(ref)

    if m:
        major = int(m.group(1))
        minor = int(m.group(2))
        patch = int(m.group(3))
        sha = m.group(4)

        versions.append(
            (major, minor, patch, sha, ref)
        )

if not versions:
    print("NONE")
else:
    versions.sort(
        key=lambda x: (x[0], x[1], x[2]),
        reverse=True
    )

    major, minor, patch, sha, ref = versions[0]

    print(f"{major}.{minor}.{patch}|{sha}|{ref}")
PY
                            ''',
                            returnStdout: true
                        ).trim()

                        env.BACKEND_LAST_RELEASE = result

                        echo "Backend last release: ${result}"
                    }
                }
            }
        }


        // ============================================================
        // 05 - FIND LAST FRONTEND RELEASE
        // ============================================================

        stage('05 - Find Last Frontend Release') {
            steps {

                echo '========== 05 - LAST FRONTEND RELEASE =========='

                withCredentials([
                    string(
                        credentialsId: 'GITHUB_TOKEN',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {

                    script {

                        def result = sh(
                            script: '''
                                set -eu
                                set +x

                                curl -fsSL \
                                    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
                                    -H "Accept: application/vnd.github+json" \
                                    "${GITHUB_API}/repos/${GITHUB_REPO}/git/matching-refs/tags/frontend/" \
                                    > /tmp/frontend-tags.json

                                python3 - <<'PY'
import json
import re

with open("/tmp/frontend-tags.json") as f:
    data = json.load(f)

pattern = re.compile(
    r'^refs/tags/frontend/v([0-9]+)\\.([0-9]+)\\.([0-9]+)-sha\\.([0-9a-fA-F]+)$'
)

versions = []

for item in data:
    ref = item.get("ref", "")
    m = pattern.match(ref)

    if m:
        major = int(m.group(1))
        minor = int(m.group(2))
        patch = int(m.group(3))
        sha = m.group(4)

        versions.append(
            (major, minor, patch, sha, ref)
        )

if not versions:
    print("NONE")
else:
    versions.sort(
        key=lambda x: (x[0], x[1], x[2]),
        reverse=True
    )

    major, minor, patch, sha, ref = versions[0]

    print(f"{major}.{minor}.{patch}|{sha}|{ref}")
PY
                            ''',
                            returnStdout: true
                        ).trim()

                        env.FRONTEND_LAST_RELEASE = result

                        echo "Frontend last release: ${result}"
                    }
                }
            }
        }


        // ============================================================
        // 06 - RESOLVE RELEASE COMMITS
        // ============================================================

        stage('06 - Resolve Release Commits') {
            steps {

                echo '========== 06 - RESOLVE RELEASE COMMITS =========='

                script {

                    def backend = env.BACKEND_LAST_RELEASE
                    def frontend = env.FRONTEND_LAST_RELEASE

                    if (backend == 'NONE') {
                        env.BACKEND_BASE_SHA = ''
                        echo 'No previous backend release.'
                    } else {

                        def backendSha = backend.split('\\|')[1]

                        env.BACKEND_BASE_SHA = sh(
                            script: """
                                set -eu

                                git rev-parse \
                                    --verify \
                                    refs/tags/backend/v${backend.split('\\|')[0]}-sha.${backendSha}^{commit}
                            """,
                            returnStdout: true
                        ).trim()

                        echo "Backend release commit: ${env.BACKEND_BASE_SHA}"
                    }

                    if (frontend == 'NONE') {
                        env.FRONTEND_BASE_SHA = ''
                        echo 'No previous frontend release.'
                    } else {

                        def frontendSha = frontend.split('\\|')[1]

                        env.FRONTEND_BASE_SHA = sh(
                            script: """
                                set -eu

                                git rev-parse \
                                    --verify \
                                    refs/tags/frontend/v${frontend.split('\\|')[0]}-sha.${frontendSha}^{commit}
                            """,
                            returnStdout: true
                        ).trim()

                        echo "Frontend release commit: ${env.FRONTEND_BASE_SHA}"
                    }
                }
            }
        }


        // ============================================================
        // 07 - DETECT BACKEND CHANGES
        // ============================================================

        stage('07 - Detect Backend Changes') {
            steps {

                echo '========== 07 - BACKEND CHANGE DETECTION =========='

                script {

                    if (!env.BACKEND_BASE_SHA?.trim()) {

                        echo 'No previous backend release.'
                        echo 'Backend will be treated as changed.'

                        env.BACKEND_CHANGED = 'true'

                    } else {

                        def changed = sh(
                            script: """
                                set -eu

                                git diff --name-only \
                                    ${env.BACKEND_BASE_SHA} \
                                    ${env.CURRENT_SHA} \
                                    -- backend/
                            """,
                            returnStdout: true
                        ).trim()

                        if (changed) {

                            env.BACKEND_CHANGED = 'true'

                            echo 'Backend changed: YES'
                            echo
                            echo changed

                        } else {

                            env.BACKEND_CHANGED = 'false'

                            echo 'Backend changed: NO'
                        }
                    }
                }
            }
        }


        // ============================================================
        // 08 - DETECT FRONTEND CHANGES
        // ============================================================

        stage('08 - Detect Frontend Changes') {
            steps {

                echo '========== 08 - FRONTEND CHANGE DETECTION =========='

                script {

                    if (!env.FRONTEND_BASE_SHA?.trim()) {

                        echo 'No previous frontend release.'
                        echo 'Frontend will be treated as changed.'

                        env.FRONTEND_CHANGED = 'true'

                    } else {

                        def changed = sh(
                            script: """
                                set -eu

                                git diff --name-only \
                                    ${env.FRONTEND_BASE_SHA} \
                                    ${env.CURRENT_SHA} \
                                    -- frontend/
                            """,
                            returnStdout: true
                        ).trim()

                        if (changed) {

                            env.FRONTEND_CHANGED = 'true'

                            echo 'Frontend changed: YES'
                            echo
                            echo changed

                        } else {

                            env.FRONTEND_CHANGED = 'false'

                            echo 'Frontend changed: NO'
                        }
                    }
                }
            }
        }


        // ============================================================
        // 09 - CALCULATE VERSIONS
        // ============================================================

        stage('09 - Calculate Versions') {
            steps {

                echo '========== 09 - CALCULATE VERSIONS =========='

                script {

                    // ---------------- BACKEND ----------------

                    if (env.BACKEND_CHANGED == 'true') {

                        if (env.BACKEND_LAST_RELEASE == 'NONE') {

                            env.BACKEND_VERSION = 'v1.0.0'

                        } else {

                            def parts =
                                env.BACKEND_LAST_RELEASE.split('\\|')[0].split('\\.')

                            int major = parts[0] as int
                            int minor = parts[1] as int
                            int patch = parts[2] as int

                            patch++

                            env.BACKEND_VERSION =
                                "v${major}.${minor}.${patch}"
                        }

                        env.BACKEND_GITHUB_TAG =
                            "backend/${env.BACKEND_VERSION}-sha.${env.SHORT_SHA}"

                        env.BACKEND_DOCKER_VERSION_TAG =
                            env.BACKEND_VERSION

                        env.BACKEND_DOCKER_SHA_TAG =
                            env.SHORT_SHA
                    }


                    // ---------------- FRONTEND ----------------

                    if (env.FRONTEND_CHANGED == 'true') {

                        if (env.FRONTEND_LAST_RELEASE == 'NONE') {

                            env.FRONTEND_VERSION = 'v1.0.0'

                        } else {

                            def parts =
                                env.FRONTEND_LAST_RELEASE.split('\\|')[0].split('\\.')

                            int major = parts[0] as int
                            int minor = parts[1] as int
                            int patch = parts[2] as int

                            patch++

                            env.FRONTEND_VERSION =
                                "v${major}.${minor}.${patch}"
                        }

                        env.FRONTEND_GITHUB_TAG =
                            "frontend/${env.FRONTEND_VERSION}-sha.${env.SHORT_SHA}"

                        env.FRONTEND_DOCKER_VERSION_TAG =
                            env.FRONTEND_VERSION

                        env.FRONTEND_DOCKER_SHA_TAG =
                            env.SHORT_SHA
                    }


                    echo '----------------------------------------'
                    echo "Current commit: ${env.CURRENT_SHA}"
                    echo "Short SHA     : ${env.SHORT_SHA}"
                    echo '----------------------------------------'

                    echo "Backend changed : ${env.BACKEND_CHANGED}"
                    echo "Frontend changed: ${env.FRONTEND_CHANGED}"

                    if (env.BACKEND_CHANGED == 'true') {
                        echo
                        echo "Backend version : ${env.BACKEND_VERSION}"
                        echo "Backend Git tag : ${env.BACKEND_GITHUB_TAG}"
                        echo "Backend Docker  : ${env.BACKEND_REPO}:${env.BACKEND_VERSION}"
                        echo "Backend Docker  : ${env.BACKEND_REPO}:${env.SHORT_SHA}"
                    }

                    if (env.FRONTEND_CHANGED == 'true') {
                        echo
                        echo "Frontend version : ${env.FRONTEND_VERSION}"
                        echo "Frontend Git tag : ${env.FRONTEND_GITHUB_TAG}"
                        echo "Frontend Docker  : ${env.FRONTEND_REPO}:${env.FRONTEND_VERSION}"
                        echo "Frontend Docker  : ${env.FRONTEND_REPO}:${env.SHORT_SHA}"
                    }
                }
            }
        }


        // ============================================================
        // 10 - BUILD BACKEND
        // ============================================================

        stage('10 - Build Backend') {
            when {
                expression {
                    env.BACKEND_CHANGED == 'true'
                }
            }

            steps {

                echo '========== 10 - BUILD BACKEND =========='

                sh '''
                    set -eu

                    test -d backend
                    test -f backend/Dockerfile

                    docker build \
                        -t "${BACKEND_REPO}:${BACKEND_VERSION}" \
                        -t "${BACKEND_REPO}:${SHORT_SHA}" \
                        ./backend

                    docker image inspect \
                        "${BACKEND_REPO}:${BACKEND_VERSION}"

                    docker image inspect \
                        "${BACKEND_REPO}:${SHORT_SHA}"

                    echo "Backend build OK."
                '''
            }
        }


        // ============================================================
        // 11 - BUILD FRONTEND
        // ============================================================

        stage('11 - Build Frontend') {
            when {
                expression {
                    env.FRONTEND_CHANGED == 'true'
                }
            }

            steps {

                echo '========== 11 - BUILD FRONTEND =========='

                sh '''
                    set -eu

                    test -d frontend
                    test -f frontend/Dockerfile

                    docker build \
                        -t "${FRONTEND_REPO}:${FRONTEND_VERSION}" \
                        -t "${FRONTEND_REPO}:${SHORT_SHA}" \
                        ./frontend

                    docker image inspect \
                        "${FRONTEND_REPO}:${FRONTEND_VERSION}"

                    docker image inspect \
                        "${FRONTEND_REPO}:${SHORT_SHA}"

                    echo "Frontend build OK."
                '''
            }
        }


        // ============================================================
        // 12 - DOCKER HUB CONFLICT CHECK
        // ============================================================

        stage('12 - Docker Hub Conflict Check') {
            when {
                anyOf {
                    expression { env.BACKEND_CHANGED == 'true' }
                    expression { env.FRONTEND_CHANGED == 'true' }
                }
            }

            steps {

                echo '========== 12 - DOCKER HUB CONFLICT CHECK =========='

                withCredentials([
                    string(
                        credentialsId: 'DOCKER_PASSWORD',
                        variable: 'DOCKER_PASSWORD'
                    )
                ]) {

                    sh '''
                        set -eu
                        set +x

                        echo "${DOCKER_PASSWORD}" | docker login \
                            -u "${DOCKER_USER}" \
                            --password-stdin

                        check_tag() {

                            REPO="$1"
                            TAG="$2"

                            echo
                            echo "Checking Docker Hub:"
                            echo "${REPO}:${TAG}"

                            if docker manifest inspect "${REPO}:${TAG}" >/dev/null 2>&1; then
                                echo "Docker tag already exists."

                                return 0
                            fi

                            echo "Docker tag does not exist."

                            return 1
                        }


                        # ------------------------------------------------
                        # Backend
                        # ------------------------------------------------

                        if [ "${BACKEND_CHANGED}" = "true" ]; then

                            if docker manifest inspect \
                                "${BACKEND_REPO}:${BACKEND_VERSION}" \
                                >/dev/null 2>&1; then

                                echo
                                echo "ERROR:"
                                echo "Backend version ${BACKEND_VERSION} already exists."

                                exit 1
                            fi

                            if docker manifest inspect \
                                "${BACKEND_REPO}:${SHORT_SHA}" \
                                >/dev/null 2>&1; then

                                echo
                                echo "ERROR:"
                                echo "Backend SHA tag ${SHORT_SHA} already exists."

                                exit 1
                            fi
                        fi


                        # ------------------------------------------------
                        # Frontend
                        # ------------------------------------------------

                        if [ "${FRONTEND_CHANGED}" = "true" ]; then

                            if docker manifest inspect \
                                "${FRONTEND_REPO}:${FRONTEND_VERSION}" \
                                >/dev/null 2>&1; then

                                echo
                                echo "ERROR:"
                                echo "Frontend version ${FRONTEND_VERSION} already exists."

                                exit 1
                            fi

                            if docker manifest inspect \
                                "${FRONTEND_REPO}:${SHORT_SHA}" \
                                >/dev/null 2>&1; then

                                echo
                                echo "ERROR:"
                                echo "Frontend SHA tag ${SHORT_SHA} already exists."

                                exit 1
                            fi
                        fi

                        echo
                        echo "Docker Hub conflict check OK."
                    '''
                }
            }
        }


        // ============================================================
        // 13 - PUSH BACKEND
        // ============================================================

        stage('13 - Push Backend') {
            when {
                expression {
                    env.BACKEND_CHANGED == 'true'
                }
            }

            steps {

                echo '========== 13 - PUSH BACKEND =========='

                withCredentials([
                    string(
                        credentialsId: 'DOCKER_PASSWORD',
                        variable: 'DOCKER_PASSWORD'
                    )
                ]) {

                    sh '''
                        set -eu
                        set +x

                        echo "${DOCKER_PASSWORD}" | docker login \
                            -u "${DOCKER_USER}" \
                            --password-stdin

                        docker push "${BACKEND_REPO}:${BACKEND_VERSION}"
                        docker push "${BACKEND_REPO}:${SHORT_SHA}"

                        echo
                        echo "Backend Docker push OK."
                    '''
                }
            }
        }


        // ============================================================
        // 14 - PUSH FRONTEND
        // ============================================================

        stage('14 - Push Frontend') {
            when {
                expression {
                    env.FRONTEND_CHANGED == 'true'
                }
            }

            steps {

                echo '========== 14 - PUSH FRONTEND =========='

                withCredentials([
                    string(
                        credentialsId: 'DOCKER_PASSWORD',
                        variable: 'DOCKER_PASSWORD'
                    )
                ]) {

                    sh '''
                        set -eu
                        set +x

                        echo "${DOCKER_PASSWORD}" | docker login \
                            -u "${DOCKER_USER}" \
                            --password-stdin

                        docker push "${FRONTEND_REPO}:${FRONTEND_VERSION}"
                        docker push "${FRONTEND_REPO}:${SHORT_SHA}"

                        echo
                        echo "Frontend Docker push OK."
                    '''
                }
            }
        }


        // ============================================================
        // 15 - VERIFY DOCKER DIGESTS
        // ============================================================

        stage('15 - Verify Docker Images') {
            when {
                anyOf {
                    expression { env.BACKEND_CHANGED == 'true' }
                    expression { env.FRONTEND_CHANGED == 'true' }
                }
            }

            steps {

                echo '========== 15 - VERIFY DOCKER IMAGES =========='

                sh '''
                    set -eu

                    verify_pair() {

                        REPO="$1"
                        VERSION_TAG="$2"
                        SHA_TAG="$3"

                        echo
                        echo "Repository: ${REPO}"

                        VERSION_DIGEST=$(
                            docker buildx imagetools inspect \
                                "${REPO}:${VERSION_TAG}" |
                            awk '/^Digest:/ {print $2; exit}'
                        )

                        SHA_DIGEST=$(
                            docker buildx imagetools inspect \
                                "${REPO}:${SHA_TAG}" |
                            awk '/^Digest:/ {print $2; exit}'
                        )

                        test -n "${VERSION_DIGEST}"
                        test -n "${SHA_DIGEST}"

                        echo "Version digest: ${VERSION_DIGEST}"
                        echo "SHA digest    : ${SHA_DIGEST}"

                        test "${VERSION_DIGEST}" = "${SHA_DIGEST}"

                        echo "Digest match OK."
                    }


                    if [ "${BACKEND_CHANGED}" = "true" ]; then

                        verify_pair \
                            "${BACKEND_REPO}" \
                            "${BACKEND_VERSION}" \
                            "${SHORT_SHA}"
                    fi


                    if [ "${FRONTEND_CHANGED}" = "true" ]; then

                        verify_pair \
                            "${FRONTEND_REPO}" \
                            "${FRONTEND_VERSION}" \
                            "${SHORT_SHA}"
                    fi
                '''
            }
        }


        // ============================================================
        // 16 - CREATE GITHUB RELEASE TAGS
        // ============================================================

        stage('16 - Create GitHub Release Tags') {
            when {
                anyOf {
                    expression { env.BACKEND_CHANGED == 'true' }
                    expression { env.FRONTEND_CHANGED == 'true' }
                }
            }

            steps {

                echo '========== 16 - CREATE GITHUB RELEASE TAGS =========='

                withCredentials([
                    string(
                        credentialsId: 'GITHUB_TOKEN',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {

                    sh '''
                        set -eu
                        set +x

                        create_tag() {

                            TAG="$1"

                            echo
                            echo "Creating GitHub tag:"
                            echo "${TAG}"

                            STATUS=$(
                                curl -sS \
                                    -o /tmp/tag-result.json \
                                    -w "%{http_code}" \
                                    -X POST \
                                    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
                                    -H "Accept: application/vnd.github+json" \
                                    -H "Content-Type: application/json" \
                                    "${GITHUB_API}/repos/${GITHUB_REPO}/git/refs" \
                                    -d "{
                                        \\"ref\\": \\"refs/tags/${TAG}\\",
                                        \\"sha\\": \\"${CURRENT_SHA}\\"
                                    }"
                            )

                            echo "GitHub tag HTTP status: ${STATUS}"

                            if [ "${STATUS}" != "201" ]; then

                                echo
                                echo "GitHub tag creation failed:"
                                cat /tmp/tag-result.json

                                exit 1
                            fi

                            echo "GitHub tag created OK."
                        }


                        if [ "${BACKEND_CHANGED}" = "true" ]; then
                            create_tag "${BACKEND_GITHUB_TAG}"
                        fi


                        if [ "${FRONTEND_CHANGED}" = "true" ]; then
                            create_tag "${FRONTEND_GITHUB_TAG}"
                        fi
                    '''
                }
            }
        }


        // ============================================================
        // 17 - VERIFY GITHUB TAGS
        // ============================================================

        stage('17 - Verify GitHub Tags') {
            when {
                anyOf {
                    expression { env.BACKEND_CHANGED == 'true' }
                    expression { env.FRONTEND_CHANGED == 'true' }
                }
            }

            steps {

                echo '========== 17 - VERIFY GITHUB TAGS =========='

                withCredentials([
                    string(
                        credentialsId: 'GITHUB_TOKEN',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {

                    sh '''
                        set -eu
                        set +x

                        verify_tag() {

                            TAG="$1"

                            echo
                            echo "Verifying:"
                            echo "${TAG}"

                            STATUS=$(
                                curl -sS \
                                    -o /tmp/verify-tag.json \
                                    -w "%{http_code}" \
                                    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
                                    -H "Accept: application/vnd.github+json" \
                                    "${GITHUB_API}/repos/${GITHUB_REPO}/git/ref/tags/${TAG}"
                            )

                            echo "HTTP status: ${STATUS}"

                            test "${STATUS}" = "200"

                            REMOTE_SHA=$(
                                python3 - <<'PY'
import json

with open("/tmp/verify-tag.json") as f:
    data = json.load(f)

print(data.get("object", {}).get("sha", ""))
PY
                            )

                            echo "Tag object SHA: ${REMOTE_SHA}"

                            test -n "${REMOTE_SHA}"

                            # Tag ruleset / annotated tag durumundan dolayı
                            # object SHA doğrudan commit olmayabilir.
                            # Bu nedenle rev-parse ile local Git'ten ayrıca
                            # doğrulama yapıyoruz.
                        }


                        if [ "${BACKEND_CHANGED}" = "true" ]; then

                            verify_tag "${BACKEND_GITHUB_TAG}"

                            git fetch --tags --force origin

                            TAG_COMMIT=$(
                                git rev-list \
                                    -n 1 \
                                    "${BACKEND_GITHUB_TAG}"
                            )

                            echo "Backend tag commit: ${TAG_COMMIT}"

                            test "${TAG_COMMIT}" = "${CURRENT_SHA}"
                        fi


                        if [ "${FRONTEND_CHANGED}" = "true" ]; then

                            verify_tag "${FRONTEND_GITHUB_TAG}"

                            git fetch --tags --force origin

                            TAG_COMMIT=$(
                                git rev-list \
                                    -n 1 \
                                    "${FRONTEND_GITHUB_TAG}"
                            )

                            echo "Frontend tag commit: ${TAG_COMMIT}"

                            test "${TAG_COMMIT}" = "${CURRENT_SHA}"
                        fi

                        echo
                        echo "GitHub tag verification OK."
                    '''
                }
            }
        }


        // ============================================================
        // 18 - FINAL VERIFICATION
        // ============================================================

        stage('18 - Final Verification') {
            steps {

                echo '========== 18 - FINAL VERIFICATION =========='

                sh '''
                    set -eu

                    echo
                    echo "========================================"
                    echo "VERSIONING PIPELINE"
                    echo "========================================"
                    echo

                    echo "Current commit:"
                    echo "${CURRENT_SHA}"

                    echo
                    echo "Backend changed:"
                    echo "${BACKEND_CHANGED}"

                    echo "Frontend changed:"
                    echo "${FRONTEND_CHANGED}"

                    echo

                    if [ "${BACKEND_CHANGED}" = "true" ]; then

                        echo "Backend release:"
                        echo "  Version : ${BACKEND_VERSION}"
                        echo "  Git tag : ${BACKEND_GITHUB_TAG}"
                        echo "  Docker  : ${BACKEND_REPO}:${BACKEND_VERSION}"
                        echo "  Docker  : ${BACKEND_REPO}:${SHORT_SHA}"

                    else

                        echo "Backend:"
                        echo "  SKIPPED"

                    fi

                    echo

                    if [ "${FRONTEND_CHANGED}" = "true" ]; then

                        echo "Frontend release:"
                        echo "  Version : ${FRONTEND_VERSION}"
                        echo "  Git tag : ${FRONTEND_GITHUB_TAG}"
                        echo "  Docker  : ${FRONTEND_REPO}:${FRONTEND_VERSION}"
                        echo "  Docker  : ${FRONTEND_REPO}:${SHORT_SHA}"

                    else

                        echo "Frontend:"
                        echo "  SKIPPED"

                    fi

                    echo
                    echo "========================================"
                    echo "ALL VERSIONING TESTS PASSED"
                    echo "========================================"
                '''
            }
        }
    }


    // ================================================================
    // POST / CLEANUP
    // ================================================================

    post {

        always {

            echo '========== CLEANUP =========='

            sh '''
                set +e

                echo "Removing local images..."

                if [ -n "${BACKEND_VERSION:-}" ]; then
                    docker rmi \
                        "${BACKEND_REPO}:${BACKEND_VERSION}" \
                        >/dev/null 2>&1 || true
                fi

                if [ -n "${BACKEND_SHA_TAG:-}" ]; then
                    docker rmi \
                        "${BACKEND_REPO}:${BACKEND_SHA_TAG}" \
                        >/dev/null 2>&1 || true
                fi

                if [ -n "${FRONTEND_VERSION:-}" ]; then
                    docker rmi \
                        "${FRONTEND_REPO}:${FRONTEND_VERSION}" \
                        >/dev/null 2>&1 || true
                fi

                if [ -n "${FRONTEND_SHA_TAG:-}" ]; then
                    docker rmi \
                        "${FRONTEND_REPO}:${FRONTEND_SHA_TAG}" \
                        >/dev/null 2>&1 || true
                fi

                docker logout >/dev/null 2>&1 || true

                echo "Cleanup completed."
            '''
        }


        success {

            echo '''
========================================
JENKINS VERSIONING: SUCCESS
========================================
'''
        }


        failure {

            echo '''
========================================
JENKINS VERSIONING: FAILED
========================================
'''
        }
    }
}
