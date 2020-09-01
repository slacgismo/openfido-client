from app.models import Pipeline, db
from app.queries import find_pipeline
from app.services import create_pipeline_run
from app.pipelines import toISO8601


def test_create_pipeline_wrong_content_type(client):
    result = client.post("/v1/pipelines", content_type="application/badtype",)
    assert result.status_code == 400


def test_create_pipeline_no_params(client):
    # An error is returned if no configuration information is supplied.
    result = client.post("/v1/pipelines", content_type="application/json", json={})
    assert result.status_code == 400


def test_create_pipeline_wrong_params(client):
    # An error is returned if no configuration information is supplied.
    params = {
        "wrong": "wrong",
        "name": "a pipeline",
        "description": "a description",
        "docker_image_url": "",
        "repository_ssh_url": "",
        "repository_branch": "",
    }
    result = client.post("/v1/pipelines", content_type="application/json", json=params,)
    assert result.status_code == 400


def test_create_pipeline_non_empty_params(client, client_application):
    db.session.commit()
    # An error is returned if no configuration information is supplied.
    params = {
        "name": "a pipeline",
        "description": "a description",
        "docker_image_url": "",
        "repository_ssh_url": "",
        "repository_branch": "",
    }
    result = client.post(
        "/v1/pipelines",
        content_type="application/json",
        json=params,
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 400


def test_create_pipeline_no_auth(client):
    params = {
        "name": "a pipeline",
        "description": "a description",
        "docker_image_url": "a/url",
        "repository_ssh_url": "ssh+github url",
        "repository_branch": "master",
    }
    result = client.post("/v1/pipelines", content_type="application/json", json=params,)
    assert result.status_code == 401


def test_create_pipeline_wrong_auth(client, worker_application):
    db.session.commit()
    # using an api_key that doesn't have client permissions will fail:
    params = {
        "name": "a pipeline",
        "description": "a description",
        "docker_image_url": "a/url",
        "repository_ssh_url": "ssh+github url",
        "repository_branch": "master",
    }
    result = client.post(
        "/v1/pipelines",
        content_type="application/json",
        json=params,
        headers={"Workflow-Key": worker_application.api_key},
    )
    assert result.status_code == 401


def test_create_pipeline(client, client_application):
    db.session.commit()
    params = {
        "name": "a pipeline",
        "description": "a description",
        "docker_image_url": "a/url",
        "repository_ssh_url": "ssh+github url",
        "repository_branch": "master",
    }
    result = client.post(
        "/v1/pipelines",
        content_type="application/json",
        json=params,
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200

    pipeline = Pipeline.query.filter(Pipeline.name == params["name"]).one_or_none()
    assert pipeline.name == "a pipeline"


def test_list_pipelines(client, client_application):
    db.session.commit()
    result = client.get(
        "/v1/pipelines",
        content_type="application/json",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200
    assert len(result.json) == 0

    p1 = Pipeline(
        name="pipeline 1",
        description="a description",
        docker_image_url="",
        repository_ssh_url="",
        repository_branch="",
    )
    db.session.add(p1)
    p2 = Pipeline(
        name="pipeline 2",
        description="a description",
        docker_image_url="",
        repository_ssh_url="",
        repository_branch="",
    )
    db.session.add(p2)
    db.session.commit()

    result = client.get(
        "/v1/pipelines",
        content_type="application/json",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200
    assert len(result.json) == 2
    assert result.json[0]["name"] == p1.name
    assert result.json[1]["name"] == p2.name


def test_get_pipeline_no_match(client, client_application):
    db.session.commit()
    result = client.get(
        "/v1/pipelines/1111ddddeeee2222",
        content_type="application/json",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 404


def test_get_pipeline(client, pipeline, client_application):
    db.session.commit()
    result = client.get(
        f"/v1/pipelines/{pipeline.uuid}",
        content_type="application/json",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200


def test_remove_pipeline_no_match(client, client_application):
    db.session.commit()
    result = client.delete(
        "/v1/pipelines/1111ddddeeee2222",
        content_type="application/json",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 400


def test_remove_pipeline(client, pipeline, client_application):
    db.session.commit()
    result = client.delete(
        f"/v1/pipelines/{pipeline.uuid}",
        content_type="application/json",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200
    assert find_pipeline(pipeline.uuid) is None


def test_create_run_no_such_uuid(client, client_application):
    db.session.commit()
    result = client.post(
        "/v1/pipelines/1111abcd/runs",
        content_type="application/json",
        json={"inputs": []},
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 400


def test_create_run_bad_input_name(client, pipeline, client_application):
    db.session.commit()
    result = client.post(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        content_type="application/json",
        json={"inputs": [{"name": "name1.pdf"}]},
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 400

    result = client.post(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        content_type="application/json",
        json={"inputs": [{"name": "name1.pdf", "url": "aurl", "extrakey": "badinput"}]},
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 400

    result = client.post(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        content_type="application/json",
        json={"inputs": "[]"},
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 400


def test_create_run(client, pipeline, client_application):
    db.session.commit()
    result = client.post(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        content_type="application/json",
        json={"inputs": [{"name": "name1.pdf", "url": "aurl"}]},
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200
    assert len(pipeline.pipeline_runs) == 1
    assert len(pipeline.pipeline_runs[0].pipeline_run_states) == 1
    assert len(pipeline.pipeline_runs[0].pipeline_run_inputs) == 1
    pipeline_run = pipeline.pipeline_runs[0]

    assert result.json == {
        "uuid": pipeline_run.uuid,
        "sequence": pipeline_run.sequence,
        "created_at": toISO8601(pipeline_run.created_at),
        "inputs": [{"name": "name1.pdf", "url": "aurl",}],
        "states": [
            {
                "state": pipeline_run.pipeline_run_states[0].name,
                "created_at": toISO8601(pipeline_run.pipeline_run_states[0].created_at),
            }
        ],
    }


def test_get_pipeline_run(client, pipeline, client_application):
    db.session.commit()
    result = client.get(
        "/v1/pipelines/no-id/runs/no-id",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 404

    # no such pipeline_run_id
    result = client.get(
        f"/v1/pipelines/{pipeline.uuid}/runs/no-id",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 404

    # successfully fetch a pipeline_run
    pipeline_run = create_pipeline_run(pipeline.uuid, [])
    db.session.commit()
    result = client.get(
        f"/v1/pipelines/{pipeline.uuid}/runs/{pipeline_run.uuid}",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200
    assert result.json == {
        "uuid": pipeline_run.uuid,
        "sequence": pipeline_run.sequence,
        "created_at": toISO8601(pipeline_run.created_at),
        "inputs": [],
        "states": [
            {
                "state": pipeline_run.pipeline_run_states[0].name,
                "created_at": toISO8601(pipeline_run.pipeline_run_states[0].created_at),
            }
        ],
    }

    # fails if the pipeline is deleted.
    pipeline.is_deleted = True
    db.session.commit()
    result = client.get(
        f"/v1/pipelines/{pipeline.uuid}/runs/{pipeline_run.uuid}",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 404


def test_list_pipeline_runs(client, pipeline, client_application):
    db.session.commit()
    result = client.get(
        f"/v1/pipelines/no-id/runs",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 404

    result = client.get(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200
    assert result.json == []

    # successfully fetch a pipeline_run
    pipeline_run = create_pipeline_run(pipeline.uuid, [])
    db.session.commit()
    result = client.get(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200
    assert result.json == [
        {
            "uuid": pipeline_run.uuid,
            "sequence": pipeline_run.sequence,
            "created_at": toISO8601(pipeline_run.created_at),
            "inputs": [],
            "states": [
                {
                    "state": pipeline_run.pipeline_run_states[0].name,
                    "created_at": toISO8601(
                        pipeline_run.pipeline_run_states[0].created_at
                    ),
                }
            ],
        }
    ]


def test_get_pipeline_run_output(client, pipeline, client_application):
    db.session.commit()
    result = client.get(
        "/v1/pipelines/no-id/runs/no-id/console",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 404

    # no such pipeline_run_id
    result = client.get(
        f"/v1/pipelines/{pipeline.uuid}/runs/no-id/console",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 404

    # successfully fetch a pipeline_run
    pipeline_run = create_pipeline_run(pipeline.uuid, [])
    pipeline_run.std_out = "stdout"
    db.session.commit()
    result = client.get(
        f"/v1/pipelines/{pipeline.uuid}/runs/{pipeline_run.uuid}/console",
        headers={"Workflow-Key": client_application.api_key},
    )
    assert result.status_code == 200
    assert result.json == {
        "std_out": "stdout",
        "std_err": "",
    }


def test_update_pipeline_run_output(client, pipeline, worker_application):
    db.session.commit()
    pipeline_run = create_pipeline_run(pipeline.uuid, [])
    db.session.commit()

    result = client.put(
        "/v1/pipelines/no-id/runs/no-id/console",
        content_type="application/json",
        json={"std_out": "stdout", "std_err": "stderr",},
        headers={"Workflow-Key": worker_application.api_key},
    )
    assert result.status_code == 404

    # no such pipeline_run_id
    result = client.put(
        f"/v1/pipelines/{pipeline.uuid}/runs/no-id/console",
        content_type="application/json",
        json={"std_out": "stdout", "std_err": "stderr",},
        headers={"Workflow-Key": worker_application.api_key},
    )
    assert result.status_code == 404

    # successfully fetch a pipeline_run
    result = client.put(
        f"/v1/pipelines/{pipeline.uuid}/runs/{pipeline_run.uuid}/console",
        content_type="application/json",
        json={"std_out": "stdout", "std_err": "stderr",},
        headers={"Workflow-Key": worker_application.api_key},
    )
    assert result.status_code == 200
    assert pipeline_run.std_out == "stdout"
    assert pipeline_run.std_err == "stderr"
