from __future__ import annotations

from datetime import timedelta

from .service import ConnectHubService, utcnow


def bootstrap_demo_service() -> ConnectHubService:
    """Seed a service instance with sample events for local exploration."""
    service = ConnectHubService()
    now = utcnow()
    service.create_event(
        name="Connect Hub Kickoff",
        category="workshop",
        mode="onsite",
        start_at=now + timedelta(days=7),
        end_at=now + timedelta(days=7, hours=2),
        capacity=50,
        location="Taipei",
        tags=["devrel", "community"],
        description="Vision alignment and onboarding workshop.",
    )
    service.create_event(
        name="AI Matching Lab",
        category="lab",
        mode="online",
        start_at=now + timedelta(days=10),
        end_at=now + timedelta(days=10, hours=2),
        capacity=40,
        location="Zoom",
        tags=["ai", "matching"],
        description="Hands-on AI matching experiments.",
    )
    return service


if __name__ == "__main__":  # pragma: no cover - manual exploration helper
    svc = bootstrap_demo_service()
    for event in svc.list_events():
        print(f"{event.name} ({event.mode}) - {event.start_at:%Y-%m-%d %H:%M %Z}")
