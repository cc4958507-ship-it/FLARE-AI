"""NASA PSI-69 FLEX-007 tabulated image measurements, not a safety profile."""
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1] / 'data' / 'nasa' / 'PSI-69' / 'FLEX-007'
PARSER_VERSION = 'psi69-flex007-tsv-v1'
# Unit-bearing NASA column names are the authority; standoff units are unspecified.
TABLES = {
    'FLEX-007_DropletData.txt': ('DropletTime_sec', {
        'DropletDiameter_mm': 'droplet_diameter',
        'ZeroedDropletXpos_mm': 'zeroed_droplet_x',
        'ZeroedDropletYpos_mm': 'zeroed_droplet_y'}),
    'FLEX-007_ColorCamData.txt': ('ColorCamTime_sec', {
        'ColorCamFlameDiameter_mm': 'color_flame_diameter'}),
    'FLEX-007_LLUVData.txt': ('LLUVTime_sec', {
        'LLUVFlameDiameter_mm': 'lluv_flame_diameter',
        'DropletXpos_mm': 'droplet_x', 'DropletZpos_mm': 'droplet_z'}),
}


def number(value, locator):
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f'Invalid number: {locator}') from exc
    if not result.is_finite():
        raise ValueError(f'Nonfinite value: {locator}')
    return result


def load_flex(root=BUNDLE):
    root = Path(root)
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    artifacts = []
    for entry in manifest['files']:
        name = entry['name']
        if Path(name).name != name:
            raise ValueError('Invalid source filename')
        content = (root / name).read_bytes()
        if hashlib.sha256(content).hexdigest() != entry['sha256'] or len(content) != entry['bytes']:
            raise ValueError(f'Source checksum or size mismatch: {name}')
        artifacts.append({'name': name, 'content': content, 'metadata': entry})
    contents = {a['name']: a['content'] for a in artifacts}
    tables = []
    skipped = []
    for name, (time_column, columns) in TABLES.items():
        reader = csv.DictReader(io.StringIO(contents[name].decode('utf-8-sig'), newline=''), delimiter='\t')
        fields = reader.fieldnames or []
        allowed_extra = {'ColorCamFlameStandoff', 'LLUVFlameStandoff'}
        if not {time_column, *columns} <= set(fields) or set(fields) - {time_column, *columns} - allowed_extra:
            raise ValueError(f'Unexpected source schema: {name}')
        for column in set(fields) & allowed_extra:
            skipped.append({'file': name, 'column': column, 'reason': 'UNIT_NOT_DECLARED_IN_HEADER'})
        previous = None
        rows = []
        for seq, row in enumerate(reader):
            locator = f'{name}:{seq + 2}'
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f'Malformed row: {locator}')
            timestamp = number(row[time_column], locator)
            if previous is not None and timestamp <= previous:
                raise ValueError(f'Non-increasing source time: {locator}')
            previous = timestamp
            rows.append((seq, timestamp, row))
        if not rows:
            raise ValueError(f'Empty source table: {name}')
        tables.append((name, columns, rows))
    origin = min(rows[0][1] for _, _, rows in tables)
    accepted = []
    for name, columns, rows in tables:
        previous_ms = -1
        for seq, timestamp, row in rows:
            t_ms = int(((timestamp - origin) * 1000).to_integral_value(rounding=ROUND_HALF_UP))
            if t_ms <= previous_ms or t_ms > 2147483647:
                raise ValueError(f'Timestamp collision or overflow after millisecond conversion: {name}:{seq + 2}')
            previous_ms = t_ms
            for column, channel in columns.items():
                original = row[column].strip()
                value = number(original, f'{name}:{seq + 2}:{column}') if original else None
                if value is not None and ('Diameter' in column and value < 0 or abs(value) > Decimal('1e6')):
                    raise ValueError(f'Out-of-range length: {name}:{seq + 2}:{column}')
                accepted.append({'channel': channel, 'sensor_id': name.removesuffix('.txt'),
                    'seq': seq, 't_rel_ms': t_ms, 'value': float(value / 1000) if value is not None else None,
                    'original_value': row[column], 'original_unit': 'mm', 'unit': 'm',
                    'quality': 'missing' if value is None else 'valid',
                    'source_time_sec': row[TABLES[name][0]], 'source_file': name,
                    'source_line': seq + 2, 'source_column': column})
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['channel', 'sensor_id', 'seq', 't_rel_ms', 'value', 'unit'])
    for s in accepted:
        writer.writerow([s[k] for k in ('channel', 'sensor_id', 'seq', 't_rel_ms', 'value', 'unit')])
    normalized_csv = output.getvalue()
    report = {'parser_version': PARSER_VERSION,
        'sha256': hashlib.sha256(normalized_csv.encode()).hexdigest(),
        'accepted': accepted, 'accepted_rows': len(accepted),
        'missing_rows': sum(s['value'] is None for s in accepted),
        'quarantine': [], 'quarantined_rows': 0, 'duplicate_rows': 0,
        'excluded_columns': skipped, 'mode': 'Replay Only', 'verification_eligible': False,
        'time_reference': {'source_origin_sec': str(origin), 'rule': 't_rel_ms = round_half_up((source_time_sec - source_origin_sec) * 1000)',
                           'meaning': 'Earliest supplied observation, not ignition or extinction time.'},
        'channels': [{'channel': c, 'source_file': f, 'source_column': col, 'unit':'m', 'source_unit':'mm'} for f, cols, _ in tables for col, c in cols.items()],
        'limitations': manifest['limitations']}
    return manifest, report, normalized_csv, artifacts
