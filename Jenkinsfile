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
                echo '========== 01 - CHECKOUT =========='

                checkout scm

                sh '''
                    set -eu

                    echo "Git version:"
                    git --version

                    echo
                    echo "Remote:"
                    git remote -v

                    echo
                    echo "Commit:"
                    git rev-parse HEAD

                    echo
                    echo "Commit message:"
                    git log -1 --pretty=%B

                    if [ -f .git/shallow ]; then
                        echo
                        echo "Shallow repository detected."
                        git fetch --unshallow origin
                    fi

                    echo
                    echo "Fetching branches..."
                    git fetch --force origin

                    echo
                    echo "Fetching tags..."
                    git fetch --tags --force origin
                '''
            }
        }


        stage('02 - GitHub Authentication') {
            steps {
                echo '========== 02 - GITHUB AUTHENTICATION =========='

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

                        echo "GitHub API authentication test..."

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


        stage('03 - GitHub Repository Access') {
            steps {
                echo '========== 03 - GITHUB REPOSITORY ACCESS =========='

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


        stage('04 - GitHub Branch Query') {
            steps {
                echo '========== 04 - GITHUB BRANCH QUERY =========='

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

                        RESULT=$(
                            git \
                                -c credential.helper="!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f" \
                                ls-remote \
                                --heads \
                                https://github.com/demirorsvolkan/todo.git \
                                refs/heads/main
                        )

                        if [ -z "$RESULT" ]; then
                            echo "main branch bulunamadı."
                            exit 1
                        fi

                        echo "$RESULT"
                        echo
                        echo "main branch query OK."
                    '''
                }
            }
        }


        stage('05 - Existing Git Tags Query') {
            steps {
                echo '========== 05 - EXISTING GIT TAGS =========='

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
                            -c credential.helper="!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f" \
                            ls-remote \
                            --tags \
                            https://github.com/demirorsvolkan/todo.git \
                            > /tmp/remote-tags.txt

                        echo
                        echo "Remote tag sayısı:"
                        wc -l /tmp/remote-tags.txt

                        echo
                        echo "İlk 20 tag:"
                        head -20 /tmp/remote-tags.txt || true

                        echo
                        echo "Git tag query OK."
                    '''
                }
            }
        }


        stage('06 - Prepare Variables') {
            steps {
                script {
                    env.TEST_SHA = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    env.TEST_SHORT_SHA = env.TEST_SHA.take(7)

                    env.TEST_ID =
                        "${env.BUILD_NUMBER}-${env.TEST_SHORT_SHA}"

                    env.TEST_GITHUB_TAG =
                        "jenkins-test/${env.TEST_ID}"

                    env.TEST_BACKEND_TAG =
                        "jenkins-test-${env.TEST_ID}"

                    env.TEST_FRONTEND_TAG =
                        "jenkins-test-${env.TEST_ID}"

                    echo '========== 06 - VARIABLES =========='
                    echo "Commit       : ${env.TEST_SHA}"
                    echo "Short SHA    : ${env.TEST_SHORT_SHA}"
                    echo "Test ID      : ${env.TEST_ID}"
                    echo "GitHub tag   : ${env.TEST_GITHUB_TAG}"
                    echo "Backend tag  : ${env.TEST_BACKEND_TAG}"
                    echo "Frontend tag : ${env.TEST_FRONTEND_TAG}"
                }
            }
        }


        stage('07 - GitHub Tag Existence Check') {
            steps {
                echo '========== 07 - TAG EXISTENCE CHECK =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        SHORT_SHA="$(git rev-parse --short=7 HEAD)"
                        TEST_TAG="jenkins-test/${BUILD_NUMBER}-${SHORT_SHA}"

                        echo "Test tag:"
                        echo "$TEST_TAG"

                        RESULT=$(
                            git \
                                -c credential.helper="!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f" \
                                ls-remote \
                                --tags \
                                https://github.com/demirorsvolkan/todo.git \
                                "refs/tags/$TEST_TAG"
                        )

                        if [ -n "$RESULT" ]; then
                            echo "HATA: Test tag zaten mevcut!"
                            echo "$RESULT"
                            exit 1
                        fi

                        echo "Test tag mevcut değil."
                    '''
                }
            }
        }


        stage('08 - Create Local Git Tag') {
            steps {
                echo '========== 08 - CREATE LOCAL TAG =========='

                sh '''
                    set -eu

                    SHORT_SHA="$(git rev-parse --short=7 HEAD)"
                    TEST_TAG="jenkins-test/${BUILD_NUMBER}-${SHORT_SHA}"

                    git config user.name "Jenkins"
                    git config user.email "jenkins@localhost"

                    echo "Tag oluşturuluyor:"
                    echo "$TEST_TAG"

                    git tag -a "$TEST_TAG" \
                        "$(git rev-parse HEAD)" \
                        -m "Jenkins integration test ${BUILD_NUMBER}-${SHORT_SHA}"

                    git show-ref --verify --quiet \
                        "refs/tags/$TEST_TAG"

                    echo
                    echo "Local tag OK."
                '''
            }
        }


        stage('09 - Push GitHub Test Tag') {
            steps {
                echo '========== 09 - PUSH GITHUB TAG =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        SHORT_SHA="$(git rev-parse --short=7 HEAD)"
                        TEST_TAG="jenkins-test/${BUILD_NUMBER}-${SHORT_SHA}"

                        git show-ref --verify --quiet \
                            "refs/tags/$TEST_TAG"

                        echo "GitHub'a tag pushlanıyor..."
                        echo "$TEST_TAG"

                        git \
                            -c credential.helper="!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f" \
                            push \
                            https://github.com/demirorsvolkan/todo.git \
                            "refs/tags/$TEST_TAG"

                        echo
                        echo "GitHub tag push OK."
                    '''
                }
            }
        }


        stage('10 - Verify GitHub Test Tag') {
            steps {
                echo '========== 10 - VERIFY GITHUB TAG =========='

                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        SHORT_SHA="$(git rev-parse --short=7 HEAD)"
                        TEST_TAG="jenkins-test/${BUILD_NUMBER}-${SHORT_SHA}"

                        echo "GitHub tag doğrulanıyor..."
                        echo "$TEST_TAG"

                        RESULT=$(
                            git \
                                -c credential.helper="!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f" \
                                ls-remote \
                                --tags \
                                https://github.com/demirorsvolkan/todo.git \
                                "refs/tags/$TEST_TAG"
                        )

                        if [ -z "$RESULT" ]; then
                            echo "HATA: GitHub tag bulunamadı."
                            exit 1
                        fi

                        echo "$RESULT"

                        echo
                        echo "GitHub tag verification OK."
                    '''
                }
            }
        }


        stage('11 - Docker Hub Login') {
            steps {
                echo '========== 11 - DOCKER HUB LOGIN =========='

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
                echo '========== 12 - DOCKER HUB REPOSITORY ACCESS =========='

                sh '''
                    set -eu

                    echo "Docker Hub erişimi test ediliyor..."

                    docker manifest inspect \
                        "$BACKEND_IMAGE:latest" \
                        >/dev/null

                    echo "Backend repository OK."

                    docker manifest inspect \
                        "$FRONTEND_IMAGE:latest" \
                        >/dev/null

                    echo "Frontend repository OK."
                '''
            }
        }
     

     stage('12A - Docker Hub API Authentication Test') {
    steps {
        echo '========== DOCKER HUB API AUTH TEST =========='

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

                echo "Docker Hub API authentication..."

                test -n "$DOCKER_USERNAME"
                test -n "$DOCKER_PASSWORD"

                # JSON body'yi güvenli şekilde oluştur.
                jq -n \
                    --arg identifier "$DOCKER_USERNAME" \
                    --arg secret "$DOCKER_PASSWORD" \
                    '{
                        identifier: $identifier,
                        secret: $secret
                    }' \
                    > /tmp/docker-auth-request.json

                echo "Docker Hub auth request hazırlanıyor..."

                HTTP_CODE=$(
                    curl \
                        -sS \
                        -X POST \
                        -H "Content-Type: application/json" \
                        -o /tmp/docker-auth-response.json \
                        -w "%{http_code}" \
                        --data-binary @/tmp/docker-auth-request.json \
                        "https://hub.docker.com/v2/auth/token"
                )

                echo "Docker Hub auth HTTP status: $HTTP_CODE"

                if [ "$HTTP_CODE" != "200" ]; then
                    echo
                    echo "Docker Hub API authentication BAŞARISIZ."

                    cat /tmp/docker-auth-response.json

                    exit 1
                fi

                DOCKER_API_TOKEN=$(
                    jq -r '.access_token // empty' \
                    /tmp/docker-auth-response.json
                )

                if [ -z "$DOCKER_API_TOKEN" ]; then
                    echo "Docker Hub API access_token döndürmedi."
                    cat /tmp/docker-auth-response.json
                    exit 1
                fi

                echo
                echo "Docker Hub JWT başarıyla alındı."

                # Token'ın gerçekten çalıştığını ayrıca test ediyoruz.
                HTTP_CODE=$(
                    curl \
                        -sS \
                        -o /tmp/docker-user-response.json \
                        -w "%{http_code}" \
                        -H "Authorization: Bearer $DOCKER_API_TOKEN" \
                        "https://hub.docker.com/v2/user/"
                )

                echo "Docker Hub authenticated API HTTP status: $HTTP_CODE"

                if [ "$HTTP_CODE" != "200" ]; then
                    echo
                    echo "Docker Hub JWT ile API erişimi BAŞARISIZ."
                    cat /tmp/docker-user-response.json
                    exit 1
                fi

                echo
                echo "Docker Hub API authentication OK."
            '''
        }
    }
}


stage('12B - Docker Hub Test Tag Query') {
    steps {
        echo '========== DOCKER HUB TEST TAG QUERY =========='

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

                echo "Backend test tag:"
                echo "$TEST_BACKEND_TAG"

                HTTP_CODE=$(
                    curl \
                        -sS \
                        -o /tmp/backend-tag.json \
                        -w "%{http_code}" \
                        -u "${DOCKER_USERNAME}:${DOCKER_PASSWORD}" \
                        "https://hub.docker.com/v2/repositories/${BACKEND_IMAGE}/tags/${TEST_BACKEND_TAG}"
                )

                echo
                echo "Backend tag HTTP status: $HTTP_CODE"

                cat /tmp/backend-tag.json || true

                if [ "$HTTP_CODE" = "200" ]; then
                    echo
                    echo "HATA: Backend test tag ZATEN VAR!"
                    echo "Aynı test tag'i tekrar kullanılamaz."
                    exit 1
                fi

                if [ "$HTTP_CODE" != "404" ]; then
                    echo
                    echo "HATA: Backend tag sorgusu beklenmeyen HTTP status döndürdü."
                    exit 1
                fi

                echo
                echo "Backend test tag mevcut değil."
                echo "Backend tag oluşturma testine devam edilebilir."
            '''
        }
    }
}


stage('12C - Docker Hub Frontend Test Tag Query') {
    steps {
        echo '========== DOCKER HUB FRONTEND TEST TAG QUERY =========='

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

                echo "Frontend test tag:"
                echo "$TEST_FRONTEND_TAG"

                HTTP_CODE=$(
                    curl \
                        -sS \
                        -o /tmp/frontend-tag.json \
                        -w "%{http_code}" \
                        -u "${DOCKER_USERNAME}:${DOCKER_PASSWORD}" \
                        "https://hub.docker.com/v2/repositories/${FRONTEND_IMAGE}/tags/${TEST_FRONTEND_TAG}"
                )

                echo
                echo "Frontend tag HTTP status: $HTTP_CODE"

                cat /tmp/frontend-tag.json || true

                if [ "$HTTP_CODE" = "200" ]; then
                    echo
                    echo "HATA: Frontend test tag ZATEN VAR!"
                    echo "Aynı test tag'i tekrar kullanılamaz."
                    exit 1
                fi

                if [ "$HTTP_CODE" != "404" ]; then
                    echo
                    echo "HATA: Frontend tag sorgusu beklenmeyen HTTP status döndürdü."
                    exit 1
                fi

                echo
                echo "Frontend test tag mevcut değil."
                echo "Frontend tag oluşturma testine devam edilebilir."
            '''
        }
    }
}

