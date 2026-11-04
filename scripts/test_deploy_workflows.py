from pathlib import Path

import pytest
import yaml

WORKFLOWS = Path(__file__).parents[1] / ".github/workflows"
REQUIRED_CONDITIONS = (
    "github.event.workflow_run.event == 'push'",
    "github.event.workflow_run.head_repository.full_name == github.repository",
)


def workflow_run_jobs():
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = yaml.safe_load(path.read_text())
        # YAML 1.1 reads the bare key "on" as true.
        triggers = workflow.get("on", workflow.get(True)) or {}
        if "workflow_run" in triggers:
            for name, job in workflow["jobs"].items():
                yield pytest.param(job, id=f"{path.name}:{name}")


def test_a_workflow_run_deployment_exists():
    assert list(workflow_run_jobs())


@pytest.mark.parametrize("job", list(workflow_run_jobs()))
def test_workflow_run_jobs_only_run_for_pushes_to_this_repository(job):
    condition = " ".join(str(job.get("if", "")).split())
    for required in REQUIRED_CONDITIONS:
        assert required in condition


def load_workflow(name):
    workflow = yaml.safe_load((WORKFLOWS / name).read_text())
    return workflow, workflow.get("on", workflow.get(True))


def test_production_release_is_manual_and_gated_before_any_other_job():
    workflow, triggers = load_workflow("deploy-production.yml")
    assert set(triggers) == {"workflow_dispatch"}
    assert {"release_sha", "confirmation"} <= set(triggers["workflow_dispatch"]["inputs"])
    jobs = workflow["jobs"]
    assert "needs" not in jobs["authorize"]
    assert jobs["verify"]["needs"] == "authorize"
    assert jobs["release"]["needs"] == "verify"
    gate = jobs["authorize"]["steps"][0]["run"]
    for check in ("$ACTOR", "$TRIGGERING_ACTOR", "refs/heads/main", "$RELEASE_SHA", "deploy production"):
        assert check in gate


@pytest.mark.parametrize("name", ["deploy-production.yml", "deploy-staging.yml"])
def test_releases_import_all_content_that_readiness_requires(name):
    source = (WORKFLOWS / name).read_text()
    for command in (
        "catalogue-import-db",
        "course-import-db",
        "english-import-db",
        "diagnostic-import-db",
    ):
        assert source.count(f"question-bank {command}") == 2
