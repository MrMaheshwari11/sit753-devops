# Demonstration video plan (maximum 10 minutes)

| Time | What to show | What to explain |
| --- | --- | --- |
| 0:00–0:45 | GitHub repository, README, Jenkinsfile | Source-controlled pipeline and application features |
| 0:45–1:30 | Jenkins job configured from SCM | How pipeline checks out GitHub project |
| 1:30–2:15 | Build stage + Docker image tag | Build artefact and versioning |
| 2:15–3:00 | Pytest JUnit results + `/health` smoke | Unit/API tests and deployable artefact check |
| 3:00–3:50 | SonarQube quality gate and ruff | Code maintainability; gate enforcement |
| 3:50–4:40 | Bandit, pip-audit, Trivy reports | Security severity, findings and what was fixed |
| 4:40–5:30 | Staging port 8081, app predictor | Test deployment and staging verification |
| 5:30–6:20 | Docker Hub version tag, production port 8080 | Release uses versioned artefact |
| 6:20–8:30 | Prometheus target UP, stop app, fire alert, Mailpit inbox | Production monitoring, alert and incident simulation |
| 8:30–9:15 | Restart app, monitoring target UP | Recovery and limitations |
| 9:15–9:45 | Jenkins stage overview, final conclusion | All seven stages and evidence summary |

**Tip:** Trigger the Jenkins job before recording or cut out installation delays; do not fake output or imply a pre-recorded pipeline was the current run. If you prepare screenshots, show the real build number and logs.
