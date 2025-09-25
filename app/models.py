from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(slots=True)
class Event:
    id: str
    name: str
    category: str
    mode: str
    start_at: datetime
    end_at: datetime
    capacity: int
    location: Optional[str]
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    seats_taken: int = 0

    def has_available_seats(self) -> bool:
        return self.seats_taken < self.capacity


@dataclass(slots=True)
class Registration:
    id: str
    event_id: str
    participant_id: str
    status: str
    registered_at: datetime
    cancelled_at: Optional[datetime] = None


@dataclass(slots=True)
class Feedback:
    id: str
    event_id: str
    participant_id: str
    score: int
    comment: Optional[str]
    submitted_at: datetime


@dataclass(slots=True)
class MatchRecord:
    id: str
    opportunity_id: str
    talent_id: str
    recommended_score: float
    notes: Optional[str]
    status: str
    created_at: datetime


@dataclass(slots=True)
class Recommendation:
    event_id: str
    reason: str


@dataclass(slots=True)
class RecommendationResponse:
    participant_id: str
    recommendations: List[Recommendation]


@dataclass(slots=True)
class DashboardMetrics:
    total_events: int
    total_registrations: int
    average_fill_rate: float
    top_categories: List[str]
    upcoming_events: List[Event]
    matches_waiting_review: int


@dataclass(slots=True)
class SurfaceFeature:
    name: str
    description: str
    ai_enabled: bool = False
    highlights: List[str] = field(default_factory=list)


@dataclass(slots=True)
class SurfaceSection:
    title: str
    summary: str
    features: List[SurfaceFeature] = field(default_factory=list)


@dataclass(slots=True)
class SurfaceBlueprint:
    frontend: SurfaceSection
    backend: SurfaceSection
