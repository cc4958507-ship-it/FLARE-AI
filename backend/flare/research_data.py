"""Explicit adapters for supplied research sources; never a simulation safety input."""
import csv
from collections import Counter
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
from sqlalchemy import insert, select, text
from .db import Session, Dataset, SourceObservation, ResearchAsset

PARSER_VERSION = 'research-native-wide-v1'
NATIVE_FILES = {'19056A2_data.csv':'acme', '19056D2_data.csv':'acme', 'C039H03_Chamber_Readings.txt':'chamber'}


def library_root():
    return Path(os.getenv('FLARE_RESEARCH_DIR', str(Path(__file__).resolve().parents[2]/'research_data'))).resolve()


def asset_path(payload, root=None):
    root = Path(root or library_root()).resolve()
    target = (root/payload['object']).resolve()
    if not target.is_relative_to(root) or not re.fullmatch(r'objects/[a-f0-9]{64}',payload['object']):
        raise ValueError('Invalid research object path')
    return target


def parse_native(content, name):
    if name not in NATIVE_FILES:
        raise ValueError('Unsupported native source')
    raw = content.decode('utf-8-sig')
    kind = NATIVE_FILES[name]
    rows = [(reader.line_num, row) for reader in [csv.reader(io.StringIO(raw,newline=''))] for row in reader if any(v.strip() for v in row)]
    header_index = 1 if kind=='acme' else 0
    header = rows[header_index][1]
    expected = 36 if kind=='acme' else 129
    if len(header)!=expected or len(set(header))!=expected or header[0] != ('Time' if kind=='acme' else 'FCU TimeStamp'):
        raise ValueError('Unexpected native source schema')
    if kind=='acme' and 'Test Point: '+name.split('_')[0] not in ','.join(rows[0][1]):
        raise ValueError('Test point identity mismatch')
    data = rows[header_index+1:]
    if not data or len(data)>100000:
        raise ValueError('Native observation row limit')
    clock = '%H:%M:%S:%f' if kind=='acme' else '%Y-%m-%d %H:%M:%S.%f'
    times = [datetime.strptime(row[0].strip(),clock) for _,row in data]
    origin = min(times)
    frequencies = Counter(row[0].strip() for _,row in data)
    channels=[]
    for index,column in enumerate(header[1:]):
        unit = 'unresolved'
        source_unit = 'not declared'
        scale,offset=1,0
        if kind=='chamber':
            if column.endswith('(PSIA)'):
                unit,source_unit,scale='Pa','PSIA',6894.757293168
            elif column.endswith('(Deg C)'):
                unit,source_unit,offset='K','degC',273.15
            else:
                raise ValueError('Unsupported chamber source unit')
        channels.append({'channel':column,'sensor_id':name.split('.')[0],'index':index,'source_file':name,'source_column':column,
            'unit':unit,'source_unit':source_unit,'scale':scale,'offset':offset,'rows':len(data),
            'missing':0,'min':None,'max':None,'mean':0,'provenance':'experimental_raw','calibration_status':'unverified'})
    observations=[]
    previous=None
    warnings=Counter()
    for seq,((line,row),timestamp) in enumerate(zip(data,times)):
        if len(row)!=expected:
            raise ValueError(f'Malformed native row: {line}')
        elapsed=timestamp-origin
        t_ms=int((Decimal(elapsed.days*86400000000+elapsed.seconds*1000000+elapsed.microseconds)/1000).to_integral_value(rounding=ROUND_HALF_UP))
        if not 0<=t_ms<=2147483647:
            raise ValueError('Native time outside supported range')
        flags=[]
        if frequencies[row[0].strip()]>1:
            flags.append('duplicate_source_timestamp')
        if previous is not None and timestamp<previous:
            flags.append('source_time_reversal')
        previous=timestamp
        warnings.update(flags)
        values=[]
        for value,channel in zip(row[1:],channels):
            parsed=float(value) if value.strip() else None
            if parsed is not None:
                parsed=parsed*channel['scale']+channel['offset']
                if not math.isfinite(parsed):
                    raise ValueError(f'Nonfinite native value: {line}')
                channel['min']=parsed if channel['min'] is None else min(channel['min'],parsed)
                channel['max']=parsed if channel['max'] is None else max(channel['max'],parsed)
                channel['mean']+=parsed
            else:
                channel['missing']+=1
            values.append(parsed)
        observations.append({'seq':seq,'t_rel_ms':t_ms,'source_time':row[0].strip(),'values_json':values,
            'original_values':row[1:],'metadata_json':{'source_line':line,'flags':flags}})
    for c in channels:
        c['mean']=c['mean']/(c['rows']-c['missing']) if c['rows']>c['missing'] else None
        c['first_t_ms']=min(o['t_rel_ms'] for o in observations)
        c['last_t_ms']=max(o['t_rel_ms'] for o in observations)
    report={'parser_version':PARSER_VERSION,'sha256':hashlib.sha256(content).hexdigest(),'storage':'native-wide',
        'accepted_rows':len(observations)*len(channels),'observation_rows':len(observations),'missing_rows':sum(c['missing'] for c in channels),
        'quarantined_rows':0,'quarantine':[],'duplicate_rows':0,'time_warnings':dict(warnings),
        'duplicate_timestamp_rows':sum(v-1 for v in frequencies.values()),'channels':channels,
        'verification_eligible':False,'mode':'Replay Only','calibration_status':'unverified',
        'time_reference':{'source_origin':str(origin.time() if kind=='acme' else origin),'source_origin_sec':None,
            'meaning':'Earliest supplied observation, not ignition or extinction time.',
            'rule':'Original source clock retained; relative milliseconds rounded half up. Timezone not inferred.'},
        'limitations':['User-supplied source attribution has not been independently verified against the repository.',
            'No scientific calibration, instrument uncertainty or combustion classification is inferred.',
            'Repeated timestamps and clock reversals are retained and flagged; they are not automatically classified as sensor faults.',
            'ACME channel units are unresolved and values remain in source scale.' if kind=='acme' else 'PSIA and degree-C source units are converted to Pa and K; this does not establish sensor calibration.']}
    return raw,observations,report


