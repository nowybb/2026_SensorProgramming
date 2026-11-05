
"""HC-SR04 초음파 센서 거리 측정 모듈."""

import time

# 임시 GPIO 번호 (BCM 기준)
# {칸 번호: (TRIG 핀, ECHO 핀)}
DEFAULT_HCSR04_PINS = {
    1: (23, 24),
    2: (27, 22),
}


class HCSR04Reader:
    def __init__(
        self,
        pin_map=None,
        *,
        gpio=None,
        timeout_seconds=0.03,
    ):
        if pin_map is None:
            pin_map = DEFAULT_HCSR04_PINS

        self.pin_map = dict(pin_map)

        if not self.pin_map:
            raise ValueError("센서 핀 매핑이 비어 있습니다.")

        all_pins = [
            pin
            for pair in self.pin_map.values()
            for pin in pair
        ]

        if len(all_pins) != len(set(all_pins)):
            raise ValueError("GPIO 핀이 중복되었습니다.")

        if not 0.001 <= timeout_seconds <= 0.1:
            raise ValueError("타임아웃 설정 오류")

        if gpio is None:
            import RPi.GPIO as gpio

        self.gpio = gpio
        self.timeout_seconds = timeout_seconds
        self._owned_pins = []

        mode = gpio.getmode()

        if mode not in (None, gpio.BCM):
            raise RuntimeError(
                "현재 GPIO 모드가 BCM이 아닙니다."
            )

        gpio.setmode(gpio.BCM)

        try:
            for trig_pin, echo_pin in self.pin_map.values():
                gpio.setup(
                    trig_pin,
                    gpio.OUT,
                    initial=gpio.LOW,
                )
                self._owned_pins.append(trig_pin)

                gpio.setup(echo_pin, gpio.IN)
                self._owned_pins.append(echo_pin)

        except Exception:
            self.close()
            raise

    def measure(self, compartment_id):
        """센서 거리(cm) 반환. 오류 시 None 반환."""

        trig, echo = self.pin_map[compartment_id]
        gpio = self.gpio

        # 초음파 송신
        gpio.output(trig, gpio.LOW)
        time.sleep(0.000002)

        gpio.output(trig, gpio.HIGH)
        time.sleep(0.000010)
        gpio.output(trig, gpio.LOW)

        # ECHO 신호 시작 대기
        deadline = time.monotonic() + self.timeout_seconds

        while gpio.input(echo) == gpio.LOW:
            if time.monotonic() >= deadline:
                return None

        pulse_start = time.monotonic()

        # ECHO 신호 종료 대기
        deadline = pulse_start + self.timeout_seconds

        while gpio.input(echo) == gpio.HIGH:
            if time.monotonic() >= deadline:
                return None

        pulse_end = time.monotonic()

        # 거리 계산 (cm)
        distance_cm = (
            (pulse_end - pulse_start) * 34300.0 / 2.0
        )

        if not 2.0 <= distance_cm <= 400.0:
            return None

        return round(distance_cm, 2)

    def close(self):
        """본 모듈이 사용한 GPIO만 정리."""

        if self._owned_pins:
            self.gpio.cleanup(self._owned_pins)
            self._owned_pins.clear()
