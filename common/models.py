"""공통 데이터 계약 v1.0 — 외부 전달 시 dataclasses.asdict() 사용."""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional
from .enums import ShoeStatus, DryingStatus, FanStatus, DoorStatus, EventType, SessionStatus, AuthType

@dataclass
class ShoeDetectionData:
    compartment_id: int
    distance_cm: Optional[float]
    shoe_status: ShoeStatus
    detected_at: str

@dataclass
class EnvironmentData:
    compartment_id: int
    temperature: Optional[float]
    humidity: Optional[float]
    is_valid: bool
    measured_at: str

@dataclass
class ExternalEnvironmentData:
    cabinet_id: int
    temperature: Optional[float]
    humidity: Optional[float]
    is_valid: bool
    measured_at: str

@dataclass
class DryingControlData:
    compartment_id: int
    drying_status: DryingStatus
    fan_status: FanStatus
    circulation_fan_status: FanStatus
    exhaust_fan_status: FanStatus
    humidity: Optional[float]
    target_humidity: float
    elapsed_seconds: int
    remaining_seconds: Optional[int]
    updated_at: str

@dataclass
class DoorControlData:
    compartment_id: int
    approach_detected: bool
    door_status: DoorStatus
    updated_at: str

@dataclass
class StorageSessionData:
    session_id: int
    cabinet_id: int
    compartment_id: int
    user_id: Optional[int]
    auth_type: AuthType
    session_status: SessionStatus
    reserved_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    token_expires_at: Optional[str] = None

@dataclass
class SystemEventData:
    event_id: str
    event_type: EventType
    cabinet_id: int
    compartment_id: Optional[int]
    session_id: Optional[int]
    occurred_at: str
    details: dict[str, Any] = field(default_factory=dict)
