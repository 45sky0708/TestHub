from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

from .models import (
    DashboardMetrics,
    Event,
    Feedback,
    MatchRecord,
    Recommendation,
    RecommendationResponse,
    Registration,
    SurfaceBlueprint,
    SurfaceSection,
)


UTC = timezone.utc


def utcnow() -> datetime:
    return datetime.now(UTC)


class ConnectHubService:
    """Domain service powering the Connect Hub MVP."""

    def __init__(self) -> None:
        self._events: Dict[str, Event] = {}
        self._registrations: Dict[str, Registration] = {}
        self._registration_index: Dict[Tuple[str, str], str] = {}
        self._feedback: Dict[str, Feedback] = {}
        self._matches: Dict[str, MatchRecord] = {}
        self._surface_blueprint = SurfaceBlueprint(
            frontend=SurfaceSection(title="前台介面", summary="", features=[]),
            backend=SurfaceSection(title="後台介面", summary="", features=[]),
        )

    # ------------------------------------------------------------------
    # Event operations
    # ------------------------------------------------------------------
    def create_event(
        self,
        *,
        name: str,
        category: str,
        mode: str,
        start_at: datetime,
        end_at: datetime,
        capacity: int,
        location: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        description: Optional[str] = None,
    ) -> Event:
        self._validate_event_window(start_at, end_at)
        self._ensure_timezone(start_at, "start_at")
        self._ensure_timezone(end_at, "end_at")
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")
        event_id = str(uuid4())
        event = Event(
            id=event_id,
            name=name,
            category=category,
            mode=mode,
            start_at=start_at,
            end_at=end_at,
            capacity=capacity,
            location=location,
            tags=list(tags or []),
            description=description,
        )
        self._events[event_id] = event
        return event

    def update_event(self, event_id: str, **updates: object) -> Event:
        event = self._get_event(event_id)
        data = asdict(event)
        data.update(updates)
        start_at = data.get("start_at", event.start_at)
        end_at = data.get("end_at", event.end_at)
        if isinstance(start_at, datetime) and isinstance(end_at, datetime):
            self._validate_event_window(start_at, end_at)
            self._ensure_timezone(start_at, "start_at")
            self._ensure_timezone(end_at, "end_at")
        capacity = data.get("capacity", event.capacity)
        if isinstance(capacity, int):
            if capacity <= 0:
                raise ValueError("capacity must be greater than zero")
            if capacity < event.seats_taken:
                raise ValueError("capacity cannot be lower than current registrations")
        updated = Event(**data)  # type: ignore[arg-type]
        self._events[event_id] = updated
        return updated

    def list_events(
        self,
        *,
        category: Optional[str] = None,
        mode: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Event]:
        events = list(self._events.values())
        if category:
            events = [evt for evt in events if evt.category == category]
        if mode:
            events = [evt for evt in events if evt.mode == mode]
        if tag:
            events = [evt for evt in events if tag in evt.tags]
        return sorted(events, key=lambda evt: evt.start_at)

    def get_event(self, event_id: str) -> Event:
        return self._get_event(event_id)

    # ------------------------------------------------------------------
    # Registration operations
    # ------------------------------------------------------------------
    def register_participant(self, *, event_id: str, participant_id: str) -> Registration:
        event = self._get_event(event_id)
        if not event.has_available_seats():
            raise ValueError("event is already at full capacity")
        if not participant_id:
            raise ValueError("participant_id is required")
        if event.end_at <= utcnow():
            raise ValueError("cannot register for an event that has already finished")

        key = (event_id, participant_id)
        now = utcnow()
        if key in self._registration_index:
            existing_id = self._registration_index[key]
            existing = self._registrations[existing_id]
            if existing.status != "cancelled":
                raise ValueError("participant already registered for event")
            revived = replace(existing, status="confirmed", cancelled_at=None, registered_at=now)
            self._registrations[existing_id] = revived
            self._events[event_id] = replace(event, seats_taken=event.seats_taken + 1)
            return revived

        registration_id = str(uuid4())
        record = Registration(
            id=registration_id,
            event_id=event_id,
            participant_id=participant_id,
            status="confirmed",
            registered_at=now,
        )
        self._registrations[registration_id] = record
        self._registration_index[key] = registration_id
        self._events[event_id] = replace(event, seats_taken=event.seats_taken + 1)
        return record

    def cancel_registration(self, registration_id: str) -> Registration:
        registration = self._get_registration(registration_id)
        if registration.status == "cancelled":
            return registration

        updated = replace(registration, status="cancelled", cancelled_at=utcnow())
        self._registrations[registration_id] = updated
        key = (registration.event_id, registration.participant_id)
        self._registration_index[key] = registration_id

        event = self._get_event(registration.event_id)
        if event.seats_taken > 0:
            self._events[event.id] = replace(event, seats_taken=event.seats_taken - 1)
        return updated

    def list_registrations(
        self,
        *,
        event_id: Optional[str] = None,
        participant_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Registration]:
        records = list(self._registrations.values())
        if event_id:
            records = [record for record in records if record.event_id == event_id]
        if participant_id:
            records = [record for record in records if record.participant_id == participant_id]
        if status:
            records = [record for record in records if record.status == status]
        return sorted(records, key=lambda record: record.registered_at)

    # ------------------------------------------------------------------
    # Feedback operations
    # ------------------------------------------------------------------
    def record_feedback(
        self,
        *,
        event_id: str,
        participant_id: str,
        score: int,
        comment: Optional[str] = None,
    ) -> Feedback:
        if not 1 <= score <= 5:
            raise ValueError("score must be between 1 and 5")
        self._get_event(event_id)
        feedback_id = str(uuid4())
        feedback = Feedback(
            id=feedback_id,
            event_id=event_id,
            participant_id=participant_id,
            score=score,
            comment=comment,
            submitted_at=utcnow(),
        )
        self._feedback[feedback_id] = feedback
        return feedback

    # ------------------------------------------------------------------
    # Matchmaking operations
    # ------------------------------------------------------------------
    def create_match(
        self,
        *,
        opportunity_id: str,
        talent_id: str,
        recommended_score: float,
        notes: Optional[str] = None,
    ) -> MatchRecord:
        if not 0 <= recommended_score <= 1:
            raise ValueError("recommended_score must be between 0 and 1")
        match_id = str(uuid4())
        record = MatchRecord(
            id=match_id,
            opportunity_id=opportunity_id,
            talent_id=talent_id,
            recommended_score=recommended_score,
            notes=notes,
            status="pending",
            created_at=utcnow(),
        )
        self._matches[match_id] = record
        return record

    def list_matches(self, *, status: Optional[str] = None) -> List[MatchRecord]:
        matches = list(self._matches.values())
        if status:
            matches = [match for match in matches if match.status == status]
        return sorted(matches, key=lambda match: match.created_at, reverse=True)

    def update_match_status(
        self, match_id: str, *, status: str, notes: Optional[str] = None
    ) -> MatchRecord:
        allowed_statuses = {"pending", "approved", "rejected", "in_review", "contacted"}
        if status not in allowed_statuses:
            raise ValueError("invalid match status")
        match = self._get_match(match_id)
        updated_notes = match.notes if notes is None else notes
        updated = replace(match, status=status, notes=updated_notes)
        self._matches[match_id] = updated
        return updated

    # ------------------------------------------------------------------
    # Insights
    # ------------------------------------------------------------------
    def recommend_events(self, *, participant_id: str, limit: int = 3) -> RecommendationResponse:
        now = utcnow()
        candidates = [
            event
            for event in self._events.values()
            if event.end_at >= now and event.has_available_seats()
        ]
        candidates.sort(key=lambda evt: (evt.seats_taken / evt.capacity if evt.capacity else 1.0, evt.start_at))
        top = candidates[:limit]
        recommendations = [
            Recommendation(event_id=event.id, reason=self._build_reason(event))
            for event in top
        ]
        return RecommendationResponse(participant_id=participant_id, recommendations=recommendations)

    def dashboard(self) -> DashboardMetrics:
        total_events = len(self._events)
        total_registrations = sum(
            1 for registration in self._registrations.values() if registration.status == "confirmed"
        )
        average_fill_rate = 0.0
        if total_events:
            fill_rates = [event.seats_taken / event.capacity for event in self._events.values() if event.capacity]
            if fill_rates:
                average_fill_rate = round(sum(fill_rates) / len(fill_rates), 3)

        category_counter = Counter(event.category for event in self._events.values())
        top_categories = [category for category, _ in category_counter.most_common(3)]

        upcoming = [event for event in self._events.values() if event.start_at >= utcnow()]
        upcoming.sort(key=lambda evt: evt.start_at)

        pending_matches = sum(1 for match in self._matches.values() if match.status == "pending")

        return DashboardMetrics(
            total_events=total_events,
            total_registrations=total_registrations,
            average_fill_rate=average_fill_rate,
            top_categories=top_categories,
            upcoming_events=upcoming[:5],
            matches_waiting_review=pending_matches,
        )

    # ------------------------------------------------------------------
    # Experience blueprint
    # ------------------------------------------------------------------
    def configure_surface_blueprint(
        self,
        *,
        frontend: SurfaceSection,
        backend: SurfaceSection,
    ) -> SurfaceBlueprint:
        self._surface_blueprint = SurfaceBlueprint(frontend=frontend, backend=backend)
        return self._surface_blueprint

    def surface_blueprint(self) -> SurfaceBlueprint:
        return self._surface_blueprint

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_event(self, event_id: str) -> Event:
        try:
            return self._events[event_id]
        except KeyError as exc:
            raise KeyError(f"event {event_id} not found") from exc

    def _get_registration(self, registration_id: str) -> Registration:
        try:
            return self._registrations[registration_id]
        except KeyError as exc:
            raise KeyError(f"registration {registration_id} not found") from exc

    def _get_match(self, match_id: str) -> MatchRecord:
        try:
            return self._matches[match_id]
        except KeyError as exc:
            raise KeyError(f"match {match_id} not found") from exc

    @staticmethod
    def _build_reason(event: Event) -> str:
        primary_tag = event.tags[0] if event.tags else event.category
        seats_left = event.capacity - event.seats_taken
        return f"Matches your interest in {primary_tag}; {seats_left} seats remaining"

    @staticmethod
    def _ensure_timezone(value: datetime, field_name: str) -> None:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError(f"{field_name} must be timezone-aware")

    @staticmethod
    def _validate_event_window(start_at: datetime, end_at: datetime) -> None:
        if end_at <= start_at:
            raise ValueError("event end time must be after the start time")


service = ConnectHubService()


def reset_service(*, seed_events: Optional[Iterable[dict]] = None) -> None:
    global service
    service = ConnectHubService()
    if seed_events:
        for payload in seed_events:
            if isinstance(payload.get("start_at"), datetime) and payload["start_at"].tzinfo is None:
                payload = payload.copy()
                payload["start_at"] = payload["start_at"].replace(tzinfo=UTC)
            if isinstance(payload.get("end_at"), datetime) and payload["end_at"].tzinfo is None:
                payload = payload.copy()
                payload["end_at"] = payload["end_at"].replace(tzinfo=UTC)
            service.create_event(**payload)


__all__ = ["service", "ConnectHubService", "reset_service", "utcnow"]
