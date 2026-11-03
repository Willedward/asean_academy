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
