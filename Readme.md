# GitHub Actions: Galaxy integration tests

The `Galaxy integration tests` workflow starts the official Galaxy Docker image,
waits for its API to respond, runs the Playwright/pytest suite, generates an
Allure HTML report, and uploads the report and raw results as a workflow artifact.

Before running the workflow, configure these repository Actions values under
**Settings > Secrets and variables > Actions**:

- `GALAXY_TEST_USERNAME`: repository variable containing the Galaxy public
  username to create for the test (for example, `admin`).
- `GALAXY_TEST_PASSWORD`: repository secret containing the test user's password.

The workflow uses `quay.io/bgruening/galaxy:latest` and maps its port 80 to
`localhost:8080`, matching the test configuration. It creates a disposable
Galaxy admin account at container startup using those secrets and the email
`admin@galaxy.org`. This image's documented default credentials are `admin` /
`password`; using Actions secrets lets the workflow set a non-default password.
Pull requests from forks do not receive repository secrets, so the login test
cannot authenticate in those runs unless the workflow is configured with a
safe non-secret test credential fallback.

After a workflow run, download the `allure-report` artifact from the run's
**Artifacts** section. Extract it and open
`reports/allure-html-report/index.html` in a browser. The raw Allure results
are included in the same artifact.

The browser runs headlessly in CI. To see it while running tests locally, pass
`--headed` to pytest.