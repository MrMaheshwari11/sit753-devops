# SIT753 7.3HD — Stock Trend Lab / Jenkins DevOps Demonstration

**Important:** This repository is a complete self-contained DEMO application, not the user's historical ML forecasting model. It calculates a simple moving-average forecast from user-supplied data and has a real SQLite-backed watchlist API. It is educational; it uses no live feeds or securities credentials.

## Features
- Interactive HTML dashboard with two working features
- `POST /api/predict` validates prices and calculates a forecast
- `GET`, `POST`, `DELETE /api/watchlist` with SQLite persistence
- `GET /health` for health checks
- `GET /metrics` for Prometheus monitoring
- Unit/API integration tests and container smoke test

## 1. Local test (Mac or Ubuntu / Windows WSL2)

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
pytest -q --cov=app --cov=monitoring
ruff check app.py monitoring.py tests/
python app.py
```
Open http://127.0.0.1:5000, click the prediction button and add a stock to the watchlist. Stop using Ctrl+C.

## 2. Docker

```bash
docker build -t sit753-stock-trend-lab:local .
docker run --rm --name sit753-local -p 5000:5000 sit753-stock-trend-lab:local
```
Open http://localhost:5000, http://localhost:5000/health and http://localhost:5000/metrics. Stop using Ctrl+C.

## 3. GitHub
Create a repository named `sit753-devops`, copy this entire folder into it, then:

```bash
git init
git add .
git commit -m "Complete stock trend lab and Jenkins pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/sit753-devops.git
git push -u origin main
```
You will need GitHub authentication (GitHub CLI or a Git credential manager).

## 4. Services: Jenkins and SonarQube
- Jenkins runs as the local user on Mac or Ubuntu WSL2, **not inside an unconfigured Jenkins container**. This allows local `docker`, `python3`, and `sh` commands to work.
- Install Java 21; start Jenkins using a recent LTS `jenkins.war`: `java -jar jenkins.war --httpPort=8085`.
- Run SonarQube with:

```bash
docker run -d --name sit753-sonarqube -p 9000:9000 \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true sonarqube:community
```
- In SonarQube at http://localhost:9000, create project with key `sit753-stock-trend-lab` and generate a token.
- Install Jenkins plugins: Pipeline, Git, Credentials Binding, SonarQube Scanner, Workspace Cleanup (optional), JUnit (usually bundled).
- Jenkins > Manage Jenkins > Credentials: add Sonar token as Secret text (`sonarqube-token`) and Docker Hub **access token** as Username with password (`dockerhub-creds`).
- Jenkins > Manage Jenkins > System > SonarQube servers: name `SonarQube`, URL `http://localhost:9000`, credentials `sonarqube-token`.
- Jenkins > Manage Jenkins > Tools > SonarQube Scanner: add scanner named `SonarScanner`, choose automatic installation.
- SonarQube > Administration > Configuration > Webhooks: add `http://host.docker.internal:8085/sonarqube-webhook/` including trailing slash. Jenkins plugin requires it for the quality gate callback.
- Set meaningful SonarQube quality conditions for new code, and confirm green Quality Gate.

## 5. Jenkins job
- Edit Jenkinsfile `IMAGE_REPO` to `YOUR_DOCKERHUB_USERNAME/sit753-stock-trend-lab` (create that public Docker Hub repository first).
- Push the edit to GitHub.
- Jenkins > New Item > Pipeline > `sit753-devops`.
- Definition `Pipeline script from SCM`, SCM `Git`, Repository URL your GitHub URL, branch `*/main`, Script Path `Jenkinsfile`.
- The Jenkins user running the job must have Docker and Python available on `PATH`.
- In Build Triggers, enable `Poll SCM` with `H/5 * * * *` to demonstrate automatic change detection even though local Jenkins cannot receive public GitHub webhooks.
- Run **Build Now**; inspect Console Output and Pipeline Stage View. Fix real failures and rerun.

## 6. Expected localhost endpoints
| Service | URL |
| --- | --- |
| Jenkins | http://localhost:8085 |
| SonarQube | http://localhost:9000 |
| Staging | http://localhost:8081 |
| Production | http://localhost:8080 |
| Production health | http://localhost:8080/health |
| Production metrics | http://localhost:8080/metrics |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |
| Mailpit (test alert inbox) | http://localhost:8025 |

## 7. Incident simulation
After Jenkins succeeds:

```bash
docker stop sit753-stock-app
```

Check Prometheus > Alerts for `StockAppDown` and Mailpit at http://localhost:8025 for the email notification to **demo mailbox** `devops-team@sit753.local`. This is a local test sink, **not** a real email delivered to a team member. Capture screenshots. Restore:

```bash
docker start sit753-stock-app
```

Wait for the Prometheus target to become UP, capture recovery evidence, and rerun the pipeline if needed.

## 8. If production is broken
Docker Hub contains version tags such as `1.0.1`. To roll back in the Jenkins shell environment, set IMAGE_TAG to your previous successful version and re-run the production Compose command after setting CONFIG_DIR and IMAGE_REPO. The Jenkinsfile also attempts automatic rollback if production health fails and a previous known-good version exists.

## 9. Evidence and submission
Screenshots: GitHub repo and Jenkinsfile, Jenkins all-seven-green stages, JUnit coverage, Sonar quality gate, security scan reports, staging and production running, Docker Hub version, Prometheus target, fired alert, Mailpit notification. Record a demo video <= 10 minutes, add video and GitHub links to the supplied answer sheet, then export PDF. Give both the marker and Unit Chair access.

## Limitations / academic honesty
- Do not claim this is your old LSTM model; the project is deliberately a self-contained stock trend lab.
- Do not claim any Jenkins stage was run unless you execute it and collect evidence.
- Do not claim Mailpit delivers email to real people; it displays a test alert in a local inbox.
- `pip-audit` and Trivy may flag current CVEs; investigate and remediate or explain findings and mitigation in the report. Never suppress findings solely to make the pipeline green.
- Jenkins controller builds are appropriate for this controlled local lab; production CI should use dedicated agents and secured infrastructure.