stage('12D - Docker Hub Test Tag DELETE') {
    steps {
        echo '========== DOCKER HUB TEST TAG DELETE =========='

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

                echo "========================================"
                echo "DOCKER HUB DELETE TEST"
                echo "========================================"

                echo
                echo "Username:"
                echo "$DOCKER_USERNAME"

                echo
                echo "Backend:"
                echo "$BACKEND_IMAGE:$TEST_BACKEND_TAG"

                echo
                echo "Frontend:"
                echo "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG"

                #
                # Docker Hub PAT -> JWT
                #
                AUTH_RESPONSE=$(
                    curl -sS \
                        -X POST \
                        -H "Content-Type: application/json" \
                        -d "{\\"identifier\\":\\"${DOCKER_USERNAME}\\",\\"secret\\":\\"${DOCKER_PASSWORD}\\"}" \
                        https://hub.docker.com/v2/auth/token
                )

                DOCKER_TOKEN=$(
                    printf '%s' "$AUTH_RESPONSE" |
                    sed -n 's/.*"access_token"[[:space:]]*:[[:space:]]*"\\([^"]*\\)".*/\\1/p'
                )

                if [ -z "$DOCKER_TOKEN" ]; then
                    echo "HATA: Docker Hub JWT alınamadı."
                    exit 1
                fi

                echo
                echo "Docker Hub JWT authentication OK."

                #
                # ========================================
                # BACKEND TAG VAR MI?
                # ========================================
                #

                echo
                echo "Backend tag kontrol ediliyor..."

                BACKEND_GET_URL="https://hub.docker.com/v2/namespaces/${DOCKER_USERNAME}/repositories/todo-backend/tags/${TEST_BACKEND_TAG}"

                BACKEND_HTTP_CODE=$(
                    curl \
                        -sS \
                        -o /tmp/backend-before-delete.json \
                        -w "%{http_code}" \
                        -H "Authorization: Bearer $DOCKER_TOKEN" \
                        -H "Accept: application/json" \
                        "$BACKEND_GET_URL"
                )

                echo "Backend GET HTTP status: $BACKEND_HTTP_CODE"

                if [ -s /tmp/backend-before-delete.json ]; then
                    cat /tmp/backend-before-delete.json
                fi

                if [ "$BACKEND_HTTP_CODE" != "200" ]; then
                    echo
                    echo "HATA: Backend tag DELETE öncesinde bulunamadı."
                    echo "DELETE işlemi yapılmayacak."
                    exit 1
                fi

                echo
                echo "Backend tag bulundu."

                #
                # ========================================
                # BACKEND DELETE
                # ========================================
                #

                echo
                echo "Backend test tag siliniyor..."

                BACKEND_DELETE_CODE=$(
                    curl \
                        -sS \
                        -o /tmp/backend-delete.json \
                        -w "%{http_code}" \
                        -X DELETE \
                        -H "Authorization: Bearer $DOCKER_TOKEN" \
                        -H "Accept: application/json" \
                        "$BACKEND_GET_URL"
                )

                echo "Backend DELETE HTTP status: $BACKEND_DELETE_CODE"

                if [ -s /tmp/backend-delete.json ]; then
                    cat /tmp/backend-delete.json
                fi

                if [ "$BACKEND_DELETE_CODE" != "204" ]; then
                    echo
                    echo "HATA: Backend tag silinemedi."
                    exit 1
                fi

                echo
                echo "Backend test tag SILINDI."

                #
                # ========================================
                # FRONTEND TAG VAR MI?
                # ========================================
                #

                echo
                echo "Frontend tag kontrol ediliyor..."

                FRONTEND_GET_URL="https://hub.docker.com/v2/namespaces/${DOCKER_USERNAME}/repositories/todo-frontend/tags/${TEST_FRONTEND_TAG}"

                FRONTEND_HTTP_CODE=$(
                    curl \
                        -sS \
                        -o /tmp/frontend-before-delete.json \
                        -w "%{http_code}" \
                        -H "Authorization: Bearer $DOCKER_TOKEN" \
                        -H "Accept: application/json" \
                        "$FRONTEND_GET_URL"
                )

                echo "Frontend GET HTTP status: $FRONTEND_HTTP_CODE"

                if [ -s /tmp/frontend-before-delete.json ]; then
                    cat /tmp/frontend-before-delete.json
                fi

                if [ "$FRONTEND_HTTP_CODE" != "200" ]; then
                    echo
                    echo "HATA: Frontend tag DELETE öncesinde bulunamadı."
                    echo "DELETE işlemi yapılmayacak."
                    exit 1
                fi

                echo
                echo "Frontend tag bulundu."

                #
                # ========================================
                # FRONTEND DELETE
                # ========================================
                #

                echo
                echo "Frontend test tag siliniyor..."

                FRONTEND_DELETE_CODE=$(
                    curl \
                        -sS \
                        -o /tmp/frontend-delete.json \
                        -w "%{http_code}" \
                        -X DELETE \
                        -H "Authorization: Bearer $DOCKER_TOKEN" \
                        -H "Accept: application/json" \
                        "$FRONTEND_GET_URL"
                )

                echo "Frontend DELETE HTTP status: $FRONTEND_DELETE_CODE"

                if [ -s /tmp/frontend-delete.json ]; then
                    cat /tmp/frontend-delete.json
                fi

                if [ "$FRONTEND_DELETE_CODE" != "204" ]; then
                    echo
                    echo "HATA: Frontend tag silinemedi."
                    exit 1
                fi

                echo
                echo "Frontend test tag SILINDI."

                echo
                echo "========================================"
                echo "DOCKER HUB TEST TAG DELETE OK"
                echo "========================================"
            '''
        }
    }
}





        stage('13 - Docker Existing Tags Query') {
            steps {
                echo '========== 13 - DOCKER EXISTING TAGS =========='

                sh '''
                    set -eu

                    echo "Backend latest:"
                    docker manifest inspect \
                        "$BACKEND_IMAGE:latest"

                    echo
                    echo "Frontend latest:"
                    docker manifest inspect \
                        "$FRONTEND_IMAGE:latest"

                    echo
                    echo "Docker existing tags query OK.."
                '''
            }
        }


        stage('14 - Build Backend') {
            steps {
                echo '========== 14 - BUILD BACKEND =========='

                sh '''
                    set -eu

                    test -d backend
                    test -f backend/Dockerfile

                    docker build \
                        -t "$BACKEND_IMAGE:$TEST_BACKEND_TAG" \
                        ./backend

                    docker image inspect \
                        "$BACKEND_IMAGE:$TEST_BACKEND_TAG" \
                        >/dev/null

                    echo
                    echo "Backend build OK."
                '''
            }
        }


        stage('15 - Build Frontend') {
            steps {
                echo '========== 15 - BUILD FRONTEND =========='

                sh '''
                    set -eu

                    test -d frontend
                    test -f frontend/Dockerfile

                    docker build \
                        -t "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG" \
                        ./frontend

                    docker image inspect \
                        "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG" \
                        >/dev/null

                    echo
                    echo "Frontend build OK."
                '''
            }
        }


        stage('16 - Local Image Verification') {
            steps {
                echo '========== 16 - LOCAL IMAGE VERIFICATION =========='

                sh '''
                    set -eu

                    docker image inspect \
                        "$BACKEND_IMAGE:$TEST_BACKEND_TAG" \
                        >/dev/null

                    docker image inspect \
                        "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG" \
                        >/dev/null

                    echo "Both local images OK."
                '''
            }
        }


        stage('17 - Push Backend Image') {
            steps {
                echo '========== 17 - PUSH BACKEND IMAGE =========='

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

                        printf '%s\\n' "$DOCKER_PASSWORD" |
                            docker login \
                                --username "$DOCKER_USERNAME" \
                                --password-stdin

                        docker push \
                            "$BACKEND_IMAGE:$TEST_BACKEND_TAG"

                        echo
                        echo "Backend Docker push OK."
                    '''
                }
            }
        }


        stage('18 - Push Frontend Image') {
            steps {
                echo '========== 18 - PUSH FRONTEND IMAGE =========='

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

                        printf '%s\\n' "$DOCKER_PASSWORD" |
                            docker login \
                                --username "$DOCKER_USERNAME" \
                                --password-stdin

                        docker push \
                            "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG"

                        echo
                        echo "Frontend Docker push OK."
                    '''
                }
            }
        }


        stage('19 - Verify Backend Remote Image') {
            steps {
                echo '========== 19 - VERIFY BACKEND IMAGE =========='

                sh '''
                    set -eu

                    docker manifest inspect \
                        "$BACKEND_IMAGE:$TEST_BACKEND_TAG"

                    echo
                    echo "Backend remote image OK."
                '''
            }
        }


        stage('20 - Verify Frontend Remote Image') {
            steps {
                echo '========== 20 - VERIFY FRONTEND IMAGE =========='

                sh '''
                    set -eu

                    docker manifest inspect \
                        "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG"

                    echo
                    echo "Frontend remote image OK."
                '''
            }
        }


        stage('21 - Backend Digest') {
            steps {
                echo '========== 21 - BACKEND DIGEST =========='

                sh '''
                    set -eu

                    DIGEST=$(
                        docker buildx imagetools inspect \
                            "$BACKEND_IMAGE:$TEST_BACKEND_TAG" |
                        grep -m 1 '^Digest:' |
                        awk '{print $2}'
                    )

                    test -n "$DIGEST"

                    echo "Backend digest:"
                    echo "$DIGEST"

                    printf '%s\\n' "$DIGEST" \
                        > /tmp/backend-digest.txt
                '''
            }
        }


        stage('22 - Frontend Digest') {
            steps {
                echo '========== 22 - FRONTEND DIGEST =========='

                sh '''
                    set -eu

                    DIGEST=$(
                        docker buildx imagetools inspect \
                            "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG" |
                        grep -m 1 '^Digest:' |
                        awk '{print $2}'
                    )

                    test -n "$DIGEST"

                    echo "Frontend digest:"
                    echo "$DIGEST"

                    printf '%s\\n' "$DIGEST" \
                        > /tmp/frontend-digest.txt
                '''
            }
        }


        stage('23 - Final Verification') {
            steps {
                echo '========== 23 - FINAL VERIFICATION =========='

                sh '''
                    set -eu

                    echo "========================================"
                    echo "FINAL INTEGRATION TEST"
                    echo "========================================"

                    echo
                    echo "GitHub"
                    echo "------"
                    echo "Authentication : OK"
                    echo "Repository     : OK"
                    echo "Branch query   : OK"
                    echo "Tag query      : OK"
                    echo "Tag create     : OK"
                    echo "Tag push       : OK"
                    echo "Tag verify     : OK"

                    echo
                    echo "Docker Hub"
                    echo "----------"
                    echo "Authentication : OK"
                    echo "Repository     : OK"
                    echo "Backend build  : OK"
                    echo "Backend push   : OK"
                    echo "Backend verify : OK"
                    echo "Frontend build : OK"
                    echo "Frontend push  : OK"
                    echo "Frontend verify: OK"

                    echo
                    echo "GitHub tag:"
                    echo "$TEST_GITHUB_TAG"

                    echo
                    echo "Backend image:"
                    echo "$BACKEND_IMAGE:$TEST_BACKEND_TAG"

                    echo
                    echo "Frontend image:"
                    echo "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG"

                    echo
                    echo "========================================"
                    echo "ALL TESTS PASSED"
                    echo "========================================"
                '''
            }
        }
    }


    post {

        success {
            echo '''
========================================
JENKINS PIPELINE: SUCCESS
========================================
GitHub authentication      : OK
GitHub repository access   : OK
GitHub branch query        : OK
GitHub tag create/push     : OK
GitHub tag verification    : OK
Docker Hub authentication  : OK
Docker backend build/push  : OK
Docker frontend build/push : OK
Docker image verification  : OK
Digest verification       : OK
========================================
'''
        }


        failure {
            echo '''
========================================
JENKINS PIPELINE: FAILED
========================================
Yukarıdaki son "TEST XX"
başarısız olan aşamadır.
========================================
'''
        }


        always {
            script {

                echo '========== CLEANUP =========='

                sh '''
                    set +e

                    echo "Local Git tag cleanup..."

                    if [ -n "${TEST_GITHUB_TAG:-}" ]; then
                        git tag -d "$TEST_GITHUB_TAG" \
                            >/dev/null 2>&1 || true
                    fi

                    echo "Local backend image cleanup..."

                    if [ -n "${TEST_BACKEND_TAG:-}" ]; then
                        docker rmi \
                            "$BACKEND_IMAGE:$TEST_BACKEND_TAG" \
                            >/dev/null 2>&1 || true
                    fi

                    echo "Local frontend image cleanup..."

                    if [ -n "${TEST_FRONTEND_TAG:-}" ]; then
                        docker rmi \
                            "$FRONTEND_IMAGE:$TEST_FRONTEND_TAG" \
                            >/dev/null 2>&1 || true
                    fi
                '''


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

                        if [ -n "${TEST_GITHUB_TAG:-}" ]; then

                            git \
                                -c credential.helper="!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f" \
                                push \
                                https://github.com/demirorsvolkan/todo.git \
                                --delete \
                                "$TEST_GITHUB_TAG" \
                                >/dev/null 2>&1 || true

                        fi

                        echo "GitHub cleanup tamamlandı."

                        echo
                        echo "Docker backend test tag cleanup..."

                        if [ -n "${TEST_BACKEND_TAG:-}" ]; then

                            curl \
                                -sS \
                                -X DELETE \
                                -u "${DOCKER_USERNAME}:${DOCKER_PASSWORD}" \
                                "https://hub.docker.com/v2/repositories/${BACKEND_IMAGE}/tags/${TEST_BACKEND_TAG}/" \
                                >/dev/null 2>&1 || true

                        fi

                        echo "Backend cleanup tamamlandı."

                        echo
                        echo "Docker frontend test tag cleanup..."

                        if [ -n "${TEST_FRONTEND_TAG:-}" ]; then

                            curl \
                                -sS \
                                -X DELETE \
                                -u "${DOCKER_USERNAME}:${DOCKER_PASSWORD}" \
                                "https://hub.docker.com/v2/repositories/${FRONTEND_IMAGE}/tags/${TEST_FRONTEND_TAG}/" \
                                >/dev/null 2>&1 || true

                        fi

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
