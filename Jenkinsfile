pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    environment {
        BACKEND_IMAGE  = 'volkandemirors/todo-backend'
        FRONTEND_IMAGE = 'volkandemirors/todo-frontend'

        BACKEND_CHANGED  = 'false'
        FRONTEND_CHANGED = 'false'

        BACKEND_SKIP  = 'false'
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

                    env.BACKEND_BASE_TAG =
                        findLatestValidTag(
                            'backend',
                            env.TRIGGER_SHA
                        )


                    env.BACKEND_BASE_COMMIT =
                        getTagCommit(
                            env.BACKEND_BASE_TAG
                        )


                    env.BACKEND_CHANGED =
                        gitDiffExists(
                            env.BACKEND_BASE_COMMIT,
                            env.TRIGGER_SHA,
                            'backend/'
                        ) ? 'true' : 'false'


                    echo """
                    ============================
                    BACKEND CHANGE CHECK
                    ============================

                    Base tag         : ${env.BACKEND_BASE_TAG}
                    Base commit      : ${env.BACKEND_BASE_COMMIT}
                    Trigger commit   : ${env.TRIGGER_SHA}
                    Changed          : ${env.BACKEND_CHANGED}
                    """


                    env.FRONTEND_BASE_TAG =
                        findLatestValidTag(
                            'frontend',
                            env.TRIGGER_SHA
                        )


                    env.FRONTEND_BASE_COMMIT =
                        getTagCommit(
                            env.FRONTEND_BASE_TAG
                        )


                    env.FRONTEND_CHANGED =
                        gitDiffExists(
                            env.FRONTEND_BASE_COMMIT,
                            env.TRIGGER_SHA,
                            'frontend/'
                        ) ? 'true' : 'false'


                    echo """
                    ============================
                    FRONTEND CHANGE CHECK
                    ============================

                    Base tag         : ${env.FRONTEND_BASE_TAG}
                    Base commit      : ${env.FRONTEND_BASE_COMMIT}
                    Trigger commit   : ${env.TRIGGER_SHA}
                    Changed          : ${env.FRONTEND_CHANGED}
                    """


                    if (
                        env.BACKEND_CHANGED == 'false' &&
                        env.FRONTEND_CHANGED == 'false'
                    ) {

                        currentBuild.result = 'NOT_BUILT'

                        error(
                            'Son release taglerinden beri backend veya frontend içeriğinde değişiklik yok.'
                        )
                    }
                }
            }
        }


        stage('Calculate Versions') {
            steps {
                script {

                    def versionType = 'patch'


                    if (env.COMMIT_MESSAGE =~ /(?m)^feat!:/) {
                        versionType = 'major'
                    }
                    else if (env.COMMIT_MESSAGE =~ /(?m)^feat:/) {
                        versionType = 'minor'
                    }
                    else if (env.COMMIT_MESSAGE =~ /(?m)^fix:/) {
                        versionType = 'patch'
                    }


                    echo "Version değişikliği: ${versionType}"


                    if (env.BACKEND_CHANGED == 'true') {

                        def backendTag = env.BACKEND_BASE_TAG

                        def matcher = backendTag =~
                            /^backend\/v([0-9]+)\.([0-9]+)\.([0-9]+)-sha\.([0-9a-fA-F]+)$/


                        if (!matcher.matches()) {
                            error(
                                "Geçersiz backend base tag formatı: ${backendTag}"
                            )
                        }


                        int major = matcher[0][1] as int
                        int minor = matcher[0][2] as int
                        int patch = matcher[0][3] as int


                        if (versionType == 'major') {
                            major++
                            minor = 0
                            patch = 0
                        }
                        else if (versionType == 'minor') {
                            minor++
                            patch = 0
                        }
                        else {
                            patch++
                        }


                        env.BACKEND_VERSION =
                            "${major}.${minor}.${patch}"


                        env.BACKEND_TAG =
                            "backend/v${env.BACKEND_VERSION}-sha.${env.SHORT_SHA}"


                        echo """
                        BACKEND VERSION

                        Base    : ${backendTag}
                        Version : ${env.BACKEND_VERSION}
                        Tag     : ${env.BACKEND_TAG}
                        """
                    }


                    if (env.FRONTEND_CHANGED == 'true') {

                        def frontendTag = env.FRONTEND_BASE_TAG

                        def matcher = frontendTag =~
                            /^frontend\/v([0-9]+)\.([0-9]+)\.([0-9]+)-sha\.([0-9a-fA-F]+)$/


                        if (!matcher.matches()) {
                            error(
                                "Geçersiz frontend base tag formatı: ${frontendTag}"
                            )
                        }


                        int major = matcher[0][1] as int
                        int minor = matcher[0][2] as int
                        int patch = matcher[0][3] as int


                        if (versionType == 'major') {
                            major++
                            minor = 0
                            patch = 0
                        }
                        else if (versionType == 'minor') {
                            minor++
                            patch = 0
                        }
                        else {
                            patch++
                        }


                        env.FRONTEND_VERSION =
                            "${major}.${minor}.${patch}"


                        env.FRONTEND_TAG =
                            "frontend/v${env.FRONTEND_VERSION}-sha.${env.SHORT_SHA}"


                        echo """
                        FRONTEND VERSION

                        Base    : ${frontendTag}
                        Version : ${env.FRONTEND_VERSION}
                        Tag     : ${env.FRONTEND_TAG}
                        """
                    }
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

                            def result = checkDockerImage(
                                env.BACKEND_IMAGE,
                                env.BACKEND_VERSION,
                                env.SHORT_SHA,
                                env.BACKEND_TAG,
                                env.TRIGGER_SHA
                            )


                            if (result == 'SKIP') {
                                env.BACKEND_SKIP = 'true'
                            }
                        }


                        if (
                            env.FRONTEND_CHANGED == 'true' &&
                            env.FRONTEND_SKIP != 'true'
                        ) {

                            def result = checkDockerImage(
                                env.FRONTEND_IMAGE,
                                env.FRONTEND_VERSION,
                                env.SHORT_SHA,
                                env.FRONTEND_TAG,
                                env.TRIGGER_SHA
                            )


                            if (result == 'SKIP') {
                                env.FRONTEND_SKIP = 'true'
                            }
                        }


                        echo "Backend skip : ${env.BACKEND_SKIP}"
                        echo "Frontend skip: ${env.FRONTEND_SKIP}"
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

                        sh """
                            set -e

                            docker build \
                                -t ${BACKEND_IMAGE}:v${BACKEND_VERSION} \
                                -t ${BACKEND_IMAGE}:sha-${SHORT_SHA} \
                                ./backend
                        """
                    }


                    if (
                        env.FRONTEND_CHANGED == 'true' &&
                        env.FRONTEND_SKIP != 'true'
                    ) {

                        sh """
                            set -e

                            docker build \
                                -t ${FRONTEND_IMAGE}:v${FRONTEND_VERSION} \
                                -t ${FRONTEND_IMAGE}:sha-${SHORT_SHA} \
                                ./frontend
                        """
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

                        sh """
                            set -e

                            docker push \
                                ${BACKEND_IMAGE}:v${BACKEND_VERSION}

                            docker push \
                                ${BACKEND_IMAGE}:sha-${SHORT_SHA}
                        """
                    }


                    if (
                        env.FRONTEND_CHANGED == 'true' &&
                        env.FRONTEND_SKIP != 'true'
                    ) {

                        sh """
                            set -e

                            docker push \
                                ${FRONTEND_IMAGE}:v${FRONTEND_VERSION}

                            docker push \
                                ${FRONTEND_IMAGE}:sha-${SHORT_SHA}
                        """
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

                            sh '''
                                set -e
                                set +x

                                git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                                    tag -a "$BACKEND_TAG" \
                                    "$TRIGGER_SHA" \
                                    -m "Release $BACKEND_TAG"

                                git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                                    push origin "$BACKEND_TAG"
                            '''
                        }


                        if (
                            env.FRONTEND_CHANGED == 'true' &&
                            env.FRONTEND_SKIP != 'true'
                        ) {

                            sh '''
                                set -e
                                set +x

                                git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                                    tag -a "$FRONTEND_TAG" \
                                    "$TRIGGER_SHA" \
                                    -m "Release $FRONTEND_TAG"

                                git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                                    push origin "$FRONTEND_TAG"
                            '''
                        }
                    }
                }
            }
        }
    }


    post {

        success {
            echo 'GitHub → Jenkins → Docker → Docker Hub → GitHub Tag başarılı!'
        }

        always {
            sh 'docker logout || true'
        }
    }
}


