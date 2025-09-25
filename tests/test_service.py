from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import app.service as service_module
from app.service import ConnectHubService, reset_service

UTC = timezone.utc


def seed_events() -> list[dict]:
    now = datetime.now(UTC)
    return [
        {
            "name": "Connect Hub Kickoff",
            "category": "workshop",
            "mode": "onsite",
            "start_at": now + timedelta(days=5),
            "end_at": now + timedelta(days=5, hours=2),
            "capacity": 50,
            "location": "Taipei",
            "tags": ["devrel", "community"],
            "description": "Launch strategy workshop.",
        },
        {
            "name": "AI Matching Lab",
            "category": "lab",
            "mode": "online",
            "start_at": now + timedelta(days=10),
            "end_at": now + timedelta(days=10, hours=2),
            "capacity": 30,
            "location": "Zoom",
            "tags": ["ai", "matching"],
            "description": "Hands-on session for AI driven matching.",
        },
    ]


def setup_function(_: object) -> None:
    reset_service(seed_events=seed_events())


def test_create_and_get_event() -> None:
    svc = service_module.service
    event = svc.create_event(
        name="Growth Roundtable",
        category="meetup",
        mode="onsite",
        start_at=datetime.now(UTC) + timedelta(days=3),
        end_at=datetime.now(UTC) + timedelta(days=3, hours=1),
        capacity=25,
        location="Taipei",
        tags=["community"],
        description="Invite-only sharing session.",
    )
    fetched = svc.get_event(event.id)
    assert fetched.name == event.name
    assert fetched.capacity == 25


def test_list_events_filtering() -> None:
    svc = service_module.service
    online_events = svc.list_events(mode="online")
    assert len(online_events) == 1
    assert online_events[0].mode == "online"


def test_register_and_dashboard_metrics() -> None:
    svc = service_module.service
    event = svc.list_events()[0]
    svc.register_participant(event_id=event.id, participant_id="user-1")

    metrics = svc.dashboard()
    assert metrics.total_registrations == 1
    assert metrics.total_events >= 2


def test_update_event_capacity_guard() -> None:
    svc = service_module.service
    event = svc.list_events()[0]
    svc.register_participant(event_id=event.id, participant_id="user-cap")

    with pytest.raises(ValueError):
        svc.update_event(event.id, capacity=0)


def test_cancel_registration_restores_capacity() -> None:
    svc = service_module.service
    event = svc.list_events()[0]
    registration = svc.register_participant(event_id=event.id, participant_id="user-2")
    assert svc.get_event(event.id).seats_taken == 1

    cancelled = svc.cancel_registration(registration.id)
    assert cancelled.status == "cancelled"
    assert svc.get_event(event.id).seats_taken == 0

    # cancelled registration should be visible when filtering by status
    cancelled_records = svc.list_registrations(status="cancelled")
    assert registration.id in {record.id for record in cancelled_records}


def test_duplicate_registration_is_blocked() -> None:
    svc = service_module.service
    event = svc.list_events()[0]
    svc.register_participant(event_id=event.id, participant_id="user-3")

    with pytest.raises(ValueError):
        svc.register_participant(event_id=event.id, participant_id="user-3")


def test_recommendations_prioritize_available_events() -> None:
    svc = service_module.service
    event = svc.list_events()[0]

    for idx in range(event.capacity):
        svc.register_participant(event_id=event.id, participant_id=f"user-{idx}")

    recommendations = svc.recommend_events(participant_id="test-user")
    assert recommendations.participant_id == "test-user"
    assert all(rec.event_id != event.id for rec in recommendations.recommendations)


def test_create_match_and_filter_pending() -> None:
    svc = service_module.service
    match = svc.create_match(
        opportunity_id="opp-1",
        talent_id="tal-1",
        recommended_score=0.8,
        notes="High overlap on skills",
    )

    pending = svc.list_matches(status="pending")
    assert len(pending) == 1
    assert pending[0].status == "pending"

    updated = svc.update_match_status(match.id, status="approved")
    assert updated.status == "approved"

    with pytest.raises(ValueError):
        svc.update_match_status(match.id, status="unknown")


def test_reset_service_replaces_global_instance() -> None:
    first_instance = service_module.service
    reset_service()
    assert service_module.service is not first_instance
    assert isinstance(service_module.service, ConnectHubService)
