import unittest
from dataclasses import asdict
from common.enums import ShoeStatus, EventType
from common.models import ShoeDetectionData, SystemEventData

class ContractTests(unittest.TestCase):
    def test_enum_serialization(self):
        d = asdict(ShoeDetectionData(1, 12.0, ShoeStatus.OCCUPIED, '2026-11-03T07:00:00+09:00'))
        self.assertEqual(d['shoe_status'], 'OCCUPIED')
    def test_event_model(self):
        e = SystemEventData('uuid', EventType.SHOE_IN, 1, 1, None, '2026-11-03T07:00:00+09:00')
        self.assertEqual(e.details, {})
