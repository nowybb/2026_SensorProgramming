"""실측 드라이버. --simulate 일 때는 불러오지 않음.
주의: 팬 MOSFET 제어부와 12V 전원, DHT22 풀업 배선 확인 후 사용.
"""
from common.config import SENSOR_PINS, FAN_PINS, FAN_ACTIVE_HIGH

class RealHardware:
    def __init__(self):
        import board
        import adafruit_dht
        import RPi.GPIO as GPIO
        self.GPIO = GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.sensors = {}
        try:
            for slot, pin in SENSOR_PINS.items():
                self.sensors[slot] = adafruit_dht.DHT22(getattr(board, 'D'+str(pin)), use_pulseio=False)
            off = GPIO.LOW if FAN_ACTIVE_HIGH else GPIO.HIGH
            for pins in FAN_PINS.values():
                for pin in pins:
                    GPIO.setup(pin, GPIO.OUT, initial=off)
        except Exception:
            self.close()
            raise

    def read(self, slot):
        dht = self.sensors[slot]
        try:
            t, h = dht.temperature, dht.humidity
            if t is None or h is None:
                return None, None, False
            return float(t), float(h), True
        except RuntimeError:
            return None, None, False

    def set_fan(self, slot, on):
        level = self.GPIO.HIGH if bool(on) == FAN_ACTIVE_HIGH else self.GPIO.LOW
        for pin in FAN_PINS[slot]:
            self.GPIO.output(pin, level)

    def close(self):
        for dht in getattr(self, 'sensors', {}).values():
            dht.exit()
        if hasattr(self, 'GPIO'):
            self.GPIO.cleanup()
