from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.schemas import OpenAPIResponse, SchemaGenerator
from starlette.testclient import TestClient

schemas = SchemaGenerator(
    {"openapi": "3.0.0", "info": {"title": "Example API", "version": "1.0"}}
)

app = Starlette()


subapp = Starlette()
app.mount("/subapp", subapp)


@app.websocket_route("/ws")
def ws(session):
    """ws"""
    raise NotImplementedError()


@app.route("/users", methods=["GET", "HEAD"])
def list_users(request):
    """
    responses:
      200:
        description: A list of users.
        examples:
          [{"username": "tom"}, {"username": "lucy"}]
    """
    raise NotImplementedError()


@app.route("/users", methods=["POST"])
def create_user(request):
    """
    responses:
      200:
        description: A user.
        examples:
          {"username": "tom"}
    """
    raise NotImplementedError()


@app.route("/orgs")
class OrganisationsEndpoint(HTTPEndpoint):
    def get(self, request):
        """
        responses:
          200:
            description: A list of organisations.
            examples:
              [{"name": "Foo Corp."}, {"name": "Acme Ltd."}]
        """
        raise NotImplementedError()

    def post(self, request):
        """
        responses:
          200:
            description: An organisation.
            examples:
              {"name": "Foo Corp."}
        """
        raise NotImplementedError()


@app.route("/regular-docstring-and-schema")
def regular_docstring_and_schema(request):
    """
    This a regular docstring example (not included in schema)

    ---

    responses:
      200:
        description: This is included in the schema.
    """
    raise NotImplementedError()


@app.route("/regular-docstring")
def regular_docstring(request):
    """
    This a regular docstring example (not included in schema)
    """
    raise NotImplementedError()


@app.route("/no-docstring")
def no_docstring(request):
    raise NotImplementedError()


@subapp.route("/subapp-endpoint")
def subapp_endpoint(request):
    """
    responses:
      200:
        description: This endpoint is part of a subapp.
    """
    raise NotImplementedError()


@app.route("/schema", methods=["GET"], include_in_schema=False)
def schema(request):
    return schemas.OpenAPIResponse(request=request)


def test_schema_generation():
    schema = schemas.get_schema(routes=app.routes)
    assert schema == {
        "openapi": "3.0.0",
        "info": {"title": "Example API", "version": "1.0"},
        "paths": {
            "/orgs": {
                "get": {
                    "responses": {
                        200: {
                            "description": "A list of " "organisations.",
                            "examples": [{"name": "Foo Corp."}, {"name": "Acme Ltd."}],
                        }
                    }
                },
                "post": {
                    "responses": {
                        200: {
                            "description": "An organisation.",
                            "examples": {"name": "Foo Corp."},
                        }
                    }
                },
            },
            "/regular-docstring-and-schema": {
                "get": {
                    "responses": {
                        200: {"description": "This is included in the schema."}
                    }
                }
            },
            "/subapp/subapp-endpoint": {
                "get": {
                    "responses": {
                        200: {"description": "This endpoint is part of a subapp."}
                    }
                }
            },
            "/users": {
                "get": {
                    "responses": {
                        200: {
                            "description": "A list of users.",
                            "examples": [{"username": "tom"}, {"username": "lucy"}],
                        }
                    }
                },
                "post": {
                    "responses": {
                        200: {"description": "A user.", "examples": {"username": "tom"}}
                    }
                },
            },
        },
    }


EXPECTED_SCHEMA = """
info:
  title: Example API
  version: '1.0'
openapi: 3.0.0
paths:
  /orgs:
    get:
      responses:
        200:
          description: A list of organisations.
          examples:
          - name: Foo Corp.
          - name: Acme Ltd.
    post:
      responses:
        200:
          description: An organisation.
          examples:
            name: Foo Corp.
  /regular-docstring-and-schema:
    get:
      responses:
        200:
          description: This is included in the schema.
  /subapp/subapp-endpoint:
    get:
      responses:
        200:
          description: This endpoint is part of a subapp.
  /users:
    get:
      responses:
        200:
          description: A list of users.
          examples:
          - username: tom
          - username: lucy
    post:
      responses:
        200:
          description: A user.
          examples:
            username: tom
"""


def test_schema_endpoint():
    client = TestClient(app)
    response = client.get("/schema")
    assert response.headers["Content-Type"] == "application/vnd.oai.openapi"
    assert response.text.strip() == EXPECTED_SCHEMA.strip()
