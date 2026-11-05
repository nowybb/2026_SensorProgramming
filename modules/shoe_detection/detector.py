
"""신발 감지 및 입·출고 판단 로직."""

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Optional
from uuid import uuid4

from common.enums import EventType, ShoeStatus
from common.models import ShoeDetectionData, SystemEventData


@dataclass(frozen=True)
class ShoeDetectionResult:
    detection: ShoeDetectionData
    event: Optional[SystemEventData] = None


class ShoeDetector:
    def __init__(
        self,
        compartment_ids=(1, 2),
        *,
        cabinet_id=1,
        occupied_max_cm=15.0,
        empty_min_cm=19.0,
        confirmations=3,
    ):
        ids = tuple(compartment_ids)

        if (
            not ids
            or len(ids) != len(set(ids))
            or not all(isinstance(i, int) and i > 0 for i in ids)
        ):
            raise ValueError("칸 번호는 중복 없는 양의 정수여야 합니다.")

        if not 2.0 <= occupied_max_cm < empty_min_cm <= 400.0:
            raise ValueError("거리 기준값 설정이 올바르지 않습니다.")

        if confirmations < 1:
            raise ValueError("confirmations는 1 이상이어야 합니다.")

        if cabinet_id < 1:
            raise ValueError("cabinet_id는 1 이상이어야 합니다.")

        self.compartment_ids = ids
        self.cabinet_id = cabinet_id
        self.occupied_max_cm = float(occupied_max_cm)
        self.empty_min_cm = float(empty_min_cm)
        self.confirmations = confirmations

        # 칸별 현재 상태 및 연속 측정 횟수
        self._status = {
            i: ShoeStatus.UNKNOWN for i in ids
        }
        self._candidate = {
            i: None for i in ids
        }
        self._count = {
            i: 0 for i in ids
        }

    def get_status(self, compartment_id):
        return self._status[compartment_id]

    def update(
        self,
        compartment_id,
        distance_cm,
        *,
        detected_at=None,
    ):
        if compartment_id not in self._status:
            raise ValueError(
                f"등록되지 않은 칸 번호: {compartment_id}"
            )

        if detected_at is None:
            detected_at = (
                datetime.now()
                .astimezone()
                .isoformat(timespec="seconds")
            )

        old = self._status[compartment_id]

        # 잘못된 측정값은 신발 없음으로 처리하지 않음
        if (
            isinstance(distance_cm, bool)
            or not isinstance(distance_cm, (int, float))
            or not isfinite(distance_cm)
            or not 2.0 <= distance_cm <= 400.0
        ):
            self._status[compartment_id] = ShoeStatus.UNKNOWN
            self._candidate[compartment_id] = None
            self._count[compartment_id] = 0

            return self._result(
                compartment_id, None, detected_at
            )

        distance = float(distance_cm)

        # 신발 유무 판단
        if distance <= self.occupied_max_cm:
            candidate = ShoeStatus.OCCUPIED

        elif distance >= self.empty_min_cm:
            candidate = ShoeStatus.EMPTY

        else:
            # 경계 구간에서는 기존 확정 상태 유지
            self._candidate[compartment_id] = None
            self._count[compartment_id] = 0

            return self._result(
                compartment_id, distance, detected_at
            )

        # 이전 상태와 같으면 변경하지 않음
        if candidate == old:
            self._candidate[compartment_id] = None
            self._count[compartment_id] = 0

            return self._result(
                compartment_id, distance, detected_at
            )

        # 같은 상태가 연속으로 측정되는지 확인
        if self._candidate[compartment_id] == candidate:
            self._count[compartment_id] += 1
        else:
            self._candidate[compartment_id] = candidate
            self._count[compartment_id] = 1

        event = None

        # 연속 측정 기준 충족 시 상태 확정
        if self._count[compartment_id] >= self.confirmations:
            self._status[compartment_id] = candidate
            self._candidate[compartment_id] = None
            self._count[compartment_id] = 0

            # 입고 감지
            if (
                old == ShoeStatus.EMPTY
                and candidate == ShoeStatus.OCCUPIED
            ):
                kind = EventType.SHOE_IN

            # 출고 감지
            elif (
                old == ShoeStatus.OCCUPIED
                and candidate == ShoeStatus.EMPTY
            ):
                kind = EventType.SHOE_OUT

            else:
                kind = None

            # 공통 이벤트 모델 생성
            if kind is not None:
                event = SystemEventData(
                    event_id=str(uuid4()),
                    event_type=kind,
                    cabinet_id=self.cabinet_id,
                    compartment_id=compartment_id,
                    session_id=None,
                    occurred_at=detected_at,
                    details={
                        "distance_cm": distance,
                        "previous_status": old.value,
                        "current_status": candidate.value,
                    },
                )

        return self._result(
            compartment_id, distance, detected_at, event
        )

    def _result(
        self,
        compartment_id,
        distance_cm,
        detected_at,
        event=None,
    ):
        detection = ShoeDetectionData(
            compartment_id=compartment_id,
            distance_cm=distance_cm,
            shoe_status=self._status[compartment_id],
            detected_at=detected_at,
        )

        return ShoeDetectionResult(
            detection=detection,
            event=event,
        )
