pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
        timestamps()
    }

    environment {
        BACKEND_IMAGE  = 'volkandemirors/todo-backend'
        FRONTEND_IMAGE = 'volkandemirors/todo-frontend'

        TEST_TAG_PREFIX = 'jenkins-test'
    }

    stages {

        stage('01 - Checkout') {
            steps {
                echo '========== TEST 01 - CHECKOUT =========='

                checkout scm

                sh '''
                    set -eu

                    echo "Git version:"
                    git --version

                    echo
                    echo "Remote:"
                    git remote -v

                    echo
                    echo "Current commit:"
                    git rev-parse HEAD

                    echo
                    echo "Current branch/ref:"
                    git branch -a --show-current || true

                    echo
                    echo "Commit message:"
                    git log -1 --pretty=%B
                '''

                sh '''
                    set -eu

                    if [ -f .git/shallow ]; then
                        echo "Repository shallow. Unshallow yapılıyor..."
                        git fetch --unshallow origin
                    fi

                    echo "Fetching branches..."
                    git fetch --force origin

                    echo "Fetching tags..."
                    git fetch --tags --force origin
                '''
            }
        }


        stage('02 - GitHub Token Authentication') {
            steps {
                echo '========== TEST 02 - GITHUB AUTHENTICATION =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        echo "GitHub token Jenkins credential'dan alındı."

                        test -n "$GITHUB_TOKEN"

                        echo "Token uzunluğu:"
                        printf '%s' "$GITHUB_TOKEN" | wc -c

                        echo
                        echo "GitHub API authentication test ediliyor..."

                        HTTP_CODE=$(
                            curl \
                                -sS \
                                -o /tmp/github-user.json \
                                -w '%{http_code}' \
                                -H "Authorization: Bearer $GITHUB_TOKEN" \
                                -H "Accept: application/vnd.github+json" \
                                https://api.github.com/user
                        )

                        echo "GitHub API HTTP status: $HTTP_CODE"

                        if [ "$HTTP_CODE" != "200" ]; then
                            echo "GitHub token authentication BAŞARISIZ."
                            cat /tmp/github-user.json || true
                            exit 1
                        fi

                        echo "GitHub token authentication OK."
                    '''
                }
            }
        }


        stage('03 - GitHub Repository Access') {
            steps {
                echo '========== TEST 03 - GITHUB REPOSITORY ACCESS =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        HTTP_STATUS=$(curl -sS \
                            -o /tmp/github_repo.json \
                            -w "%{http_code}" \
                            -H "Authorization: Bearer $GITHUB_TOKEN" \
                            -H "Accept: application/vnd.github+json" \
                            https://api.github.com/repos/demirorsvolkan/todo)

                        echo "GitHub repository API HTTP status: $HTTP_STATUS"

                        if [ "$HTTP_STATUS" != "200" ]; then
                            echo "GitHub repository erişimi başarısız."
                            cat /tmp/github_repo.json
                            exit 1
                        fi

                        echo "GitHub repository erişimi OK."
                    '''
                }
            }
        }



        stage('04 - GitHub Branch Query') {
            steps {
                echo '========== TEST 04 - GITHUB BRANCH QUERY =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        echo "main branch sorgulanıyor..."

                        git \
                            -c credential.helper="!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f" \
                            ls-remote \
                            --heads \
                            https://github.com/demirorsvolkan/todo.git \
                            refs/heads/main

                        echo
                        echo "main branch sorgusu OK."
                    '''
                }
            }
        }






        stage('05 - Existing Git Tags Query') {
            steps {
                echo '========== TEST 05 - EXISTING TAGS =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        echo "Remote tag'ler sorgulanıyor..."

                        git \
                            -c http.extraheader="Authorization: Bearer ${GITHUB_TOKEN}" \
                            ls-remote \
                            --tags \
                            origin \
                            > remote-tags.txt

                        echo
                        echo "Remote tag satır sayısı:"
                        wc -l remote-tags.txt

                        echo
                        echo "İlk 20 tag:"
                        head -20 remote-tags.txt || true

                        echo
                        echo "Tag sorgusu OK."
                    '''
                }
            }
        }



        stage('06 - Prepare Test Variables') {
            steps {
                script {

                    env.TEST_SHA = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    env.TEST_SHORT_SHA = env.TEST_SHA.take(7)

                    env.TEST_ID = "${env.BUILD_NUMBER}-${env.TEST_SHORT_SHA}"

                    env.TEST_GITHUB_TAG =
                        "jenkins-test/${env.TEST_ID}"

                    env.TEST_BACKEND_VERSION =
                        "jenkins-test-${env.TEST_ID}"

                    env.TEST_FRONTEND_VERSION =
                        "jenkins-test-${env.TEST_ID}"

                    env.TEST_BACKEND_TAG =
                        "jenkins-test-${env.TEST_ID}"

                    env.TEST_FRONTEND_TAG =
                        "jenkins-test-${env.TEST_ID}"

                    echo '========== TEST 06 - VARIABLES =========='
                    echo "Commit       : ${env.TEST_SHA}"
                    echo "Short SHA    : ${env.TEST_SHORT_SHA}"
                    echo "Test ID      : ${env.TEST_ID}"
                    echo "GitHub tag   : ${env.TEST_GITHUB_TAG}"
                    echo "Backend test : ${env.TEST_BACKEND_TAG}"
                    echo "Frontend test: ${env.TEST_FRONTEND_TAG}"
                }
            }
        }


        stage('07 - GitHub Test Tag Does Not Exist') {
            steps {
                echo '========== TEST 07 - TAG EXISTENCE CHECK =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        echo "Test tag kontrol ediliyor:"
                        echo "$TEST_GITHUB_TAG"

                        OUTPUT=$(
                            git \
                                -c http.extraheader="Authorization: Bearer ${GITHUB_TOKEN}" \
                                ls-remote \
                                --tags \
                                origin \
                                "refs/tags/${TEST_GITHUB_TAG}" \
                                "refs/tags/${TEST_GITHUB_TAG}^{}"
                        )

                        if [ -n "$OUTPUT" ]; then
                            echo "HATA: Test tag zaten mevcut:"
                            echo "$OUTPUT"
                            exit 1
                        fi

                        echo "Test tag mevcut değil. Beklenen durum."
                    '''
                }
            }
        }


        stage('08 - Create Local Git Test Tag') {
            steps {
                echo '========== TEST 08 - CREATE LOCAL TAG =========='

                sh '''
                    set -eu

                    echo "Local test tag oluşturuluyor..."

                    git tag -a \
                        "$TEST_GITHUB_TAG" \
                        "$TEST_SHA" \
                        -m "Jenkins integration test $TEST_ID"

                    echo
                    echo "Local tag:"
                    git show-ref --tags "$TEST_GITHUB_TAG"

                    echo
                    echo "Tag commit:"
                    git rev-list -n 1 "$TEST_GITHUB_TAG"

                    echo
                    echo "Beklenen commit:"
                    echo "$TEST_SHA"
                '''
            }
        }


        stage('09 - Push GitHub Test Tag') {
            steps {
                echo '========== TEST 09 - PUSH GITHUB TAG =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        echo "GitHub test tag pushlanıyor..."

                        git \
                            -c http.extraheader="Authorization: Bearer ${GITHUB_TOKEN}" \
                            push \
                            origin \
                            "$TEST_GITHUB_TAG"

                        echo
                        echo "GitHub tag push OK."
                    '''
                }
            }
        }


        stage('10 - Verify GitHub Test Tag') {
            steps {
                echo '========== TEST 10 - VERIFY GITHUB TAG =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        echo "Pushlanan tag tekrar sorgulanıyor..."

                        OUTPUT=$(
                            git \
                                -c http.extraheader="Authorization: Bearer ${GITHUB_TOKEN}" \
                                ls-remote \
                                --tags \
                                origin \
                                "refs/tags/${TEST_GITHUB_TAG}" \
                                "refs/tags/${TEST_GITHUB_TAG}^{}"
                        )

                        if [ -z "$OUTPUT" ]; then
                            echo "HATA: GitHub test tag bulunamadı."
                            exit 1
                        fi

                        echo
                        echo "$OUTPUT"

                        REMOTE_COMMIT=$(
                            printf '%s\\n' "$OUTPUT" |
                            awk \
                                -v tag="$TEST_GITHUB_TAG" \
                                '$2 == "refs/tags/" tag "^{}" {
                                    print $1
                                    exit
                                }'
                        )

                        if [ -z "$REMOTE_COMMIT" ]; then
                            REMOTE_COMMIT=$(
                                printf '%s\\n' "$OUTPUT" |
                                awk \
                                    -v tag="$TEST_GITHUB_TAG" \
                                    '$2 == "refs/tags/" tag {
                                        print $1
                                        exit
                                    }'
                            )
                        fi

                        echo
                        echo "Remote tag commit:"
                        echo "$REMOTE_COMMIT"

                        echo
                        echo "Expected commit:"
                        echo "$TEST_SHA"

                        if [ "$REMOTE_COMMIT" != "$TEST_SHA" ]; then
                            echo "HATA: GitHub tag yanlış commit'i gösteriyor."
                            exit 1
                        fi

                        echo
                        echo "GitHub tag doğrulaması OK."
                    '''
                }
            }
        }


        stage('11 - Docker Hub Login') {
            steps {
                echo '========== TEST 11 - DOCKER HUB LOGIN =========='

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

                        test -n "$DOCKER_USERNAME"
                        test -n "$DOCKER_PASSWORD"

                        echo "Docker Hub login deneniyor..."

                        printf '%s\\n' "$DOCKER_PASSWORD" |
                            docker login \
                                --username "$DOCKER_USERNAME" \
                                --password-stdin

                        echo
                        echo "Docker Hub login OK."
                    '''
                }
            }
        }


        stage('12 - Docker Hub Repository Access') {
            steps {
                echo '========== TEST 12 - DOCKER HUB REPOSITORY ACCESS =========='

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

                        echo "Backend repository kontrolü..."

                        docker manifest inspect \
                            "$BACKEND_IMAGE:latest" \
                            >/dev/null 2>&1 || true

                        echo "Backend repository erişim sorgusu tamamlandı."

                        echo
                        echo "Frontend repository kontrolü..."

                        docker manifest inspect \
                            "$FRONTEND_IMAGE:latest" \
                            >/dev/null 2>&1 || true

                        echo "Frontend repository erişim sorgusu tamamlandı."
                    '''
                }
            }
        }


        stage('13 - Docker Existing Tags Query') {
            steps {
                echo '========== TEST 13 - DOCKER EXISTING TAGS =========='

                sh '''
                    set -eu

                    echo "Backend latest manifest:"
                    docker manifest inspect \
                        "$BACKEND_IMAGE:latest" \
                        2>&1 || true

                    echo
                    echo "Frontend latest manifest:"
                    docker manifest inspect \
                        "$FRONTEND_IMAGE:latest" \
                        2>&1 || true
                '''
            }
        }


        stage('14 - Docker Build Backend') {
            steps {
                echo '========== TEST 14 - BUILD BACKEND =========='

                sh '''
                    set -eu

                    test -d backend

                    echo "Backend Dockerfile:"
                    test -f backend/Dockerfile

                    echo
                    echo "Backend image build başlıyor..."

                    docker build \
                        -t "$BACKEND_IMAGE:$TEST_BACKEND_TAG" \
                        ./backend

                    echo
                    echo "Backend build OK."
                '''
            }
        }


        stage('15 - Docker Build Frontend') {
            steps {
                echo '========== TEST 15 - BUILD FRONTEND =========='

                sh '''
                    set -eu

                    test -d frontend

                    echo "Frontend Dockerfile:"
                    test -f frontend/Dockerfile

                    echo
                    echo "Frontend image build başlıyor..."

                    docker build \
                        -t "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG" \
                        ./frontend

                    echo
                    echo "Frontend build OK."
                '''
            }
        }


        stage('16 - Docker Local Image Verification') {
            steps {
                echo '========== TEST 16 - LOCAL IMAGE VERIFICATION =========='

                sh '''
                    set -eu

                    echo "Backend image:"
                    docker image inspect \
                        "$BACKEND_IMAGE:$TEST_BACKEND_TAG" \
                        >/dev/null

                    echo "Backend image OK."

                    echo
                    echo "Frontend image:"
                    docker image inspect \
                        "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG" \
                        >/dev/null

                    echo "Frontend image OK."
                '''
            }
        }


        stage('17 - Push Backend Test Image') {
            steps {
                echo '========== TEST 17 - PUSH BACKEND IMAGE =========='

                sh '''
                    set -eu

                    echo "Backend test image pushlanıyor..."

                    docker push \
                        "$BACKEND_IMAGE:$TEST_BACKEND_TAG"

                    echo
                    echo "Backend Docker push OK."
                '''
            }
        }


        stage('18 - Push Frontend Test Image') {
            steps {
                echo '========== TEST 18 - PUSH FRONTEND IMAGE =========='

                sh '''
                    set -eu

                    echo "Frontend test image pushlanıyor..."

                    docker push \
                        "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG"

                    echo
                    echo "Frontend Docker push OK."
                '''
            }
        }


        stage('19 - Verify Backend Docker Image') {
            steps {
                echo '========== TEST 19 - VERIFY BACKEND IMAGE =========='

                sh '''
                    set -eu

                    echo "Backend remote image kontrol ediliyor..."

                    docker manifest inspect \
                        "$BACKEND_IMAGE:$TEST_BACKEND_TAG"

                    echo
                    echo "Backend remote image OK."
                '''
            }
        }


        stage('20 - Verify Frontend Docker Image') {
            steps {
                echo '========== TEST 20 - VERIFY FRONTEND IMAGE =========='

                sh '''
                    set -eu

                    echo "Frontend remote image kontrol ediliyor..."

                    docker manifest inspect \
                        "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG"

                    echo
                    echo "Frontend remote image OK."
                '''
            }
        }


        stage('21 - Backend Digest') {
            steps {
                echo '========== TEST 21 - BACKEND DIGEST =========='

                sh '''
                    set -eu

                    docker buildx imagetools inspect \
                        "$BACKEND_IMAGE:$TEST_BACKEND_TAG" |
                    grep -m 1 '^Digest:' |
                    awk '{print $2}' |
                    tee /tmp/backend-digest.txt

                    test -s /tmp/backend-digest.txt

                    echo
                    echo "Backend digest OK."
                '''
            }
        }


        stage('22 - Frontend Digest') {
            steps {
                echo '========== TEST 22 - FRONTEND DIGEST =========='

                sh '''
                    set -eu

                    docker buildx imagetools inspect \
                        "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG" |
                    grep -m 1 '^Digest:' |
                    awk '{print $2}' |
                    tee /tmp/frontend-digest.txt

                    test -s /tmp/frontend-digest.txt

                    echo
                    echo "Frontend digest OK."
                '''
            }
        }


        stage('23 - Final Integration Verification') {
            steps {
                echo '========== TEST 23 - FINAL INTEGRATION CHECK =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        echo "========================================"
                        echo "FINAL TEST"
                        echo "========================================"

                        echo
                        echo "GitHub:"
                        echo "  Repository access : OK"
                        echo "  Tag push           : OK"
                        echo "  Tag verification   : OK"

                        echo
                        echo "Docker Hub:"
                        echo "  Login              : OK"
                        echo "  Backend build      : OK"
                        echo "  Backend push       : OK"
                        echo "  Backend verify     : OK"
                        echo "  Frontend build     : OK"
                        echo "  Frontend push      : OK"
                        echo "  Frontend verify    : OK"

                        echo
                        echo "Test GitHub tag:"
                        echo "$TEST_GITHUB_TAG"

                        echo
                        echo "Backend test image:"
                        echo "$BACKEND_IMAGE:$TEST_BACKEND_TAG"

                        echo
                        echo "Frontend test image:"
                        echo "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG"

                        echo
                        echo "========================================"
                        echo "ALL TESTS PASSED"
                        echo "========================================"
                    '''
                }
            }
        }
    }


    post {

        success {
            echo '''
========================================
JENKINS INTEGRATION TEST: SUCCESS
========================================
GitHub authentication      : OK
GitHub repository access   : OK
GitHub tag create/push     : OK
GitHub tag verification    : OK
Docker Hub authentication  : OK
Docker backend build/push  : OK
Docker frontend build/push : OK
Docker image verification  : OK
========================================
'''
        }


        failure {
            echo '''
========================================
JENKINS INTEGRATION TEST: FAILED
========================================
Yukarıdaki son "TEST XX" aşaması
başarısız olan operasyonu gösterir.
========================================
'''
        }


        always {

            script {

                echo '========== CLEANUP =========='

                sh '''
                    set +e

                    echo "Local Git test tag siliniyor..."

                    git tag -d "$TEST_GITHUB_TAG" \
                        >/dev/null 2>&1 || true

                    echo "Local Docker backend image siliniyor..."

                    docker rmi \
                        "$BACKEND_IMAGE:$TEST_BACKEND_TAG" \
                        >/dev/null 2>&1 || true

                    echo "Local Docker frontend image siliniyor..."

                    docker rmi \
                        "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG" \
                        >/dev/null 2>&1 || true
                '''


                /*
                 * Gerçek remote cleanup.
                 *
                 * Sadece bu testin oluşturduğu isimler silinir.
                 */
                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    ),
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {

                    sh '''
                        set +e
                        set +x

                        echo
                        echo "Remote GitHub test tag cleanup..."

                        git \
                            -c http.extraheader="Authorization: Bearer ${GITHUB_TOKEN}" \
                            push \
                            origin \
                            --delete \
                            "$TEST_GITHUB_TAG" \
                            >/dev/null 2>&1 || true

                        echo "GitHub cleanup tamamlandı."

                        echo
                        echo "Docker backend test tag cleanup..."

                        curl \
                            -sS \
                            -X DELETE \
                            -u "${DOCKER_USERNAME}:${DOCKER_PASSWORD}" \
                            "https://hub.docker.com/v2/repositories/${BACKEND_IMAGE}/tags/${TEST_BACKEND_TAG}/" \
                            >/dev/null 2>&1 || true

                        echo "Backend cleanup tamamlandı."

                        echo
                        echo "Docker frontend test tag cleanup..."

                        curl \
                            -sS \
                            -X DELETE \
                            -u "${DOCKER_USERNAME}:${DOCKER_PASSWORD}" \
                            "https://hub.docker.com/v2/repositories/${FRONTEND_IMAGE}/tags/${TEST_FRONTEND_TAG}/" \
                            >/dev/null 2>&1 || true

                        echo "Frontend cleanup tamamlandı."

                        echo
                        echo "Docker logout..."

                        docker logout >/dev/null 2>&1 || true

                        echo
                        echo "Cleanup tamamlandı."
                    '''
                }
            }
        }
    }
}
