pipeline {
    agent any
    options {
        timestamps()
        disableConcurrentBuilds()
    }
    environment {
        IMAGE_REPO = 'mrmaheshwari11/sit753-stock-trend-lab'
        VERSION = "1.0.${BUILD_NUMBER}"
    }
    stages {
        stage('Build') {
            steps {
                sh '''
                    set -eu
                    mkdir -p reports
                    docker build --pull -t "$IMAGE_REPO:$VERSION" .
                    docker image inspect "$IMAGE_REPO:$VERSION" > reports/image-inspect.json
                    printf 'Image: %s\nGit commit: %s\n' "$IMAGE_REPO:$VERSION" "${GIT_COMMIT:-unknown}" > reports/build-info.txt
                '''
            }
        }
        stage('Test') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv .jenkins-venv
                    . .jenkins-venv/bin/activate
                    python -m pip install -r requirements.txt -r requirements-dev.txt
                    python -m pytest -q --junitxml=reports/junit.xml --cov=app --cov=monitoring --cov-report=xml:coverage.xml
                    docker rm -f sit753-ci-smoke >/dev/null 2>&1 || true
                    docker run -d --name sit753-ci-smoke -p 18081:5000 "$IMAGE_REPO:$VERSION"
                    trap 'docker rm -f sit753-ci-smoke >/dev/null 2>&1 || true' EXIT
                    success=0
                    for i in $(seq 1 30); do
                        if curl -fsS http://127.0.0.1:18081/health; then success=1; break; fi
                        sleep 2
                    done
                    test "$success" -eq 1
                '''
            }
        }
        stage('Code Quality') {
            steps {
                sh '''
                    set -eu
                    . .jenkins-venv/bin/activate
                    ruff check app.py monitoring.py tests/ > reports/ruff.txt 2>&1
                '''
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('SonarQube') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
        stage('Security') {
            steps {
                sh '''
                    set -eu
                    . .jenkins-venv/bin/activate
                    bandit app.py monitoring.py -f txt -o reports/bandit.txt
                    pip-audit -r requirements.txt -f json -o reports/pip-audit.json
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                      aquasec/trivy:0.66.0 image --image-src docker \
                      --severity HIGH,CRITICAL --exit-code 1 \
                      "$IMAGE_REPO:$VERSION" > reports/trivy.txt 2>&1
                '''
            }
        }
        stage('Deployment') {
            when {
                expression {
                    (env.BRANCH_NAME ?: env.GIT_BRANCH ?: '').tokenize('/').last() == 'main'
                }
            }
            steps {
                sh '''
                    set -eu
                    export IMAGE_TAG="$VERSION"
                    docker compose -p sit753-staging -f deploy/staging.yml up -d
                    success=0
                    for i in $(seq 1 30); do
                        if curl -fsS http://127.0.0.1:8081/health; then success=1; break; fi
                        sleep 2
                    done
                    test "$success" -eq 1
                '''
            }
        }
        stage('Release') {
            when {
                expression {
                    (env.BRANCH_NAME ?: env.GIT_BRANCH ?: '').tokenize('/').last() == 'main'
                }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        set -eu
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push "$IMAGE_REPO:$VERSION"
                        docker logout
                    '''
                }
                sh '''
                    set -eu
                    export IMAGE_TAG="$VERSION"
                    export CONFIG_DIR="$HOME/.sit753-monitoring"
                    mkdir -p "$CONFIG_DIR"
                    cp prometheus/prometheus.yml prometheus/rules.yml prometheus/alertmanager.yml "$CONFIG_DIR/"
                    if [ -f "$HOME/.sit753-prod-version" ]; then
                        cp "$HOME/.sit753-prod-version" "$HOME/.sit753-prev-version"
                    fi
                    docker compose -p sit753-production -f deploy/production.yml pull
                    docker compose -p sit753-production -f deploy/production.yml up -d
                    success=0
                    for i in $(seq 1 30); do
                        if curl -fsS http://127.0.0.1:8080/health; then success=1; break; fi
                        sleep 2
                    done
                    if [ "$success" -ne 1 ]; then
                        echo 'Production health failed; attempt to roll back to previous release'
                        if [ -f "$HOME/.sit753-prev-version" ]; then
                            export IMAGE_TAG="$(cat "$HOME/.sit753-prev-version")"
                            docker compose -p sit753-production -f deploy/production.yml up -d || true
                        fi
                        exit 1
                    fi
                    printf '%s\n' "$VERSION" > "$HOME/.sit753-prod-version"
                    printf 'Released %s:%s\n' "$IMAGE_REPO" "$VERSION" > reports/release.txt
                '''
            }
        }
        stage('Monitoring') {
            when {
                expression {
                    (env.BRANCH_NAME ?: env.GIT_BRANCH ?: '').tokenize('/').last() == 'main'
                }
            }
            steps {
                sh '''
                    set -eu
                    curl -fsS http://127.0.0.1:8080/health
                    for i in $(seq 1 30); do
                        if curl -fsS http://127.0.0.1:9090/-/ready >/dev/null && \
                           curl -fsS http://127.0.0.1:9093/-/ready >/dev/null && \
                           curl -fsS 'http://127.0.0.1:9090/api/v1/query?query=up%7Bjob%3D%22stock-app%22%7D' | \
                           python3 -c 'import sys,json; r=json.load(sys.stdin)["data"]["result"]; sys.exit(0 if r and r[0]["value"][1]=="1" else 1)'; then
                            echo 'Prometheus and Alertmanager ready; stock-app target UP'
                            exit 0
                        fi
                        sleep 3
                    done
                    echo 'Monitoring readiness or scrape verification failed'
                    exit 1
                '''
            }
        }
    }
    post {
        always {
            junit testResults: 'reports/junit.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'reports/**,coverage.xml', allowEmptyArchive: true, fingerprint: true
            sh 'docker rm -f sit753-ci-smoke >/dev/null 2>&1 || true'
        }
    }
}
