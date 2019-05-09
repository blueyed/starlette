import asyncio
import pytest

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.websockets import WebSocket, WebSocketDisconnect

mock_service = Starlette()


@mock_service.route("/")
def mock_service_endpoint(request):
    return JSONResponse({"mock": "example"})


app = Starlette()


@app.route("/")
def homepage(request):
    client = TestClient(mock_service)
    response = client.get("/")
    return JSONResponse(response.json())


startup_error_app = Starlette()


@startup_error_app.on_event("startup")
def startup():
    raise RuntimeError()


def test_use_testclient_in_endpoint():
    """
    We should be able to use the test client within applications.

    This is useful if we need to mock out other services,
    during tests or in development.
    """
    client = TestClient(app)
    response = client.get("/")
    assert response.json() == {"mock": "example"}


def testclient_as_contextmanager():
    with TestClient(app):
        pass


def test_error_on_startup():
    with pytest.raises(RuntimeError):
        with TestClient(startup_error_app):
            pass  # pragma: no cover


def test_testclient_asgi2():
    def app(scope):
        async def inner(receive, send):
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"text/plain"]],
                }
            )
            await send({"type": "http.response.body", "body": b"Hello, world!"})

        return inner

    client = TestClient(app)
    response = client.get("/")
    assert response.text == "Hello, world!"


def test_testclient_asgi3():
    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send({"type": "http.response.body", "body": b"Hello, world!"})

    client = TestClient(app)
    response = client.get("/")
    assert response.text == "Hello, world!"


def test_websocket_blocking_receive():
    def app(scope):
        async def respond(websocket):
            await websocket.send_json({"message": "test"})

        async def asgi(receive, send):
            websocket = WebSocket(scope, receive=receive, send=send)
            await websocket.accept()
            asyncio.ensure_future(respond(websocket))
            try:
                # this will block as the client does not send us data
                # it should not prevent `respond` from executing though
                await websocket.receive_json()
            except WebSocketDisconnect:
                pass

        return asgi

    client = TestClient(app)
    with client.websocket_connect("/") as websocket:
        data = websocket.receive_json()
        assert data == {"message": "test"}


def test_error_with_middleware_and_testclient_exit():
    """TestClient's __exit__ should not raise the exception again."""
    app = Starlette()

    @app.middleware("http")
    async def http_middleware(request, call_next):
        return await call_next(request)

    @app.route("/error")
    async def error(request):
        pytest.fail("should_only_fail_once")

    with TestClient(app) as client:
        with pytest.raises(pytest.fail.Exception):
            client.get("/error")

    # XXX: needed to fix the following on stderr when running all tests?!
    # Task exception was never retrieved
    # future: <Task finished coro=<Starlette.__call__() done, defined at
    # …/starlette/applications.py:132> exception=should_only_fail_once>
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.sleep(0))
