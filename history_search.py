import csv
import argparse
from datetime import datetime

HISTORY_CSV = 'event_history.csv'

def parse_args():
    parser = argparse.ArgumentParser(description='Search traffic history records')
    parser.add_argument('--start', help='Start time YYYY-mm-dd HH:MM:SS')
    parser.add_argument('--end', help='End time YYYY-mm-dd HH:MM:SS')
    parser.add_argument('--vehicle', help='Filter by vehicle type')
    parser.add_argument('--with-plate', action='store_true', help='Only records with plate number')
    parser.add_argument('--no-plate', action='store_true', help='Only records without plate number')
    return parser.parse_args()

def parse_time(value):
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

def load_records(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row

def match(row, start, end, vehicle, with_plate, no_plate):
    dt = datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S')
    if start and dt < start:
        return False
    if end and dt > end:
        return False
    if vehicle and vehicle not in row['vehicle_type']:
        return False
    plate = row['plate_number'].strip()
    if with_plate and not plate:
        return False
    if no_plate and plate:
        return False
    return True

def main():
    args = parse_args()
    start = parse_time(args.start)
    end = parse_time(args.end)
    path = HISTORY_CSV
    for row in load_records(path):
        if match(row, start, end, args.vehicle, args.with_plate, args.no_plate):
            print(f"{row['time']} | {row['plate_number']} | {row['vehicle_type']} | {row['global_img']} | {row['small_img']}")

if __name__ == '__main__':
    main()
