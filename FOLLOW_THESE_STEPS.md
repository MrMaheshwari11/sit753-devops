# SIT753 7.3HD — Exact start-to-finish checklist

This is for a **local demonstration** on a Mac or Ubuntu terminal (including Windows WSL2). Run all shell commands in **one terminal environment**: don't run Jenkins on Windows while Docker and Python are only available inside WSL2.

## A — Application first
1. Extract the ZIP. Rename the extracted folder as desired. Open it in VS Code.
2. In the terminal, cd into the folder containing app.py and Jenkinsfile.
3. `python3 -m venv .venv` then `. .venv/bin/activate`.
4. `python -m pip install -r requirements.txt -r requirements-dev.txt`.
5. `python -m pytest -q --cov=app --cov=monitoring`; fix errors.
6. `ruff check app.py monitoring.py tests/`; fix lint issues.
7. `python app.py`, open http://127.0.0.1:5000 and exercise prediction and watchlist. Press Ctrl+C.
8. Start Docker Desktop. `docker build -t sit753-stock-trend-lab:local .`
9. `docker run --rm -p 5000:5000 sit753-stock-trend-lab:local`. Open http://localhost:5000/health and `/metrics`, then Ctrl+C.

## B — GitHub and Docker Hub
10. Create a new empty GitHub repository called `sit753-devops` (do not auto-create README when Git files are already present).
11. Run `git init`, `git add .`, `git commit -m "Add Flask app and full Jenkins pipeline"`, `git branch -M main`, `git remote add origin https://github.com/YOUR_GITHUB_USERNAME/sit753-devops.git`, `git push -u origin main`. Authenticate in your Git credential manager or GitHub CLI.
12. In Docker Hub create a PUBLIC repository `sit753-stock-trend-lab`. Create a Docker Hub access token, and save it privately.
13. Edit `Jenkinsfile`, replacing `YOUR_DOCKERHUB_USERNAME` with the Docker Hub username (not GitHub username unless the same). Commit and push.

## C — Jenkins and SonarQube
14. Install Java 21 (or 25), Python 3, Git, and Docker CLI into the OS account where Jenkins runs.
15. Download `jenkins.war` from https://get.jenkins.io/war-stable/latest/jenkins.war. Run `java -jar jenkins.war --httpPort=8085`, leaving the terminal open. Open http://localhost:8085.
16. Unlock with the initial password shown in Jenkins console / `~/.jenkins/secrets/initialAdminPassword`. Install suggested plugins. Create admin account.
17. Install Jenkins plugins if missing: Git, Pipeline, Credentials Binding, JUnit, SonarQube Scanner.
18. `docker run -d --name sit753-sonarqube -p 9000:9000 -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true sonarqube:community`. Open http://localhost:9000 (admin/admin initially). Change password, create project key `sit753-stock-trend-lab`, generate token.
19. Jenkins > Manage Jenkins > Credentials > System > Global: add Sonar token as **Secret text** ID `sonarqube-token`; add Docker Hub username and ACCESS TOKEN as **Username with password** ID `dockerhub-creds`.
20. Jenkins > Manage Jenkins > System > SonarQube servers: configure name `SonarQube`, URL `http://localhost:9000`, use `sonarqube-token`.
21. Jenkins > Manage Jenkins > Tools > SonarQube Scanner: add auto-installed scanner named exactly `SonarScanner`.
22. SonarQube > Administration > Configuration > Webhooks (may be project settings): URL `http://host.docker.internal:8085/sonarqube-webhook/`. Preserve the trailing slash. Confirm delivery from SonarQube.
23. Jenkins > Manage Jenkins > Nodes: ensure the local built-in agent can run one executor for this lab. Jenkins itself must run under an account able to execute `docker ps` and `python3`. Never enable anonymous admin access.

## D — Run the pipeline
24. Jenkins > New Item > Pipeline, name `sit753-devops` > Definition `Pipeline script from SCM` > Git > Repository URL your GitHub repo > Branch specifier `*/main` > Script Path `Jenkinsfile` > Save.
25. Set Poll SCM trigger `H/5 * * * *` for automatic code-change detection while Jenkins is running locally.
26. Click **Build Now**, open build > Console Output / Stage View. Expect seven named stages. If Sonar or security finds genuine problems, fix them and commit/push. If Deployment and later stages are skipped, verify Git checkout is `main` and `GIT_BRANCH` is set.
27. Confirm green Build, Test, Code Quality, Security, Deployment, Release, Monitoring. Verify reports and registry version tag.

## E — Monitoring incident simulation
28. Open http://localhost:8080 for production, :8081 for staging, :9090 for Prometheus Targets, :9093 for Alertmanager, :8025 for Mailpit (test alert inbox).
29. Check Prometheus target stock-app is UP. Query `up{job="stock-app"}` equals 1.
30. Run `docker stop sit753-stock-app`. Let Prometheus evaluate the StockAppDown alert and Alertmanager deliver a message to Mailpit. Capture both.
31. Run `docker start sit753-stock-app`; ensure target returns to UP; capture recovery.

## F — Evidence and submission
32. Screenshots: GitHub project, Jenkins 7-green-stage overview, Build Docker tag, Test JUnit + coverage, SonarQube quality gate, Bandit/pip-audit/Trivy results, staging site, Docker Hub tagged image, production site, Prometheus UP, firing alert and Mailpit email. No invented screenshots.
33. Record a narrated screen video **no more than 10 minutes**. Demonstrate repo checkout/setup, progression through all seven stages, real working app, and an alert simulation. Upload to a platform your marker can view.
34. Open the supplied answer-sheet template or the provided draft. Enter real GitHub and video URLs, count stages actually working, insert Jenkins screenshot, stage details, actual security analysis. Export PDF.
35. Ensure **both marker and unit chair** have access to GitHub + video, and submit PDF before deadline. Review task instructions about limited submissions.

## Expected endpoints
| Item | URL |
|---|---|
| Jenkins | http://localhost:8085 |
| SonarQube | http://localhost:9000 |
| Staging | http://localhost:8081 |
| Production | http://localhost:8080 |
| Health | http://localhost:8080/health |
| Metrics | http://localhost:8080/metrics |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |
| Test alert mailbox | http://localhost:8025 |

**Important limitations:** This is a new educational moving-average Stock Trend Lab, not your previous LSTM stock predictor. The app/server Jenkins/Trivy/Sonar services have not been deployed remotely by the assistant. Locally, all pipeline results and vulnerability explanations must be verified by you. Mailpit emails are delivered to a TEST inbox and not a real external team.
