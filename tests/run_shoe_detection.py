
"""신발 감지 모듈 단독 실행 프로그램."""

import argparse
import json
import time

from dataclasses import asdict

from modules.shoe_detection.detector import ShoeDetector
from modules.shoe_detection.service import ShoeDetectionService


class DemoReader:
    """실제 센서 없이 거리값을 생성하는 클래스."""

    pin_map = {
        1: None,
        2: None,
    }

    def __init__(self):
        self.index = 0

        # 1번 칸: 빈 칸 -> 신발 입고 -> 신발 출고
        # 2번 칸: 계속 빈 칸
        self.sequence = {
            1: [25, 25, 25, 10, 10, 10, 10, 25, 25, 25],
            2: [25] * 10,
        }

    def measure(self, compartment_id):
        seq = self.sequence[compartment_id]
        return seq[min(self.index, len(seq) - 1)]

    def next_round(self):
        self.index += 1


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--real",
        action="store_true",
        help="실제 HC-SR04 센서 사용",
    )

    parser.add_argument(
        "--rounds",
        type=int,
        default=10,
        help="측정 횟수",
    )

    parser.add_argument(
        "--occupied-max",
        type=float,
        default=15.0,
    )

    parser.add_argument(
        "--empty-min",
        type=float,
        default=19.0,
    )

    args = parser.parse_args()

    if args.rounds <= 0:
        parser.error("측정 횟수는 1 이상이어야 합니다.")

    # 실제 센서 또는 가상 센서 선택
    if args.real:
        from modules.shoe_detection.hardware import HCSR04Reader
        reader = HCSR04Reader()
    else:
        reader = DemoReader()

    detector = ShoeDetector(
        compartment_ids=reader.pin_map.keys(),
        occupied_max_cm=args.occupied_max,
        empty_min_cm=args.empty_min,
    )

    service = ShoeDetectionService(
        reader,
        detector,
    )

    try:
        for _ in range(args.rounds):
            results = service.poll_all()

            for result in results:
                output = {
                    "detection": asdict(result.detection),
                    "event": (
                        asdict(result.event)
                        if result.event
                        else None
                    ),
                }

                print(
                    json.dumps(
                        output,
                        ensure_ascii=False,
                    )
                )

            if not args.real:
                reader.next_round()

            time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    finally:
        if args.real:
            reader.close()


if __name__ == "__main__":
    main()
