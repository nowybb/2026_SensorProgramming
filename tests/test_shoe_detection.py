
"""신발 감지 모듈 단위 테스트."""

import unittest

from dataclasses import asdict

from common.enums import EventType, ShoeStatus

from modules.shoe_detection.detector import ShoeDetector
from modules.shoe_detection.service import ShoeDetectionService


class FakeReader:
    pin_map = {1: None, 2: None}

    def __init__(self, distances):
        self.distances = distances

    def measure(self, slot):
        return self.distances[slot]


class ShoeDetectionTests(unittest.TestCase):

    def setUp(self):
        self.detector = ShoeDetector()

    def feed(self, slot, distances):
        return [
            self.detector.update(slot, d)
            for d in distances
        ]

    # 1. 최초 상태 확인
    def test_initial_measurement_is_not_an_entry(self):
        states = self.feed(1, [25, 25, 25])

        self.assertEqual(
            states[-1].detection.shoe_status,
            ShoeStatus.EMPTY,
        )

        self.assertTrue(
            all(x.event is None for x in states)
        )

    # 2. 입고 및 출고 감지
    def test_entry_and_exit_events_once(self):
        self.feed(1, [25, 25, 25])

        incoming = self.feed(
            1, [10, 10, 10, 10]
        )

        outgoing = self.feed(
            1, [25, 25, 25, 25]
        )

        self.assertEqual(
            [x.event.event_type for x in incoming if x.event],
            [EventType.SHOE_IN],
        )

        self.assertEqual(
            [x.event.event_type for x in outgoing if x.event],
            [EventType.SHOE_OUT],
        )

        self.assertEqual(
            incoming[2].event.compartment_id,
            1,
        )

        self.assertEqual(
            self.detector.get_status(1),
            ShoeStatus.EMPTY,
        )

    # 3. 일시적인 거리 오차 무시
    def test_debounce_ignores_single_spike(self):
        self.feed(1, [25, 25, 25])

        seq = self.feed(
            1, [10, 25, 10, 25]
        )

        self.assertTrue(
            all(
                x.detection.shoe_status == ShoeStatus.EMPTY
                for x in seq
            )
        )

        self.assertTrue(
            all(x.event is None for x in seq)
        )

    # 4. 거리 경계 구간
    def test_gray_zone_maintains_previous_state(self):
        self.feed(1, [25, 25, 25])

        seq = self.feed(
            1, [17, 17, 17]
        )

        self.assertTrue(
            all(
                x.detection.shoe_status == ShoeStatus.EMPTY
                for x in seq
            )
        )

    # 5. 센서 오류 처리
    def test_timeout_yields_unknown_not_false_checkout(self):
        self.feed(1, [10, 10, 10])

        error = self.detector.update(1, None)

        self.assertEqual(
            error.detection.shoe_status,
            ShoeStatus.UNKNOWN,
        )

        self.assertIsNone(error.event)

        recovery = self.feed(
            1, [25, 25, 25]
        )

        self.assertEqual(
            recovery[-1].detection.shoe_status,
            ShoeStatus.EMPTY,
        )

        self.assertTrue(
            all(x.event is None for x in recovery)
        )

    # 6. 두 칸 독립 감지
    def test_two_compartments_independent(self):
        self.feed(1, [25, 25, 25])
        self.feed(2, [25, 25, 25])

        results = self.feed(
            2, [12, 12, 12]
        )

        self.assertEqual(
            self.detector.get_status(1),
            ShoeStatus.EMPTY,
        )

        self.assertEqual(
            self.detector.get_status(2),
            ShoeStatus.OCCUPIED,
        )

        self.assertEqual(
            results[-1].event.compartment_id,
            2,
        )

    # 7. GitHub 공통 데이터 규격 확인
    def test_common_data_contract(self):
        data = self.feed(
            1, [10, 10, 10]
        )[-1].detection

        payload = asdict(data)

        self.assertEqual(
            set(payload),
            {
                "compartment_id",
                "distance_cm",
                "shoe_status",
                "detected_at",
            },
        )

        self.assertEqual(
            payload["shoe_status"],
            "OCCUPIED",
        )

    # 8. 비정상 거리값 처리
    def test_invalid_values(self):
        for bad in (
            float("nan"),
            float("inf"),
            -1,
            401,
            True,
        ):
            value = self.detector.update(1, bad)

            self.assertEqual(
                value.detection.shoe_status,
                ShoeStatus.UNKNOWN,
            )

            self.assertIsNone(value.event)

    # 9. 센서와 칸 번호 매핑
    def test_service_matches_pin_map(self):
        reader = FakeReader({
            1: 25.0,
            2: 10.0,
        })

        service = ShoeDetectionService(
            reader,
            between_sensors_seconds=0,
        )

        for _ in range(3):
            results = service.poll_all()

        self.assertEqual(
            [
                x.detection.compartment_id
                for x in results
            ],
            [1, 2],
        )

        self.assertEqual(
            [
                x.detection.shoe_status
                for x in results
            ],
            [
                ShoeStatus.EMPTY,
                ShoeStatus.OCCUPIED,
            ],
        )


if __name__ == "__main__":
    unittest.main()
