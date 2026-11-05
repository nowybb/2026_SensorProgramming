
"""초음파 센서 측정과 신발 감지 로직 연결."""

import time

from .detector import ShoeDetector


class ShoeDetectionService:
    def __init__(
        self,
        reader,
        detector=None,
        *,
        between_sensors_seconds=0.06,
    ):
        self.reader = reader

        self.detector = detector or ShoeDetector(
            compartment_ids=reader.pin_map.keys()
        )

        # 칸 번호 매핑 검사
        if (
            set(self.detector.compartment_ids)
            != set(reader.pin_map)
        ):
            raise ValueError(
                "센서 GPIO 매핑과 감지 칸 번호가 다릅니다."
            )

        if between_sensors_seconds < 0:
            raise ValueError(
                "센서 측정 간격은 음수가 될 수 없습니다."
            )

        self.between_sensors_seconds = (
            between_sensors_seconds
        )

    def poll_all(self):
        """모든 칸의 신발 감지 결과 반환."""

        results = []

        for i, slot in enumerate(
            self.detector.compartment_ids
        ):
            # 해당 칸의 초음파 거리 측정
            distance = self.reader.measure(slot)

            # 신발 상태 판단
            result = self.detector.update(
                slot,
                distance,
            )

            results.append(result)

            # 센서 간 초음파 간섭 방지
            if i < len(self.detector.compartment_ids) - 1:
                time.sleep(
                    self.between_sensors_seconds
                )

        return results