/*
 * ==================================================================
 * SON GEÇERLİ COMPONENT RELEASE TAG'İNİ BUL
 * ==================================================================
 */
def findLatestValidTag(
    String component,
    String triggerSha
) {

    def tags = sh(
        script: """
            set -e

            git tag \
                --merged '${triggerSha}' \
                --sort=-v:refname |
            grep -E '^${component}/v[0-9]+\\\\.[0-9]+\\\\.[0-9]+-sha\\\\.[0-9a-fA-F]+\\\$' ||
            true
        """,
        returnStdout: true
    ).trim()


    if (!tags) {

        echo """
        ${component} için trigger commit'in
        geçmişinde release tag bulunamadı.

        İlk release kabul edilecek.
        """

        return "${component}/v0.0.0-sha.0000000"
    }


    for (String tag : tags.split('\n')) {

        tag = tag.trim()

        if (!tag) {
            continue
        }


        def matcher = tag =~
            /^${component}\/v([0-9]+)\.([0-9]+)\.([0-9]+)-sha\.([0-9a-fA-F]+)$/


        if (!matcher.matches()) {
            continue
        }


        def tagSha =
            matcher[0][4].toLowerCase()


        def tagCommit =
            getTagCommit(tag)


        /*
         * Tag formatındaki SHA gerçekten tag'in
         * işaret ettiği commit'in prefix'i mi?
         */
        if (
            !tagCommit
                .toLowerCase()
                .startsWith(tagSha)
        ) {

            echo """
            Geçersiz ${component} tag atlandı.

            Tag        : ${tag}
            Tag commit : ${tagCommit}
            Tag SHA    : ${tagSha}
            """

            continue
        }


        echo """
        Geçerli ${component} release tag bulundu.

        Tag        : ${tag}
        Tag commit : ${tagCommit}
        Tag SHA    : ${tagSha}
        """


        return tag
    }


    echo """
    ${component} için SHA doğrulamasından geçen
    release tag bulunamadı.

    İlk release kabul edilecek.
    """


    return "${component}/v0.0.0-sha.0000000"
}