def import_library(root=None):
    root=Path(root or library_root())
    package=json.loads((root/'manifest.json').read_text(encoding='utf8'))
    validated=[]
    for asset in package['assets']:
        path=asset_path(asset,root)
        with path.open('rb') as handle:
            digest=hashlib.file_digest(handle,'sha256').hexdigest()
        if digest!=asset['id'] or path.stat().st_size!=asset['bytes']:
            raise ValueError('Research asset checksum mismatch: '+asset['name'])
        validated.append(asset)
    imported=[]
    for asset in validated:
        with Session.begin() as db:
            db.execute(text('SELECT pg_advisory_xact_lock(8426103)'))
            if not db.get(ResearchAsset,asset['id']):
                db.add(ResearchAsset(id=asset['id'],payload=asset))
        if asset['name'] not in NATIVE_FILES:
            continue
        content=asset_path(asset,root).read_bytes()
        identity=hashlib.sha256((asset['id']+PARSER_VERSION).encode()).hexdigest()
        dataset_id='data_'+identity[:59]
        with Session.begin() as db:
            db.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':int(identity[:15],16)})
            existing=db.get(Dataset,dataset_id)
            if existing:
                imported.append({'id':dataset_id,'name':asset['name'],'reused':True,'observation_rows':existing.report['observation_rows'],'measurement_rows':existing.report['accepted_rows']})
                continue
            raw,observations,report=parse_native(content,asset['name'])
            manifest={'title':asset['name'].split('_data')[0].split('_Chamber')[0]+' — supplied experimental observations',
                'origin':'experimental','source_url':asset['source_url'],'license':'User-supplied files; repository attribution and usage terms require review.',
                'review_status':'user_supplied_unreviewed','processing_level':'Native source observations; calibration unverified',
                'source_asset_id':asset['id'],'storage':'native-wide','source_file':asset['name'],'study_id':asset.get('study_id'),
                'files':[{'name':asset['name'],'sha256':asset['id'],'bytes':asset['bytes'],'asset_id':asset['id']}],
                'provenance':'experimental_raw','calibration_status':'unverified'}
            db.add(Dataset(id=dataset_id,manifest=manifest,raw_csv=raw,report=report))
            db.flush()
            for start in range(0,len(observations),1000):
                db.execute(insert(SourceObservation),[{'dataset_id':dataset_id,**o} for o in observations[start:start+1000]])
            imported.append({'id':dataset_id,'name':asset['name'],'reused':False,'observation_rows':len(observations),'measurement_rows':report['accepted_rows']})
    return {'assets':len(validated),'datasets':imported}


if __name__=='__main__':
    print(json.dumps(import_library(),ensure_ascii=False))
