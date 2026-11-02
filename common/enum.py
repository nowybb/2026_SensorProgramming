
from enum import Enum

class ShoeStatus(str, Enum):
    EMPTY = "EMPTY"
    OCCUPIED = "OCCUPIED"
    UNKNOWN = "UNKNOWN"

class DryingStatus(str, Enum):
    IDLE = "IDLE"
    DRYING = "DRYING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class FanStatus(str, Enum):
    OFF = "OFF"
    ON = "ON"

class DoorStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MOVING = "MOVING"
    ERROR = "ERROR"

class EventType(str, Enum):
    SHOE_IN = "SHOE_IN"
    SHOE_OUT = "SHOE_OUT"
    DRY_START = "DRY_START"
    DRY_COMPLETE = "DRY_COMPLETE"
    DRY_ERROR = "DRY_ERROR"
    UNEXPECTED_REMOVAL = "UNEXPECTED_REMOVAL"

class CabinetMode(str, Enum):
    HOME = "HOME"
    PUBLIC = "PUBLIC"
