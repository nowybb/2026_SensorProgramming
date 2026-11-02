"""하드웨어와 분리된 칸별 자동 건조 판단 로직."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from common.config import START_RH, STOP_RH, START_CONFIRM, STOP_CONFIRM, MAX_DRY_SECONDS

@dataclass
class CabinetState:
    slot: int
    shoe_present: bool = False
    humidity: Optional[float] = None
    temperature: Optional[float] = None
    state: str = "EMPTY"
    fan_on: bool = False
    started_at: Optional[datetime] = None
    last_valid_at: Optional[datetime] = None
    start_count: int = 0
    stop_count: int = 0
    previous_shoe: bool = False
    events: list = field(default_factory=list)

    def update(self, shoe_present, temperature, humidity, now, valid=True):
        """Returns transition events; invalid measurements always stop the fan."""
        self.events = []
        shoe_present = bool(shoe_present)
        if shoe_present != self.previous_shoe:
            self.events.append('SHOE_IN' if shoe_present else 'SHOE_OUT')
        self.previous_shoe = shoe_present
        self.shoe_present = shoe_present
        if not shoe_present:
            if self.fan_on:
                self.events.append('DRY_INTERRUPTED')
            self.fan_on = False
            self.state = 'EMPTY'
            self.started_at = None
            self.start_count = self.stop_count = 0
            return self.events
        if not valid or temperature is None or humidity is None or not (0 <= humidity <= 100 and -30 <= temperature <= 80):
            if self.fan_on:
                self.events.append('SENSOR_ERROR')
            self.fan_on = False
            self.state = 'SENSOR_ERROR'
            self.start_count = self.stop_count = 0
            return self.events
        self.temperature, self.humidity = float(temperature), float(humidity)
        self.last_valid_at = now
        if self.state == 'SENSOR_ERROR':
            self.state = 'STORED'
        if self.fan_on:
            if self.started_at and (now - self.started_at).total_seconds() >= MAX_DRY_SECONDS:
                self.fan_on = False
                self.state = 'TIMEOUT'
                self.events.append('DRY_TIMEOUT')
                return self.events
            self.stop_count = self.stop_count + 1 if humidity <= STOP_RH else 0
            if self.stop_count >= STOP_CONFIRM:
                self.fan_on = False
                self.state = 'DONE'
                self.events.append('DRY_DONE')
                self.stop_count = 0
            else:
                self.state = 'DRYING'
            return self.events
        # TIMEOUT: manual reset via shoe removal; DONE can restart if humidity rises
        if self.state == 'TIMEOUT':
            return self.events
        self.start_count = self.start_count + 1 if humidity >= START_RH else 0
        if self.start_count >= START_CONFIRM:
            self.fan_on = True
            self.state = 'DRYING'
            self.started_at = now
            self.stop_count = 0
            self.start_count = 0
            self.events.append('DRY_STARTED')
        elif self.state != 'DONE':
            self.state = 'STORED'
        return self.events
