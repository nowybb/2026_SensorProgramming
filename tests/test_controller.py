import unittest
from datetime import datetime, timedelta
from controller import CabinetState

class ControllerTests(unittest.TestCase):
    def test_start_and_stop(self):
        s = CabinetState(1)
        now = datetime.now()
        for i in range(3):
            s.update(True, 24, 75, now + timedelta(seconds=i))
        self.assertTrue(s.fan_on)
        self.assertEqual(s.state, 'DRYING')
        for i in range(3):
            s.update(True, 24, 50, now + timedelta(seconds=10+i))
        self.assertFalse(s.fan_on)
        self.assertEqual(s.state, 'DONE')

    def test_sensor_failure_stops(self):
        s = CabinetState(1)
        now = datetime.now()
        for i in range(3):
            s.update(True, 24, 75, now + timedelta(seconds=i))
        s.update(True, None, None, now + timedelta(seconds=4), valid=False)
        self.assertFalse(s.fan_on)
        self.assertEqual(s.state, 'SENSOR_ERROR')

    def test_shoe_removed(self):
        s = CabinetState(2)
        now = datetime.now()
        for i in range(3):
            s.update(True, 24, 80, now + timedelta(seconds=i))
        e = s.update(False, 24, 80, now + timedelta(seconds=4))
        self.assertEqual(s.state, 'EMPTY')
        self.assertFalse(s.fan_on)
        self.assertIn('SHOE_OUT', e)

if __name__ == '__main__':
    unittest.main()
