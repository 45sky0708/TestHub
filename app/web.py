"""Minimal WSGI app to expose a Connect Hub MVP dashboard."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import Callable, Iterable, Optional
from wsgiref.simple_server import make_server

from .main import bootstrap_demo_service
from .models import Event
from .service import ConnectHubService

HTML_CONTENT_TYPE = ("Content-Type", "text/html; charset=utf-8")
JSON_CONTENT_TYPE = ("Content-Type", "application/json; charset=utf-8")


def _format_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M %Z")


def _render_events(events: Iterable[Event]) -> str:
    cards = []
    for event in events:
        tags = "".join(f"<span class=\"tag\">{tag}</span>" for tag in event.tags)
        cards.append(
            """
            <article class="event-card">
                <header>
                    <h2>{name}</h2>
                    <span class="category">{category}</span>
                </header>
                <dl>
                    <div><dt>Mode</dt><dd>{mode}</dd></div>
                    <div><dt>When</dt><dd>{start} &ndash; {end}</dd></div>
                    <div><dt>Location</dt><dd>{location}</dd></div>
                    <div><dt>Capacity</dt><dd>{taken}/{capacity} (剩餘 {remaining})</dd></div>
                </dl>
                <p class="description">{description}</p>
                <footer>{tags}</footer>
            </article>
            """.format(
                name=event.name,
                category=event.category.title(),
                mode=event.mode.title(),
                start=_format_datetime(event.start_at),
                end=_format_datetime(event.end_at),
                location=event.location or "待定",
                capacity=event.capacity,
                taken=event.seats_taken,
                remaining=max(event.capacity - event.seats_taken, 0),
                description=event.description or "",
                tags=tags,
            )
        )
    if cards:
        return "\n".join(cards)
    return "<p class=\"empty\">目前沒有可報名的活動。</p>"


def render_dashboard(service: ConnectHubService) -> str:
    metrics = service.dashboard()
    upcoming_markup = _render_events(metrics.upcoming_events)
    all_events_markup = _render_events(service.list_events())
    return f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="utf-8" />
        <title>Connect Hub MVP</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            :root {{
                color-scheme: light dark;
                font-family: "Noto Sans TC", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                background: #f5f5f5;
                color: #1f2933;
                line-height: 1.6;
            }}
            body {{
                margin: 0;
                padding: 2.5rem 1.5rem 4rem;
                background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
            }}
            header.page-header {{
                max-width: 960px;
                margin: 0 auto 2rem;
                text-align: center;
            }}
            header.page-header h1 {{
                margin: 0 0 0.5rem;
                font-size: clamp(2rem, 5vw, 3rem);
                letter-spacing: 0.04em;
            }}
            header.page-header p {{
                margin: 0;
                color: #475569;
            }}
            section {{
                max-width: 960px;
                margin: 0 auto 2.5rem;
                padding: 1.5rem;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 16px;
                box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
            }}
            section h2 {{
                margin-top: 0;
                font-size: 1.5rem;
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 0.5rem;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0 0;
            }}
            .metric {{
                padding: 1rem;
                border-radius: 12px;
                background: linear-gradient(160deg, #2563eb 0%, #7c3aed 100%);
                color: #fff;
                box-shadow: 0 10px 25px rgba(79, 70, 229, 0.25);
            }}
            .metric span {{
                display: block;
                font-size: 0.9rem;
                opacity: 0.85;
            }}
            .metric strong {{
                display: block;
                font-size: 1.8rem;
                margin-top: 0.35rem;
                font-weight: 700;
            }}
            .event-card {{
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 1.25rem;
                margin: 1rem 0;
                background: #ffffff;
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}
            .event-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 16px 32px rgba(30, 64, 175, 0.16);
            }}
            .event-card header {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                gap: 1rem;
            }}
            .event-card h2 {{
                margin: 0;
                font-size: 1.35rem;
            }}
            .category {{
                font-size: 0.85rem;
                padding: 0.35rem 0.6rem;
                border-radius: 999px;
                background: #dbeafe;
                color: #1d4ed8;
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 0.05em;
            }}
            dl {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 0.75rem 1rem;
                margin: 1rem 0;
            }}
            dt {{
                font-weight: 600;
                color: #475569;
                text-transform: uppercase;
                font-size: 0.75rem;
                letter-spacing: 0.05em;
            }}
            dd {{
                margin: 0.25rem 0 0;
                font-size: 0.95rem;
            }}
            .tag {{
                display: inline-flex;
                align-items: center;
                padding: 0.3rem 0.75rem;
                margin: 0 0.3rem 0.3rem 0;
                border-radius: 999px;
                background: #f1f5f9;
                color: #0f172a;
                font-size: 0.8rem;
            }}
            .description {{
                margin: 0 0 0.5rem;
                color: #334155;
            }}
            .empty {{
                margin: 1.5rem 0;
                text-align: center;
                color: #64748b;
            }}
            footer.page-footer {{
                max-width: 960px;
                margin: 0 auto;
                text-align: center;
                color: #475569;
                font-size: 0.85rem;
            }}
            @media (prefers-color-scheme: dark) {{
                body {{ background: #0f172a; }}
                section {{
                    background: rgba(15, 23, 42, 0.85);
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    color: #e2e8f0;
                }}
                .event-card {{
                    background: rgba(15, 23, 42, 0.95);
                    border: 1px solid rgba(148, 163, 184, 0.18);
                }}
                .category {{
                    background: rgba(59, 130, 246, 0.2);
                    color: #93c5fd;
                }}
                .tag {{
                    background: rgba(148, 163, 184, 0.16);
                    color: #e2e8f0;
                }}
                .description {{ color: #cbd5f5; }}
                dt {{ color: #cbd5f5; }}
                footer.page-footer {{ color: #cbd5f5; }}
            }}
        </style>
    </head>
    <body>
        <header class="page-header">
            <h1>Connect Hub MVP 面板</h1>
            <p>快速檢視活動排程、報名熱度與 AI 媒合待辦</p>
        </header>
        <section>
            <h2>核心指標</h2>
            <div class="metrics">
                <div class="metric"><span>活動數量</span><strong>{metrics.total_events}</strong></div>
                <div class="metric"><span>有效報名</span><strong>{metrics.total_registrations}</strong></div>
                <div class="metric"><span>平均入席率</span><strong>{metrics.average_fill_rate:.0%}</strong></div>
                <div class="metric"><span>待審核媒合</span><strong>{metrics.matches_waiting_review}</strong></div>
            </div>
        </section>
        <section>
            <h2>即將開始</h2>
            {upcoming_markup}
        </section>
        <section>
            <h2>所有活動</h2>
            {all_events_markup}
        </section>
        <footer class="page-footer">
            <p>此頁面使用內建的記憶體資料，做為 Connect Hub MVP 的可視化雛型。</p>
        </footer>
    </body>
    </html>
    """


