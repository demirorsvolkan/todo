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

                    /*
                     * NONE = Bu component için daha önce
                     * hiçbir release tag'ı yok.
                     *
                     * İLK RELEASE durumunda:
                     * - diff yapılmaz
                     * - component otomatik changed=true kabul edilir
                     */

                    env.BACKEND_BASE_TAG = findLatestValidTag(
                        'backend',
                        env.TRIGGER_SHA
                    )

                    env.FRONTEND_BASE_TAG = findLatestValidTag(
                        'frontend',
                        env.TRIGGER_SHA
                    )


                    // ==========================
                    // BACKEND
                    // ==========================

                    if (env.BACKEND_BASE_TAG == 'NONE') {

                        env.BACKEND_CHANGED = 'true'

                        echo 'Backend: RELEASE YOK'
                        echo 'Backend: İlk release → 0.0.0 baz alınacak'
                        echo 'Backend: Diff kontrolü YOK'
                        echo 'Backend: Changed = true'

                    } else {

                        def backendCommit = getTagCommit(
                            env.BACKEND_BASE_TAG
                        )

                        env.BACKEND_CHANGED = gitDiffExists(
                            backendCommit,
                            env.TRIGGER_SHA,
                            'backend/'
                        ) ? 'true' : 'false'

                        echo "Backend release : ${env.BACKEND_BASE_TAG}"
                        echo "Backend commit  : ${backendCommit}"
                        echo "Backend changed : ${env.BACKEND_CHANGED}"
                    }


                    // ==========================
                    // FRONTEND
                    // ==========================

                    if (env.FRONTEND_BASE_TAG == 'NONE') {

                        env.FRONTEND_CHANGED = 'true'

                        echo 'Frontend: RELEASE YOK'
                        echo 'Frontend: İlk release → 0.0.0 baz alınacak'
                        echo 'Frontend: Diff kontrolü YOK'
                        echo 'Frontend: Changed = true'

                    } else {

                        def frontendCommit = getTagCommit(
                            env.FRONTEND_BASE_TAG
                        )

                        env.FRONTEND_CHANGED = gitDiffExists(
                            frontendCommit,
                            env.TRIGGER_SHA,
                            'frontend/'
                        ) ? 'true' : 'false'

                        echo "Frontend release : ${env.FRONTEND_BASE_TAG}"
                        echo "Frontend commit  : ${frontendCommit}"
                        echo "Frontend changed : ${env.FRONTEND_CHANGED}"
                    }


                    echo '========================================'
                    echo "Backend base    : ${env.BACKEND_BASE_TAG}"
                    echo "Backend changed : ${env.BACKEND_CHANGED}"
                    echo "Frontend base   : ${env.FRONTEND_BASE_TAG}"
                    echo "Frontend changed: ${env.FRONTEND_CHANGED}"
                    echo '========================================'


                    /*
                     * Burada artık ilk release problemi yaşanmaz.
                     *
                     * Hiç release yoksa zaten changed=true.
                     */
                    if (
                        env.BACKEND_CHANGED != 'true' &&
                        env.FRONTEND_CHANGED != 'true'
                    ) {
                        error('Backend veya frontend değişmedi.')
                    }
                }
            }
        }


        stage('Calculate Versions') {
            steps {
                script {

                    /*
                     * Commit mesajı SADECE version bump
                     * türünü belirler.
                     *
                     * feat!:  -> major
                     * feat:   -> minor
                     * diğer   -> patch
                     */

                    def versionType = 'patch'

                    if (env.COMMIT_MESSAGE =~ /(?m)^feat!:/) {
                        versionType = 'major'
                    } else if (env.COMMIT_MESSAGE =~ /(?m)^feat:/) {
                        versionType = 'minor'
                    }


                    // ==========================
                    // BACKEND VERSION
                    // ==========================

                    if (env.BACKEND_CHANGED == 'true') {

                        if (env.BACKEND_BASE_TAG == 'NONE') {

                            /*
                             * İLK BACKEND RELEASE
                             *
                             * Base = 0.0.0
                             */

                            if (versionType == 'major') {
                                env.BACKEND_VERSION = '1.0.0'
                            } else if (versionType == 'minor') {
                                env.BACKEND_VERSION = '0.1.0'
                            } else {
                                env.BACKEND_VERSION = '0.0.1'
                            }

                        } else {

                            def matcher =
                                env.BACKEND_BASE_TAG =~
                                /^backend\/v([0-9]+)\.([0-9]+)\.([0-9]+)-sha\.[0-9a-fA-F]+$/

                            if (!matcher.matches()) {
                                error(
                                    "Geçersiz backend base tag: " +
                                    env.BACKEND_BASE_TAG
                                )
                            }

                            int major = matcher[0][1] as int
                            int minor = matcher[0][2] as int
                            int patch = matcher[0][3] as int

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

                            env.BACKEND_VERSION =
                                "${major}.${minor}.${patch}"
                        }

                        env.BACKEND_TAG =
                            "backend/v${env.BACKEND_VERSION}-sha.${env.SHORT_SHA}"
                    }


                    // ==========================
                    // FRONTEND VERSION
                    // ==========================

                    if (env.FRONTEND_CHANGED == 'true') {

                        if (env.FRONTEND_BASE_TAG == 'NONE') {

                            /*
                             * İLK FRONTEND RELEASE
                             *
                             * Base = 0.0.0
                             */

                            if (versionType == 'major') {
                                env.FRONTEND_VERSION = '1.0.0'
                            } else if (versionType == 'minor') {
                                env.FRONTEND_VERSION = '0.1.0'
                            } else {
                                env.FRONTEND_VERSION = '0.0.1'
                            }

                        } else {

                            def matcher =
                                env.FRONTEND_BASE_TAG =~
                                /^frontend\/v([0-9]+)\.([0-9]+)\.([0-9]+)-sha\.[0-9a-fA-F]+$/

                            if (!matcher.matches()) {
                                error(
                                    "Geçersiz frontend base tag: " +
                                    env.FRONTEND_BASE_TAG
                                )
                            }

                            int major = matcher[0][1] as int
                            int minor = matcher[0][2] as int
                            int patch = matcher[0][3] as int

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

                            env.FRONTEND_VERSION =
                                "${major}.${minor}.${patch}"
                        }

                        env.FRONTEND_TAG =
                            "frontend/v${env.FRONTEND_VERSION}-sha.${env.SHORT_SHA}"
                    }


                    echo "Version type     : ${versionType}"
                    echo "Backend version  : ${env.BACKEND_VERSION ?: '-'}"
                    echo "Frontend version : ${env.FRONTEND_VERSION ?: '-'}"
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

                            echo "$DOCKER_PASSWORD" |
                                docker login \
                                -u "$DOCKER_USERNAME" \
                                --password-stdin
                        '''


                        if (
                            env.BACKEND_CHANGED == 'true' &&
                            env.BACKEND_SKIP != 'true'
                        ) {

                            if (
                                checkDockerImage(
                                    env.BACKEND_IMAGE,
                                    env.BACKEND_VERSION,
                                    env.SHORT_SHA,
                                    env.BACKEND_TAG,
                                    env.TRIGGER_SHA
                                ) == 'SKIP'
                            ) {
                                env.BACKEND_SKIP = 'true'
                            }
                        }


                        if (
                            env.FRONTEND_CHANGED == 'true' &&
                            env.FRONTEND_SKIP != 'true'
                        ) {

                            if (
                                checkDockerImage(
                                    env.FRONTEND_IMAGE,
                                    env.FRONTEND_VERSION,
                                    env.SHORT_SHA,
                                    env.FRONTEND_TAG,
                                    env.TRIGGER_SHA
                                ) == 'SKIP'
                            ) {
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

                                    git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                                        tag -a "$CREATE_TAG" "$CREATE_SHA" \
                                        -m "Release $CREATE_TAG"

                                    git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                                        push origin "$CREATE_TAG"
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

                                    git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                                        tag -a "$CREATE_TAG" "$CREATE_SHA" \
                                        -m "Release $CREATE_TAG"

                                    git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                                        push origin "$CREATE_TAG"
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


/*
 * ============================================================
 * FIND LATEST VALID RELEASE TAG
 * ============================================================
 *
 * Sonuç:
 *
 *   backend/frontend release varsa:
 *       backend/vX.Y.Z-sha.XXXXXXX
 *
 *   hiç release yoksa:
 *       NONE
 *
 * ÖNEMLİ:
 * NONE bir gerçek Git tag değildir.
 * Sadece pipeline içerisinde "ilk release" durumunu
 * açıkça temsil eder.
 */
def findLatestValidTag(String component, String triggerSha) {

    def tags = withEnv([
        "COMPONENT=${component}",
        "TRIGGER_SHA=${triggerSha}"
    ]) {

        sh(
            script: '''
                git tag --merged "$TRIGGER_SHA" --sort=-v:refname |
                grep -E "^${COMPONENT}/v[0-9]+\\.[0-9]+\\.[0-9]+-sha\\.[0-9a-fA-F]+$" ||
                true
            ''',
            returnStdout: true
        ).trim()
    }


    /*
     * Hiç release yok.
     *
     * BURADA BAŞKA HİÇBİR KONTROL YOK.
     */
    if (!tags) {
        return 'NONE'
    }


    /*
     * En yeni tag'dan başlayarak geçerli olanı bul.
     */
    for (String tag : tags.split('\n')) {

        tag = tag.trim()

        if (!tag) {
            continue
        }


        def parts = parseTag(
            tag,
            component
        )

        def tagSha = parts[3]

        def tagCommit = getTagCommit(tag)


        /*
         * Tag isminde yazan SHA,
         * tag'ın gösterdiği commit'in başıyla
         * eşleşmeli.
         */
        if (
            tagCommit
                .toLowerCase()
                .startsWith(tagSha.toLowerCase())
        ) {
            return tag
        }
    }


    /*
     * Tag bulundu ama geçerli release tag'ı bulunamadı.
     *
     * Bunu da ilk release kabul ediyoruz.
     */
    return 'NONE'
}


/*
 * ============================================================
 * PARSE TAG
 * ============================================================
 */
def parseTag(String tag, String component) {

    def prefix = "${component}/v"
    def suffix = '-sha.'

    if (
        !tag.startsWith(prefix) ||
        !tag.contains(suffix)
    ) {
        error("Geçersiz tag: ${tag}")
    }


    def value = tag.substring(
        prefix.length()
    )

    def index = value.indexOf(suffix)

    if (index < 0) {
        error("Geçersiz tag: ${tag}")
    }


    def version = value.substring(
        0,
        index
    )

    def sha = value.substring(
        index + suffix.length()
    )

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


/*
 * ============================================================
 * GET TAG COMMIT
 * ============================================================
 */
def getTagCommit(String tag) {

    if (
        !tag ||
        tag == 'NONE'
    ) {
        error("Commit alınacak geçerli tag yok: ${tag}")
    }


    return withEnv([
        "RELEASE_TAG=${tag}"
    ]) {

        sh(
            script: '''
                set -e

                git rev-list \
                    -n 1 \
                    "$RELEASE_TAG"
            ''',
            returnStdout: true
        ).trim()
    }
}


/*
 * ============================================================
 * GIT DIFF
 * ============================================================
 *
 * Bu fonksiyon SADECE daha önce release yapılmış
 * component'lerde kullanılır.
 *
 * İlk release'de BU FONKSİYON ÇAĞRILMAZ.
 */
def gitDiffExists(
    String oldCommit,
    String newCommit,
    String componentPath
) {

    if (!oldCommit) {
        error(
            "Diff için eski commit bulunamadı: " +
            componentPath
        )
    }


    def result = withEnv([
        "OLD_COMMIT=${oldCommit}",
        "NEW_COMMIT=${newCommit}",
        "COMPONENT_PATH=${componentPath}"
    ]) {

        sh(
            script: '''
                git diff --quiet \
                    "$OLD_COMMIT" \
                    "$NEW_COMMIT" \
                    -- \
                    "$COMPONENT_PATH"
            ''',
            returnStatus: true
        )
    }


    /*
     * git diff --quiet:
     *
     * 0 = değişiklik yok
     * 1 = değişiklik var
     * diğer = hata
     */

    if (result == 0) {
        return false
    }

    if (result == 1) {
        return true
    }


    error(
        "Git diff failed: ${componentPath}"
    )
}


/*
 * ============================================================
 * DOCKER HUB / GITHUB RELEASE CHECK
 * ============================================================
 */
def checkDockerImage(
    String image,
    String version,
    String sha,
    String githubTag,
    String triggerSha
) {

    /*
     * GitHub'da bu release tag'ı var mı?
     */
    def remoteTagOutput = withEnv([
        "TAG_TO_CHECK=${githubTag}"
    ]) {

        sh(
            script: '''
                set -e

                git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                    ls-remote \
                    --tags \
                    origin \
                    "refs/tags/$TAG_TO_CHECK" \
                    "refs/tags/$TAG_TO_CHECK^{}"
            ''',
            returnStdout: true
        ).trim()
    }


    def remoteTagCommit = ''


    if (remoteTagOutput) {

        remoteTagCommit = withEnv([
            "REMOTE_TAG_OUTPUT=${remoteTagOutput}",
            "EXPECTED_TAG=${githubTag}"
        ]) {

            sh(
                script: '''
                    printf '%s\\n' "$REMOTE_TAG_OUTPUT" |
                    awk \
                        -v tag="$EXPECTED_TAG" \
                        '$2 == "refs/tags/" tag "^{}" {
                            print $1
                            exit
                        }'
                ''',
                returnStdout: true
            ).trim()
        }


        if (!remoteTagCommit) {

            remoteTagCommit = withEnv([
                "REMOTE_TAG_OUTPUT=${remoteTagOutput}",
                "EXPECTED_TAG=${githubTag}"
            ]) {

                sh(
                    script: '''
                        printf '%s\\n' "$REMOTE_TAG_OUTPUT" |
                        awk \
                            -v tag="$EXPECTED_TAG" \
                            '$2 == "refs/tags/" tag {
                                print $1
                                exit
                            }'
                    ''',
                    returnStdout: true
                ).trim()
            }
        }


        if (!remoteTagCommit) {
            error(
                "GitHub tag commit alınamadı: " +
                githubTag
            )
        }


        if (
            !remoteTagCommit.equalsIgnoreCase(
                triggerSha
            )
        ) {
            error(
                "GitHub tag yanlış commit'i gösteriyor: " +
                githubTag
            )
        }
    }


    /*
     * Docker version tag var mı?
     */
    def versionExists = withEnv([
        "IMAGE=${image}",
        "VERSION=${version}"
    ]) {

        sh(
            script: '''
                docker manifest inspect \
                    "$IMAGE:v$VERSION" \
                    >/dev/null 2>&1
            ''',
            returnStatus: true
        ) == 0
    }


    /*
     * Ne Docker image var ne GitHub tag var:
     *
     * BUILD
     */
    if (
        !versionExists &&
        !remoteTagOutput
    ) {
        return 'BUILD'
    }


    /*
     * GitHub tag var ama Docker image yok.
     */
    if (
        !versionExists &&
        remoteTagOutput
    ) {
        error(
            "GitHub tag var fakat Docker image yok: " +
            "${image}:v${version}"
        )
    }


    /*
     * Docker version image digest.
     */
    def versionDigest = withEnv([
        "IMAGE=${image}",
        "VERSION=${version}"
    ]) {

        sh(
            script: '''
                set -e

                docker buildx imagetools inspect \
                    "$IMAGE:v$VERSION" |
                grep -m 1 '^Digest:' |
                awk '{print $2}'
            ''',
            returnStdout: true
        ).trim()
    }


    if (!versionDigest) {
        error(
            "Docker image digest alınamadı: " +
            "${image}:v${version}"
        )
    }


    /*
     * Docker SHA image digest.
     */
    def shaDigest = withEnv([
        "IMAGE=${image}",
        "SHA=${sha}"
    ]) {

        sh(
            script: '''
                docker buildx imagetools inspect \
                    "$IMAGE:sha-$SHA" \
                    2>/dev/null |
                grep -m 1 '^Digest:' |
                awk '{print $2}' ||
                true
            ''',
            returnStdout: true
        ).trim()
    }


    if (!shaDigest) {
        error(
            "Version image var fakat SHA image yok: " +
            "${image}:sha-${sha}"
        )
    }


    if (versionDigest != shaDigest) {
        error(
            "Digest uyuşmazlığı: " +
            "${image}:v${version}"
        )
    }


    /*
     * İkisi de mevcut ve aynı.
     * Daha önce release yapılmış.
     */
    if (remoteTagOutput) {
        return 'SKIP'
    }


    /*
     * Docker image var ama GitHub tag yok.
     */
    error(
        "Docker image var fakat GitHub tag yok: " +
        githubTag
    )
}