/*
 * ==================================================================
 * TAG COMMIT'İNİ BUL
 * ==================================================================
 */
def getTagCommit(String tag) {

    if (tag.endsWith('/v0.0.0-sha.0000000')) {
        return '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    }


    return sh(
        script: """
            set -e
            git rev-list -n 1 '${tag}'
        """,
        returnStdout: true
    ).trim()
}


/*
 * ==================================================================
 * GERÇEK İÇERİK DEĞİŞİKLİĞİ VAR MI?
 * ==================================================================
 */
def gitDiffExists(
    String oldCommit,
    String newCommit,
    String componentPath
) {

    def result = sh(
        script: """
            git diff \
                --quiet \
                '${oldCommit}' \
                '${newCommit}' \
                -- '${componentPath}'
        """,
        returnStatus: true
    )


    if (result == 0) {
        return false
    }


    if (result == 1) {
        return true
    }


    error("""
    Git diff sırasında hata oluştu.

    Component   : ${componentPath}
    Eski commit : ${oldCommit}
    Yeni commit : ${newCommit}
    Exit code   : ${result}
    """)

    return false
}


/*
 * ==================================================================
 * DOCKER HUB + GITHUB RELEASE KONTROLÜ
 * ==================================================================
 */
def checkDockerImage(
    String image,
    String version,
    String sha,
    String githubTag,
    String triggerSha
) {

    /*
     * --------------------------------------------------------------
     * GITHUB TAG KONTROLÜ
     * --------------------------------------------------------------
     */
    def remoteTagOutput = sh(
        script: '''
            set -e
            set +x

            git -c http.extraheader="AUTHORIZATION: Bearer $GITHUB_TOKEN" \
                ls-remote --tags origin \
                "refs/tags/$GITHUB_TAG" \
                "refs/tags/$GITHUB_TAG^{}"
        ''',
        returnStdout: true
    ).trim()


    def remoteTagCommit = ''


    if (remoteTagOutput) {

        remoteTagCommit = sh(
            script: """
                printf '%s\\n' '${remoteTagOutput}' |
                awk '\\$2 == "refs/tags/${githubTag}^{}" {print \\$1; exit}'
            """,
            returnStdout: true
        ).trim()


        /*
         * Lightweight tag fallback.
         */
        if (!remoteTagCommit) {

            remoteTagCommit = sh(
                script: """
                    printf '%s\\n' '${remoteTagOutput}' |
                    awk '\\$2 == "refs/tags/${githubTag}" {print \\$1; exit}'
                """,
                returnStdout: true
            ).trim()
        }


        if (!remoteTagCommit) {

            error("""
            GITHUB TAG CHECK FAILED

            Tag mevcut fakat commit alınamadı:

            ${githubTag}
            """)
        }


        if (
            !remoteTagCommit.equalsIgnoreCase(triggerSha)
        ) {

            error("""
            INCONSISTENT RELEASE

            GitHub tag yanlış commit'i gösteriyor.

            Tag:
            ${githubTag}

            Beklenen:
            ${triggerSha}

            Gerçek:
            ${remoteTagCommit}
            """)
        }
    }


    /*
     * --------------------------------------------------------------
     * VERSION IMAGE VAR MI?
     * --------------------------------------------------------------
     */
    def versionExists = sh(
        script: """
            docker manifest inspect \
                ${image}:v${version} \
                >/dev/null 2>&1
        """,
        returnStatus: true
    ) == 0


    /*
     * --------------------------------------------------------------
     * IMAGE YOK + TAG YOK
     * --------------------------------------------------------------
     */
    if (!versionExists && !remoteTagOutput) {

        echo """
        NORMAL BUILD

        ${image}:v${version}
        Docker Hub'da yok.

        GitHub tag:
        ${githubTag}

        → Build yapılacak.
        """

        return 'BUILD'
    }


    /*
     * --------------------------------------------------------------
     * IMAGE YOK + TAG VAR
     * --------------------------------------------------------------
     *
     * Bu durum normal değildir.
     *
     * GitHub release tag var fakat Docker image yok.
     */
    if (!versionExists && remoteTagOutput) {

        error("""
        INCONSISTENT RELEASE

        GitHub tag mevcut:
        ${githubTag}

        Tag commit:
        ${remoteTagCommit}

        Fakat Docker image mevcut değil:
        ${image}:v${version}

        Release yarım kalmış görünüyor.
        Pipeline durduruldu.
        """)
    }


    /*
     * --------------------------------------------------------------
     * VERSION IMAGE DIGEST
     * --------------------------------------------------------------
     */
    def versionDigest = sh(
        script: """
            docker buildx imagetools inspect \
                ${image}:v${version} |
            grep -m 1 '^Digest:' |
            awk '{print \\$2}'
        """,
        returnStdout: true
    ).trim()


    if (!versionDigest) {

        error("""
        VERSION CHECK FAILED

        ${image}:v${version} mevcut fakat
        digest alınamadı.
        """)
    }


    /*
     * --------------------------------------------------------------
     * SHA IMAGE DIGEST
     * --------------------------------------------------------------
     */
    def shaDigest = sh(
        script: """
            docker buildx imagetools inspect \
                ${image}:sha-${sha} 2>/dev/null |
            grep -m 1 '^Digest:' |
            awk '{print \\$2}' ||
            true
        """,
        returnStdout: true
    ).trim()


    /*
     * Version var + SHA yok = yarım release.
     */
    if (!shaDigest) {

        error("""
        VERSION CONFLICT

        ${image}:v${version} mevcut fakat
        ${image}:sha-${sha} bulunamadı.

        Pipeline durduruldu.
        """)
    }


    /*
     * --------------------------------------------------------------
     * DIGEST KARŞILAŞTIR
     * --------------------------------------------------------------
     */
    if (versionDigest != shaDigest) {

        error("""
        VERSION CONFLICT

        ${image}:v${version}
        Digest: ${versionDigest}

        ${image}:sha-${sha}
        Digest: ${shaDigest}

        Aynı version farklı image'lara işaret ediyor.
        Pipeline durduruldu.
        """)
    }


    /*
     * --------------------------------------------------------------
     * HER ŞEY MEVCUT
     * --------------------------------------------------------------
     */
    if (remoteTagOutput) {

        echo """
        RELEASE ZATEN MEVCUT

        Docker image : ${image}:v${version}
        SHA image    : ${image}:sha-${sha}
        GitHub tag   : ${githubTag}
        Tag commit   : ${remoteTagCommit}

        → SKIP
        """

        return 'SKIP'
    }


    /*
     * --------------------------------------------------------------
     * IMAGE VAR AMA TAG YOK
     * --------------------------------------------------------------
     */
    error("""
    INCONSISTENT RELEASE

    Docker image mevcut:

    ${image}:v${version}
    ${image}:sha-${sha}

    Digest aynı:

    ${versionDigest}

    Fakat GitHub tag yok:

    ${githubTag}

    Release yarım kalmış görünüyor.
    Pipeline durduruldu.
    """)
}