def events_payload(service: ConnectHubService) -> list[dict[str, object]]:
    return [asdict(event) for event in service.list_events()]


def dashboard_payload(service: ConnectHubService) -> dict[str, object]:
    metrics = service.dashboard()
    payload = asdict(metrics)
    payload["upcoming_events"] = [asdict(event) for event in metrics.upcoming_events]
    return payload


def create_app(service: Optional[ConnectHubService] = None) -> Callable:
    svc = service or bootstrap_demo_service()

    def app(environ: dict, start_response: Callable) -> Iterable[bytes]:
        path = environ.get("PATH_INFO", "")
        if path in {"", "/"}:
            body = render_dashboard(svc)
            start_response("200 OK", [HTML_CONTENT_TYPE])
            return [body.encode("utf-8")]
        if path == "/api/events":
            body = json.dumps(events_payload(svc), default=str)
            start_response("200 OK", [JSON_CONTENT_TYPE])
            return [body.encode("utf-8")]
        if path == "/api/dashboard":
            body = json.dumps(dashboard_payload(svc), default=str)
            start_response("200 OK", [JSON_CONTENT_TYPE])
            return [body.encode("utf-8")]
        start_response("404 Not Found", [HTML_CONTENT_TYPE])
        return [b"<h1>404 Not Found</h1>"]

    return app


def run(host: str = "0.0.0.0", port: int = 8000) -> None:  # pragma: no cover - convenience wrapper
    with make_server(host, port, create_app()) as server:
        print(f"Serving Connect Hub MVP on http://{host}:{port}")
        server.serve_forever()


if __name__ == "__main__":  # pragma: no cover
    run()
