"""뽀송 자동 건조 모듈. 기본은 시뮬레이션이며 실제 팬은 --real 옵션이 필요."""
import argparse
import csv
import json
import math
import random
import time
from datetime import datetime
from pathlib import Path
from config import SAMPLE_SECONDS, LOG_SECONDS
from controller import CabinetState

FIELDS = ['timestamp', 'slot', 'shoe_present', 'temperature', 'humidity', 'fan_on', 'state', 'events']


def run(simulate=True):
    hardware = None
    if not simulate:
        from hardware import RealHardware
        hardware = RealHardware()
    states = {slot: CabinetState(slot) for slot in (1, 2)}
    output = Path(__file__).parent / 'data'
    output.mkdir(exist_ok=True)
    csv_path = output / 'readings.csv'
    status_path = output / 'status.json'
    existing = csv_path.exists()
    t0 = time.monotonic()
    last_log = -LOG_SECONDS
    print('MODE:', 'SIMULATION (팬 미작동)' if simulate else 'REAL HARDWARE')
    try:
        with csv_path.open('a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            if not existing or csv_path.stat().st_size == 0:
                writer.writeheader()
            while True:
                elapsed = time.monotonic() - t0
                now = datetime.now()
                snapshot = {'timestamp': now.isoformat(timespec='seconds'), 'slots': {}}
                for slot, obj in states.items():
                    if simulate:
                        # 1번 칸에 신발이 있다고 가정. 2번 칸은 비어 있음.
                        shoe = slot == 1
                        humidity = max(49.0, 76.0 - elapsed * .13) if shoe else 48.0
                        temperature, valid = 24.0, True
                    else:
                        # 담당 팀원의 shoe detection 출력과 연동 전까지 임의 팬 가동 금지
                        shoe = False
                        temperature, humidity, valid = hardware.read(slot)
                    events = obj.update(shoe, temperature, humidity, now, valid=valid)
                    if hardware:
                        hardware.set_fan(slot, obj.fan_on)
                    row = dict(timestamp=now.isoformat(timespec='seconds'), slot=slot,
                               shoe_present=obj.shoe_present, temperature=obj.temperature,
                               humidity=obj.humidity, fan_on=obj.fan_on,
                               state=obj.state, events='|'.join(events))
                    if elapsed - last_log >= LOG_SECONDS:
                        writer.writerow(row)
                        f.flush()
                    snapshot['slots'][str(slot)] = row
                    if events:
                        print(f'[{now:%H:%M:%S}] {slot}번 칸: {events}')
                if elapsed - last_log >= LOG_SECONDS:
                    last_log = elapsed
                temp_file = status_path.with_suffix('.tmp')
                temp_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
                temp_file.replace(status_path)
                print(' | '.join(f'{i}번 {o.state} {o.humidity}% FAN={o.fan_on}' for i, o in states.items()))
                time.sleep(SAMPLE_SECONDS)
    except KeyboardInterrupt:
        print('종료합니다.')
    finally:
        if hardware:
            for slot in states:
                hardware.set_fan(slot, False)
            hardware.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--simulate', action='store_true', help='가상 센서로 안전 테스트 (기본값)')
    group.add_argument('--real', action='store_true', help='실제 GPIO 연결, 신발 감지 연동 전 팬 미작동')
    args = parser.parse_args()
    run(simulate=not args.real)
