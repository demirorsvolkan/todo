pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    environment {
        BACKEND_IMAGE = 'volkandemirors/todo-backend'
        FRONTEND_IMAGE = 'volkandemirors/todo-frontend'
        BACKEND_CHANGED = 'false'
        FRONTEND_CHANGED = 'false'
        BACKEND_SKIP = 'false'
        FRONTEND_SKIP = 'false'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    set -e
                    if [ -f .git/shallow ]; then
                        git fetch --unshallow origin
                    fi
                    git fetch --tags --force origin
                    git fetch origin main --force
                '''
            }
        }

        stage('Validate Trigger') {
            steps {
                script {
                    def isTagBuild = sh(
                        script: '''
                            if [ -n "${TAG_NAME:-}" ]; then
                                exit 0
                            fi
                            if git describe --exact-match --tags HEAD >/dev/null 2>&1; then
                                exit 0
                            fi
                            exit 1
                        ''',
                        returnStatus: true
                    ) == 0

                    if (isTagBuild) {
                        currentBuild.result = 'NOT_BUILT'
                        error('Tag-triggered build ignored.')
                    }

                    env.TRIGGER_SHA = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    env.SHORT_SHA = env.TRIGGER_SHA.take(7)

                    env.COMMIT_MESSAGE = sh(
                        script: 'git log -1 --pretty=%B',
                        returnStdout: true
                    ).trim()

                    echo "Trigger SHA    : ${env.TRIGGER_SHA}"
                    echo "Short SHA      : ${env.SHORT_SHA}"
                    echo "Commit message : ${env.COMMIT_MESSAGE}"
                }
            }
        }

        stage('Detect Changes') {
            steps {
                script {
                    env.BACKEND_BASE_TAG = findLatestValidTag('backend', env.TRIGGER_SHA)
                    env.BACKEND_BASE_COMMIT = getTagCommit(env.BACKEND_BASE_TAG)
                    env.BACKEND_CHANGED = gitDiffExists(
                        env.BACKEND_BASE_COMMIT,
                        env.TRIGGER_SHA,
                        'backend/'
                    ) ? 'true' : 'false'

                    env.FRONTEND_BASE_TAG = findLatestValidTag('frontend', env.TRIGGER_SHA)
                    env.FRONTEND_BASE_COMMIT = getTagCommit(env.FRONTEND_BASE_TAG)
                    env.FRONTEND_CHANGED = gitDiffExists(
                        env.FRONTEND_BASE_COMMIT,
                        env.TRIGGER_SHA,
                        'frontend/'
                    ) ? 'true' : 'false'

                    echo "Backend base    : ${env.BACKEND_BASE_TAG}"
                    echo "Backend changed : ${env.BACKEND_CHANGED}"
                    echo "Frontend base   : ${env.FRONTEND_BASE_TAG}"
                    echo "Frontend changed: ${env.FRONTEND_CHANGED}"

                    if (
                        env.BACKEND_CHANGED == 'false' &&
                        env.FRONTEND_CHANGED == 'false'
                    ) {
                        currentBuild.result = 'NOT_BUILT'
                        error('Backend veya frontend değişmedi.')
                    }
                }
            }
        }

        stage('Calculate Versions') {
            steps {
                script {
                    def versionType = 'patch'

                    if (env.COMMIT_MESSAGE.startsWith('feat!:')) {
                        versionType = 'major'
                    } else if (env.COMMIT_MESSAGE.startsWith('feat:')) {
                        versionType = 'minor'
                    }

                    if (env.BACKEND_CHANGED == 'true') {
                        def parts = parseTag(env.BACKEND_BASE_TAG, 'backend')
                        def major = parts[0]
                        def minor = parts[1]
                        def patch = parts[2]

                        if (versionType == 'major') {
                            major++
                            minor = 0
                            patch = 0
                        } else if (versionType == 'minor') {
                            minor++
                            patch = 0
                        } else {
                            patch++
                        }

                        env.BACKEND_VERSION = "${major}.${minor}.${patch}"
                        env.BACKEND_TAG = "backend/v${env.BACKEND_VERSION}-sha.${env.SHORT_SHA}"
                    }

                    if (env.FRONTEND_CHANGED == 'true') {
                        def parts = parseTag(env.FRONTEND_BASE_TAG, 'frontend')
                        def major = parts[0]
                        def minor = parts[1]
                        def patch = parts[2]

                        if (versionType == 'major') {
                            major++
                            minor = 0
                            patch = 0
                        } else if (versionType == 'minor') {
                            minor++
                            patch = 0
                        } else {
                            patch++
                        }

                        env.FRONTEND_VERSION = "${major}.${minor}.${patch}"
                        env.FRONTEND_TAG = "frontend/v${env.FRONTEND_VERSION}-sha.${env.SHORT_SHA}"
                    }

                    echo "Version type: ${versionType}"
                    echo "Backend: ${env.BACKEND_VERSION ?: 'unchanged'}"
                    echo "Frontend: ${env.FRONTEND_VERSION ?: 'unchanged'}"
                }
            }
        }

        stage('Docker Hub Check') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'dockerhub-credentials',
                            usernameVariable: 'DOCKER_USERNAME',
                            passwordVariable: 'DOCKER_PASSWORD'
                        ),
                        string(
                            credentialsId: 'github-token',
                            variable: 'GITHUB_TOKEN'
                        )
                    ]) {
                        sh '''
                            set -e
                            set +x
                            echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
                        '''

                        if (
                            env.BACKEND_CHANGED == 'true' &&
                            env.BACKEND_SKIP != 'true'
                        ) {
                            if (checkDockerImage(
                                env.BACKEND_IMAGE,
                                env.BACKEND_VERSION,
                                env.SHORT_SHA,
                                env.BACKEND_TAG,
                                env.TRIGGER_SHA
                            ) == 'SKIP') {
                                env.BACKEND_SKIP = 'true'
                            }
                        }

                        if (
                            env.FRONTEND_CHANGED == 'true' &&
                            env.FRONTEND_SKIP != 'true'
                        ) {
                            if (checkDockerImage(
                                env.FRONTEND_IMAGE,
                                env.FRONTEND_VERSION,
                                env.SHORT_SHA,
                                env.FRONTEND_TAG,
                                env.TRIGGER_SHA
                            ) == 'SKIP') {
                                env.FRONTEND_SKIP = 'true'
                            }
                        }
                    }
                }
            }
        }

        stage('Build Images') {
            steps {
                script {
                    if (
                        env.BACKEND_CHANGED == 'true' &&
                        env.BACKEND_SKIP != 'true'
                    ) {
                        withEnv([
                            "IMAGE=${env.BACKEND_IMAGE}",
                            "VERSION=${env.BACKEND_VERSION}",
                            "SHA=${env.SHORT_SHA}"
                        ]) {
                            sh '''
                                set -e
                                docker build \
                                    -t "$IMAGE:v$VERSION" \
                                    -t "$IMAGE:sha-$SHA" \
                                    ./backend
                            '''
                        }
                    }

                    if (
                        env.FRONTEND_CHANGED == 'true' &&
                        env.FRONTEND_SKIP != 'true'
                    ) {
                        withEnv([
                            "IMAGE=${env.FRONTEND_IMAGE}",
                            "VERSION=${env.FRONTEND_VERSION}",
                            "SHA=${env.SHORT_SHA}"
                        ]) {
                            sh '''
                                set -e
                                docker build \
                                    -t "$IMAGE:v$VERSION" \
                                    -t "$IMAGE:sha-$SHA" \
                                    ./frontend
                            '''
                        }
                    }
                }
            }
        }

        stage('Push Images') {
            steps {
                script {
                    if (
                        env.BACKEND_CHANGED == 'true' &&
                        env.BACKEND_SKIP != 'true'
                    ) {
                        withEnv([
                            "IMAGE=${env.BACKEND_IMAGE}",
                            "VERSION=${env.BACKEND_VERSION}",
                            "SHA=${env.SHORT_SHA}"
                        ]) {
                            sh '''
                                set -e
                                docker push "$IMAGE:v$VERSION"
                                docker push "$IMAGE:sha-$SHA"
                            '''
                        }
                    }

                    if (
                        env.FRONTEND_CHANGED == 'true' &&
                        env.FRONTEND_SKIP != 'true'
                    ) {
                        withEnv([
                            "IMAGE=${env.FRONTEND_IMAGE}",
                            "VERSION=${env.FRONTEND_VERSION}",
                            "SHA=${env.SHORT_SHA}"
                        ]) {
                            sh '''
                                set -e
                                docker push "$IMAGE:v$VERSION"
                                docker push "$IMAGE:sha-$SHA"
                            '''
                        }
                    }
                }
            }
        }

        stage('Create GitHub Tags') {
            steps {
                script {
                    withCredentials([
                        string(
                            credentialsId: 'github-token',
                            variable: 'GITHUB_TOKEN'
                        )
                    ]) {
                        if (
                            env.BACKEND_CHANGED == 'true' &&
                            env.BACKEND_SKIP != 'true'
                        ) {
                            withEnv([
                                "CREATE_TAG=${env.BACKEND_TAG}",
                                "CREATE_SHA=${env.TRIGGER_SHA}"
                            ]) {
                                sh '''
                                    set -e
                                    set +x
                                    git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" tag -a "$CREATE_TAG" "$CREATE_SHA" -m "Release $CREATE_TAG"
                                    git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" push origin "$CREATE_TAG"
                                '''
                            }
                        }

                        if (
                            env.FRONTEND_CHANGED == 'true' &&
                            env.FRONTEND_SKIP != 'true'
                        ) {
                            withEnv([
                                "CREATE_TAG=${env.FRONTEND_TAG}",
                                "CREATE_SHA=${env.TRIGGER_SHA}"
                            ]) {
                                sh '''
                                    set -e
                                    set +x
                                    git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" tag -a "$CREATE_TAG" "$CREATE_SHA" -m "Release $CREATE_TAG"
                                    git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" push origin "$CREATE_TAG"
                                '''
                            }
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Release başarılı!'
        }
        always {
            sh 'docker logout || true'
        }
    }
}

def findLatestValidTag(String component, String triggerSha) {
    def tags = withEnv([
        "COMPONENT=$component",
        "TRIGGER_SHA=$triggerSha"
    ]) {
        sh(
            script: '''
                git tag --merged "$TRIGGER_SHA" --sort=-v:refname |
                grep -E "^${COMPONENT}/v[0-9]+\\.[0-9]+\\.[0-9]+-sha\\.[0-9a-fA-F]+$" || true
            ''',
            returnStdout: true
        ).trim()
    }

    if (!tags) {
        return "${component}/v0.0.0-sha.0000000"
    }

    for (String tag : tags.split('\n')) {
        tag = tag.trim()
        if (!tag) {
            continue
        }

        def parts = parseTag(tag, component)
        def tagSha = parts[3]
        def tagCommit = getTagCommit(tag)

        if (tagCommit.toLowerCase().startsWith(tagSha.toLowerCase())) {
            return tag
        }
    }

    return "${component}/v0.0.0-sha.0000000"
}

def parseTag(String tag, String component) {
    def prefix = "${component}/v"
    def suffix = '-sha.'

    if (!tag.startsWith(prefix) || !tag.contains(suffix)) {
        error("Geçersiz tag: ${tag}")
    }

    def value = tag.substring(prefix.length())
    def index = value.indexOf(suffix)

    if (index < 0) {
        error("Geçersiz tag: ${tag}")
    }

    def version = value.substring(0, index)
    def sha = value.substring(index + suffix.length())
    def numbers = version.split('\\.')

    if (
        numbers.size() != 3 ||
        !numbers[0].isInteger() ||
        !numbers[1].isInteger() ||
        !numbers[2].isInteger() ||
        !sha.matches('[0-9a-fA-F]+')
    ) {
        error("Geçersiz tag: ${tag}")
    }

    return [
        numbers[0] as int,
        numbers[1] as int,
        numbers[2] as int,
        sha
    ]
}

def getTagCommit(String tag) {
    if (tag.endsWith('/v0.0.0-sha.0000000')) {
        return ''
    }

    return withEnv(["RELEASE_TAG=${tag}"]) {
        sh(
            script: '''
                set -e
                git rev-list -n 1 "$RELEASE_TAG"
            ''',
            returnStdout: true
        ).trim()
    }
}


def gitDiffExists(String oldCommit, String newCommit, String componentPath) {
    if (!oldCommit) {
        return sh(
            script: "git ls-tree -r --name-only '${newCommit}' -- '${componentPath}' | grep -q .",
            returnStatus: true
        ) == 0
    }

    def result = withEnv([
        "OLD_COMMIT=${oldCommit}",
        "NEW_COMMIT=${newCommit}",
        "COMPONENT_PATH=${componentPath}"
    ]) {
        sh(
            script: '''
                git diff --quiet "$OLD_COMMIT" "$NEW_COMMIT" -- "$COMPONENT_PATH"
            ''',
            returnStatus: true
        )
    }

    if (result == 0) return false
    if (result == 1) return true

    error("Git diff failed: ${componentPath}")
}


def checkDockerImage(
    String image,
    String version,
    String sha,
    String githubTag,
    String triggerSha
) {
    def remoteTagOutput = withEnv([
        "TAG_TO_CHECK=$githubTag"
    ]) {
        sh(
            script: '''
                set -e
                git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                    ls-remote --tags origin \
                    "refs/tags/$TAG_TO_CHECK" \
                    "refs/tags/$TAG_TO_CHECK^{}"
            ''',
            returnStdout: true
        ).trim()
    }

    def remoteTagCommit = ''

    if (remoteTagOutput) {
        remoteTagCommit = withEnv([
            "REMOTE_TAG_OUTPUT=$remoteTagOutput",
            "EXPECTED_TAG=$githubTag"
        ]) {
            sh(
                script: '''
                    printf '%s\n' "$REMOTE_TAG_OUTPUT" |
                    awk -v tag="$EXPECTED_TAG" '$2 == "refs/tags/" tag "^{}" {print $1; exit}'
                ''',
                returnStdout: true
            ).trim()
        }

        if (!remoteTagCommit) {
            remoteTagCommit = withEnv([
                "REMOTE_TAG_OUTPUT=$remoteTagOutput",
                "EXPECTED_TAG=$githubTag"
            ]) {
                sh(
                    script: '''
                        printf '%s\n' "$REMOTE_TAG_OUTPUT" |
                        awk -v tag="$EXPECTED_TAG" '$2 == "refs/tags/" tag {print $1; exit}'
                    ''',
                    returnStdout: true
                ).trim()
            }
        }

        if (!remoteTagCommit) {
            error("GitHub tag commit alınamadı: ${githubTag}")
        }

        if (!remoteTagCommit.equalsIgnoreCase(triggerSha)) {
            error("GitHub tag yanlış commit'i gösteriyor: ${githubTag}")
        }
    }

    def versionExists = withEnv([
        "IMAGE=$image",
        "VERSION=$version"
    ]) {
        sh(
            script: '''
                docker manifest inspect "$IMAGE:v$VERSION" >/dev/null 2>&1
            ''',
            returnStatus: true
        ) == 0
    }

    if (!versionExists && !remoteTagOutput) {
        return 'BUILD'
    }

    if (!versionExists && remoteTagOutput) {
        error("GitHub tag var fakat Docker image yok: ${image}:v${version}")
    }

    def versionDigest = withEnv([
        "IMAGE=$image",
        "VERSION=$version"
    ]) {
        sh(
            script: '''
                set -e
                docker buildx imagetools inspect "$IMAGE:v$VERSION" |
                grep -m 1 '^Digest:' |
                awk '{print $2}'
            ''',
            returnStdout: true
        ).trim()
    }

    if (!versionDigest) {
        error("Docker image digest alınamadı: ${image}:v${version}")
    }

    def shaDigest = withEnv([
        "IMAGE=$image",
        "SHA=$sha"
    ]) {
        sh(
            script: '''
                docker buildx imagetools inspect "$IMAGE:sha-$SHA" 2>/dev/null |
                grep -m 1 '^Digest:' |
                awk '{print $2}' || true
            ''',
            returnStdout: true
        ).trim()
    }

    if (!shaDigest) {
        error("Version image var fakat SHA image yok: ${image}:sha-${sha}")
    }

    if (versionDigest != shaDigest) {
        error("Digest uyuşmazlığı: ${image}:v${version}")
    }

    if (remoteTagOutput) {
        return 'SKIP'
    }

    error("Docker image var fakat GitHub tag yok: ${githubTag}")
}
