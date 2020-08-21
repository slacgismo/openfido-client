from .models import (
    Pipeline,
    PipelineRun,
    PipelineRunInput,
    PipelineRunState,
    RunState,
    db,
)
from .queries import find_pipeline, find_run_state_type, find_pipeline_run


def delete_pipeline(uuid):
    """ Delete a pipeline.

    Note: The db.session is not committed. Be sure to commit the session.
    """
    pipeline = find_pipeline(uuid)
    if pipeline is None:
        raise ValueError("no pipeline found")

    pipeline.is_deleted = True


def create_pipeline(
    name, description, docker_image_url, repository_ssh_url, repository_branch
):
    """ Create a Pipeline.

    Note: The db.session is not committed. Be sure to commit the session.
    """
    if len(name) == 0 or len(description) == 0:
        raise ValueError("name and description must be supplied.")
    if len(docker_image_url) == 0:
        raise ValueError("A docker image URL must be supplied.")
    if len(repository_ssh_url) == 0 or len(repository_branch) == 0:
        raise ValueError("A ssh URL must be supplied.")

    pipeline = Pipeline(
        name=name,
        description=description,
        docker_image_url=docker_image_url,
        repository_ssh_url=repository_ssh_url,
        repository_branch=repository_branch,
    )
    db.session.add(pipeline)

    return pipeline


def create_pipeline_run_state(run_state):
    run_state_type = find_run_state_type(run_state)
    pipeline_run_state = PipelineRunState(
        name=run_state_type.name,
        description=run_state_type.description,
        code=run_state_type.code,
    )
    run_state_type.pipeline_run_states.append(pipeline_run_state)

    return pipeline_run_state


def create_pipeline_run(uuid, inputs):
    """ Create a new PipelineRun for a Pipeline's uuid """
    pipeline = find_pipeline(uuid)
    if pipeline is None:
        raise ValueError("no pipeline found")

    sequence = len(pipeline.pipeline_runs) + 1
    pipeline_run = PipelineRun(sequence=sequence)

    for i in inputs:
        pipeline_run.pipeline_run_inputs.append(
            PipelineRunInput(filename=i["name"], url=i["url"])
        )

    pipeline_run.pipeline_run_states.append(
        create_pipeline_run_state(RunState.NOT_STARTED)
    )
    pipeline.pipeline_runs.append(pipeline_run)
    db.session.add(pipeline)

    return pipeline_run


def update_pipeline_run_output(uuid, std_out, std_err):
    pipeline_run = find_pipeline_run(uuid)
    if pipeline_run is None:
        raise ValueError("pipeline run not found")

    pipeline_run.std_out = std_out
    pipeline_run.std_err = std_err
