"""Explicit long-form CSV contract; imports never enter synthetic verification."""
import csv
import hashlib
import io
import math
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

PARSER_VERSION = 'csv-long-v1'
UNITS = {'Pa': ('Pa', 1, 0), 'kPa': ('Pa', 1000, 0),
         'K': ('K', 1, 0), 'degC': ('K', 1, 273.15),
         'ppm': ('fraction', 0.000001, 0), 'fraction': ('fraction', 1, 0),
         'm/s': ('m/s', 1, 0), 'm': ('m', 1, 0), 'mm': ('m', 0.001, 0)}


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    license: str = Field(min_length=1, max_length=2000)
    origin: Literal['NASA raw', 'experimental', 'synthetic']
    csv_text: str = Field(min_length=1, max_length=2_000_000)


def parse_csv(raw: str):
    reader = csv.DictReader(io.StringIO(raw, newline=''))
    expected = ['channel', 'sensor_id', 'seq', 't_rel_ms', 'value', 'unit']
    if reader.fieldnames != expected:
        raise ValueError('CSV header must be: ' + ','.join(expected))
    accepted, quarantine, seen, last, units = [], [], {}, {}, {}
    duplicates = 0
    for line, row in enumerate(reader, 2):
        if line > 10001:
            raise ValueError('At most 10000 measurement rows per import')
        if None in row or any(v is None for v in row.values()):
            raise ValueError(f'Malformed CSV row {line}')
        try:
            channel, sensor = row['channel'].strip(), row['sensor_id'].strip()
            if not channel or not sensor or max(len(channel), len(sensor)) > 120:
                raise ValueError('Invalid channel or sensor identity')
            seq, t = int(row['seq']), int(row['t_rel_ms'])
            if not 0 <= seq <= 2147483647 or not 0 <= t <= 2147483647:
                raise ValueError('Sequence and time must be nonnegative 32-bit integers')
            value = float(row['value']) if row['value'].strip() else None
            if value is not None and not math.isfinite(value):
                raise ValueError('Non-finite values must be represented as empty cells')
        except ValueError as exc:
            raise ValueError(f'Row {line}: {exc}') from exc
        identity = (channel, sensor)
        key = (*identity, seq)
        if key in seen:
            if seen[key] != row:
                raise ValueError(f'Conflicting duplicate identity at row {line}')
            duplicates += 1
            continue
        seen[key] = row
        reason = None
        if row['unit'] not in UNITS:
            reason = 'UNKNOWN_UNIT'
        elif identity in units and units[identity] != row['unit']:
            reason = 'UNIT_CHANGED'
        elif identity in last and (t <= last[identity][0] or seq <= last[identity][1]):
            reason = 'NON_INCREASING_TIME_OR_SEQUENCE'
        if reason:
            quarantine.append({'line': line, 'reason': reason, 'raw': row})
            continue
        unit, scale, offset = UNITS[row['unit']]
        normalized = None if value is None else value * scale + offset
        if normalized is not None and (not math.isfinite(normalized) or
                (unit in ('Pa', 'K') and normalized < 0) or
                (unit == 'fraction' and not 0 <= normalized <= 1)):
            quarantine.append({'line': line, 'reason': 'OUT_OF_RANGE', 'raw': row})
            continue
        units[identity], last[identity] = row['unit'], (t, seq)
        accepted.append({'channel': channel, 'sensor_id': sensor, 'seq': seq,
                         't_rel_ms': t, 'original_value': row['value'],
                         'original_unit': row['unit'], 'value': normalized, 'unit': unit,
                         'quality': 'missing' if value is None else 'valid'})
    return {'parser_version': PARSER_VERSION, 'sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(),
            'accepted': accepted, 'quarantine': quarantine, 'duplicate_rows': duplicates,
            'accepted_rows': len(accepted), 'quarantined_rows': len(quarantine),
            'verification_eligible': False, 'mode': 'Replay Only',
            'limitations': ['Source identity and license are supplied by the importer and require review.',
                            'No calibration or combustion verification is performed.',
                            'ppm conversion assumes the documented fraction basis; review source metadata.']}
