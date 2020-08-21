from app.models import Pipeline, db
from app.queries import find_pipeline
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


def test_create_pipeline_non_empty_params(client):
    # An error is returned if no configuration information is supplied.
    params = {
        "name": "a pipeline",
        "description": "a description",
        "docker_image_url": "",
        "repository_ssh_url": "",
        "repository_branch": "",
    }
    result = client.post("/v1/pipelines", content_type="application/json", json=params,)
    assert result.status_code == 400


def test_create_pipeline(client):
    params = {
        "name": "a pipeline",
        "description": "a description",
        "docker_image_url": "a/url",
        "repository_ssh_url": "ssh+github url",
        "repository_branch": "master",
    }
    result = client.post("/v1/pipelines", content_type="application/json", json=params,)
    assert result.status_code == 200

    pipeline = Pipeline.query.filter(Pipeline.name == params["name"]).one_or_none()
    assert pipeline.name == "a pipeline"


def test_list_pipelines(client):
    result = client.get("/v1/pipelines", content_type="application/json")
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

    result = client.get("/v1/pipelines", content_type="application/json")
    assert result.status_code == 200
    assert len(result.json) == 2
    assert result.json[0]["name"] == p1.name
    assert result.json[1]["name"] == p2.name


def test_get_pipeline_no_match(client):
    result = client.get(
        "/v1/pipelines/1111ddddeeee2222", content_type="application/json"
    )
    assert result.status_code == 404


def test_get_pipeline(client, pipeline):
    result = client.get(
        f"/v1/pipelines/{pipeline.uuid}", content_type="application/json"
    )
    assert result.status_code == 200


def test_remove_pipeline_no_match(client):
    result = client.delete(
        "/v1/pipelines/1111ddddeeee2222", content_type="application/json"
    )
    assert result.status_code == 400


def test_remove_pipeline(client, pipeline):
    result = client.delete(
        f"/v1/pipelines/{pipeline.uuid}", content_type="application/json"
    )
    assert result.status_code == 200
    assert find_pipeline(pipeline.uuid) is None


def test_create_run_no_such_uuid(client):
    result = client.post(
        "/v1/pipelines/1111abcd/runs",
        content_type="application/json",
        json={"inputs": []},
    )
    assert result.status_code == 400


def test_create_run_bad_input_name(client, pipeline):
    result = client.post(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        content_type="application/json",
        json={"inputs": [{"name": "name1.pdf"}]},
    )
    assert result.status_code == 400

    result = client.post(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        content_type="application/json",
        json={"inputs": [{"name": "name1.pdf", "url": "aurl", "extrakey": "badinput"}]},
    )
    assert result.status_code == 400

    result = client.post(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        content_type="application/json",
        json={"inputs": "[]"},
    )
    assert result.status_code == 400


def test_create_run(client, pipeline):
    result = client.post(
        f"/v1/pipelines/{pipeline.uuid}/runs",
        content_type="application/json",
        json={"inputs": [{"name": "name1.pdf", "url": "aurl"}]},
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
