### Bring Old Fitbit Data to Strava

This is a script to generate **`.GPX`** files from the **old** [**Fitbit**](https://www.fitbit.com/) data, so that it can be imported into [**Strava**](https://www.strava.com/). 

- Save the script as `script_name.py` and run it next to the `Takeout` directory. 

**Script** 

```bash
import bisect
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

if sys.platform == 'win32':
    RAW_ROOT = Path(r"c:\Users\MAK\Downloads\Takeout\Fitbit")
else:
    RAW_ROOT = Path("/mnt/c/Users/MAK/Downloads/Takeout/Fitbit")

HEALTH_DATA_DIR = RAW_ROOT / "Health Fitness Data_GoogleData"
JSON_DATA_DIR = RAW_ROOT / "Global Export Data"
GPS_DATA_DIR = RAW_ROOT / "Physical Activity_GoogleData"
HEART_RATE_DIR = GPS_DATA_DIR
OUTPUT_DIR = RAW_ROOT / "Workout_GPX_Exports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_csv_datetime(value: str):
    if not value:
        return None
    try:
        if value.endswith('Z'):
            value = value[:-1] + '+00:00'
        return datetime.fromisoformat(value)
    except ValueError:
        return None

def parse_json_start(value: str):
    if not value:
        return None
    for fmt in ['%m/%d/%y %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None

def load_exercise_metadata():
    rows = []
    for csv_file in sorted(HEALTH_DATA_DIR.glob('UserExercises_*.csv')):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                exercise_id = row.get('exercise_id')
                if not exercise_id:
                    continue
                start_time = parse_csv_datetime(row.get('exercise_start', ''))
                end_time = parse_csv_datetime(row.get('exercise_end', ''))
                if not start_time or not end_time:
                    continue
                rows.append({
                    'exercise_id': exercise_id,
                    'activity_name': row.get('activity_name', 'Unknown'),
                    'start_time': start_time,
                    'end_time': end_time,
                    'utc_offset': row.get('utc_offset', ''),
                    'cutoff_time': end_time,
                    'source_csv': csv_file.name,
                    'row': row,
                })
    return rows

def load_gps_points():
    gps_by_date = {}
    for csv_file in sorted(GPS_DATA_DIR.glob('gps_location_*.csv')):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                    lat = float(row['latitude'])
                    lon = float(row['longitude'])
                    ele = float(row['altitude'])
                except Exception:
                    continue
                date_key = ts.date()
                gps_by_date.setdefault(date_key, []).append({
                    'timestamp': ts,
                    'latitude': lat,
                    'longitude': lon,
                    'altitude': ele,
                })
    for pts in gps_by_date.values():
        pts.sort(key=lambda p: p['timestamp'])
    return gps_by_date

def load_heart_rate_data():
    heart_rate_by_date = {}
    for csv_file in sorted(HEART_RATE_DIR.glob('heart_rate_*.csv')):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                    bpm = int(float(row['beats per minute']))
                except Exception:
                    continue
                date_key = ts.date()
                heart_rate_by_date.setdefault(date_key, []).append({
                    'timestamp': ts,
                    'bpm': bpm,
                })
    for date_key, hrs in list(heart_rate_by_date.items()):
        hrs.sort(key=lambda h: h['timestamp'])
        heart_rate_by_date[date_key] = {
            'records': hrs,
            'timestamps': [h['timestamp'] for h in hrs],
        }
    return heart_rate_by_date

def find_nearest_heart_rate(timestamp, heart_rate_by_date, max_delta=timedelta(seconds=30)):
    best = None
    best_delta = max_delta
    for day_offset in (-1, 0, 1):
        day = (timestamp + timedelta(days=day_offset)).date()
        hr_day = heart_rate_by_date.get(day)
        if not hr_day:
            continue
        timestamps = hr_day['timestamps']
        hrs = hr_day['records']
        index = bisect.bisect_left(timestamps, timestamp)
        candidates = []
        if index > 0:
            candidates.append(hrs[index - 1])
        if index < len(hrs):
            candidates.append(hrs[index])
        for hr in candidates:
            delta = abs(hr['timestamp'] - timestamp)
            if delta < best_delta:
                best = hr
                best_delta = delta
                if delta == timedelta(0):
                    return best
    return best

def build_csv_index(metadata_rows):
    index = {}
    for row in metadata_rows:
        key = row['start_time'].isoformat()
        index.setdefault(key, []).append(row)
    return index

def match_activity_to_csv(activity, csv_index):
    key = activity['start_time'].isoformat()
    candidates = csv_index.get(key, [])
    if candidates:
        return candidates[0]
    best = None
    best_delta = timedelta.max
    for rows in csv_index.values():
        for candidate in rows:
            delta = abs(candidate['start_time'] - activity['start_time'])
            if delta < best_delta and delta <= timedelta(seconds=5):
                best = candidate
                best_delta = delta
    return best

def parse_exercise_json():
    activities = []
    for json_file in sorted(JSON_DATA_DIR.glob('exercise-*.json')):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for item in data:
            start_time = parse_json_start(item.get('startTime') or item.get('originalStartTime') or '')
            duration_ms = None
            for field in ['duration', 'originalDuration', 'activeDuration']:
                if field in item and item[field] is not None:
                    try:
                        duration_ms = int(item[field])
                        break
                    except (ValueError, TypeError):
                        continue
            if not start_time or duration_ms is None:
                continue
            activities.append({
                'json_file': json_file.name,
                'logId': str(item.get('logId', '')),
                'activityTypeId': str(item.get('activityTypeId', '')),
                'activityName': item.get('activityName', 'Unknown'),
                'start_time': start_time,
                'duration_seconds': int(duration_ms / 1000),
                'end_time': start_time + timedelta(milliseconds=duration_ms),
                'hasGps': bool(item.get('hasGps', False)),
                'raw': item,
            })
    return activities

def build_gpx(activity, points):
    gpx = ET.Element('gpx', {
        'version': '1.1',
        'creator': 'Fitbit Exercise JSON GPX Export',
        'xmlns': 'http://www.topografix.com/GPX/1/1',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xmlns:gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1',
        'xsi:schemaLocation': 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd',
    })
    metadata = ET.SubElement(gpx, 'metadata')
    time_elem = ET.SubElement(metadata, 'time')
    time_elem.text = activity['start_time'].isoformat().replace('+00:00', 'Z')
    trk = ET.SubElement(gpx, 'trk')
    name = ET.SubElement(trk, 'name')
    name.text = f"{activity['activityName']}"
    cmt = ET.SubElement(trk, 'cmt')
    cmt.text = activity['activityName']
    desc = ET.SubElement(trk, 'desc')
    desc.text = (
        f"Source JSON: {activity['json_file']} | "
        f"Duration: {activity['duration_seconds']}s | "
        f"LogId: {activity['logId']} | ActivityTypeId: {activity['activityTypeId']}"
    )
    trkseg = ET.SubElement(trk, 'trkseg')
    for point in points:
        trkpt = ET.SubElement(trkseg, 'trkpt', {
            'lat': f"{point['latitude']:.7f}",
            'lon': f"{point['longitude']:.7f}",
        })
        ele = ET.SubElement(trkpt, 'ele')
        ele.text = f"{point['altitude']:.1f}"
        ts_elem = ET.SubElement(trkpt, 'time')
        ts_elem.text = point['timestamp'].isoformat().replace('+00:00', 'Z')
        if point.get('heart_rate') is not None:
            extensions = ET.SubElement(trkpt, 'extensions')
            tpe = ET.SubElement(extensions, 'gpxtpx:TrackPointExtension')
            hr_elem = ET.SubElement(tpe, 'gpxtpx:hr')
            hr_elem.text = str(point['heart_rate'])
    indent_xml(gpx)
    return ET.tostring(gpx, encoding='unicode')

def indent_xml(element, level=0):
    indent = '\n' + ('  ' * level)
    if len(element):
        if not element.text or not element.text.strip():
            element.text = indent + '  '
        for child in element:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not element.tail or not element.tail.strip()):
            element.tail = indent

def points_for_activity(activity, gps_by_date, heart_rate_by_date):
    if not gps_by_date:
        return []
    start = activity['start_time']
    end = activity['end_time']
    buffer = timedelta(seconds=5)
    pts = []
    for day_offset in (-1, 0, 1):
        day = (start + timedelta(days=day_offset)).date()
        for point in gps_by_date.get(day, []):
            if start - buffer <= point['timestamp'] <= end + buffer:
                pts.append(point)
    pts.sort(key=lambda p: p['timestamp'])
    for point in pts:
        hr = find_nearest_heart_rate(point['timestamp'], heart_rate_by_date)
        if hr:
            point['heart_rate'] = hr['bpm']
    return pts

def filename_for_activity(activity, exercise_id, cutoff_time):
    start_str = activity['start_time'].strftime('%Y%m%dT%H%M%SZ')
    end_str = activity['end_time'].strftime('%Y%m%dT%H%M%SZ')
    cutoff_str = cutoff_time.strftime('%Y%m%dT%H%M%SZ')
    return (
        f"{exercise_id}_{start_str}_{end_str}_{activity['duration_seconds']}s_"
        f"{cutoff_str}_{activity['logId']}_{activity['activityTypeId']}.gpx"
    )

def main():
    print('Loading exercise metadata from CSV...')
    csv_rows = load_exercise_metadata()
    csv_index = build_csv_index(csv_rows)
    print(f'  Loaded {len(csv_rows)} exercise metadata rows.')

    print('Loading exercise JSON logs...')
    activities = parse_exercise_json()
    print(f'  Loaded {len(activities)} JSON activity entries.')

    print('Matching JSON activities to CSV exercise IDs...')
    matched = []
    unmatched = []
    for activity in activities:
        csv_match = match_activity_to_csv(activity, csv_index)
        if csv_match:
            activity['exercise_id'] = csv_match['exercise_id']
            activity['csv_start_time'] = csv_match['start_time']
            activity['csv_end_time'] = csv_match['end_time']
            activity['cutoff_time'] = csv_match['cutoff_time']
            activity['csv_activity_name'] = csv_match['activity_name']
            matched.append(activity)
        else:
            unmatched.append(activity)

    print(f'  Matched {len(matched)} activities, {len(unmatched)} unmatched.')

    print('Loading GPS point data...')
    gps_by_date = load_gps_points()
    total_points = sum(len(v) for v in gps_by_date.values())
    print(f'  Loaded {total_points} GPS points on {len(gps_by_date)} days.')

    print('Loading heart rate point data...')
    heart_rate_by_date = load_heart_rate_data()
    total_hr_points = sum(len(v['records']) for v in heart_rate_by_date.values())
    print(f'  Loaded {total_hr_points} heart rate points on {len(heart_rate_by_date)} days.')

    report_path = OUTPUT_DIR / 'exercise_json_gpx_summary.csv'
    with open(report_path, 'w', newline='', encoding='utf-8') as summary_file:
        writer = csv.writer(summary_file)
        writer.writerow([
            'exercise_id', 'json_file', 'logId', 'activityTypeId', 'activityName',
            'csv_start_time', 'csv_end_time', 'csv_cutoff_time', 'json_start_time',
            'json_end_time', 'duration_seconds', 'matched', 'gps_point_count', 'hr_point_count', 'gpx_file'
        ])

        generated = 0
        for activity in matched:
            points = points_for_activity(activity, gps_by_date, heart_rate_by_date)
            gpx_file_name = None
            if points:
                gpx_file_name = filename_for_activity(activity, activity['exercise_id'], activity['cutoff_time'])
                gpx_content = build_gpx(activity, points)
                path = OUTPUT_DIR / gpx_file_name
                with open(path, 'w', encoding='utf-8') as out_f:
                    out_f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                    out_f.write(gpx_content)
                generated += 1
            writer.writerow([
                activity['exercise_id'],
                activity['json_file'],
                activity['logId'],
                activity['activityTypeId'],
                activity['activityName'],
                activity.get('csv_start_time').isoformat() if activity.get('csv_start_time') else '',
                activity.get('csv_end_time').isoformat() if activity.get('csv_end_time') else '',
                activity.get('cutoff_time').isoformat().replace('+00:00', 'Z') if activity.get('cutoff_time') else '',
                activity['start_time'].isoformat().replace('+00:00', 'Z'),
                activity['end_time'].isoformat().replace('+00:00', 'Z'),
                activity['duration_seconds'],
                'yes',
                len(points),
                sum(1 for p in points if p.get('heart_rate') is not None),
                gpx_file_name or '',
            ])

    if unmatched:
        print('WARNING: Some JSON activities did not match a CSV exercise row.')
        for activity in unmatched[:10]:
            print(f"  Unmatched logId={activity['logId']} start={activity['start_time'].isoformat()} duration={activity['duration_seconds']}s")
        if len(unmatched) > 10:
            print(f'  ... plus {len(unmatched)-10} more')

    print(f'Generated {generated} GPX files to {OUTPUT_DIR}')
    print(f'Summary saved to {report_path}')

if __name__ == '__main__':
    main()

```