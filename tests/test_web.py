from __future__ import annotations

import io
import json
from typing import Tuple

from wsgiref.util import setup_testing_defaults

from app.web import create_app


def _call_app(app, path: str) -> Tuple[int, dict[str, str], bytes]:
    body = io.BytesIO()
    environ = {}
    setup_testing_defaults(environ)
    environ["PATH_INFO"] = path

    status_headers: list[Tuple[str, str]] = []

    def start_response(status: str, headers: list[Tuple[str, str]]) -> None:
        code = int(status.split()[0])
        status_headers.append((code, headers))

    result = app(environ, start_response)
    for chunk in result:
        body.write(chunk)
    if hasattr(result, "close"):
        result.close()

    status_code, headers = status_headers[0]
    header_dict = {key: value for key, value in headers}
    return status_code, header_dict, body.getvalue()


def test_dashboard_page_contains_sections() -> None:
    app = create_app()
    status, headers, payload = _call_app(app, "/")
    assert status == 200
    assert headers["Content-Type"].startswith("text/html")
    html = payload.decode("utf-8")
    assert "Connect Hub MVP 面板" in html
    assert "所有活動" in html
    assert "前台體驗" in html
    assert "後台營運" in html


def test_events_api_returns_seed_data() -> None:
    app = create_app()
    status, headers, payload = _call_app(app, "/api/events")
    assert status == 200
    assert headers["Content-Type"].startswith("application/json")
    events = json.loads(payload.decode("utf-8"))
    assert isinstance(events, list)
    assert events
    assert {"id", "name", "capacity", "start_at"}.issubset(events[0])


def test_dashboard_api_contains_metrics() -> None:
    app = create_app()
    status, headers, payload = _call_app(app, "/api/dashboard")
    assert status == 200
    metrics = json.loads(payload.decode("utf-8"))
    assert metrics["total_events"] >= 1
    assert isinstance(metrics["upcoming_events"], list)


def test_surface_api_returns_blueprint() -> None:
    app = create_app()
    status, headers, payload = _call_app(app, "/api/surface")
    assert status == 200
    assert headers["Content-Type"].startswith("application/json")
    blueprint = json.loads(payload.decode("utf-8"))
    assert "frontend" in blueprint and "backend" in blueprint
    assert blueprint["frontend"]["features"]
    assert any(feature["ai_enabled"] for feature in blueprint["backend"]["features"])
