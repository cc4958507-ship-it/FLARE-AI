"""Paged measurement access for legacy long form and native wide observations."""
import math
from sqlalchemy import select, func, case, or_
from .db import Measurement, SourceObservation


def channel_catalog(db, dataset):
    if dataset.report.get('storage')=='native-wide':
        return dataset.report['channels']
    rows=db.execute(select(Measurement.channel,Measurement.sensor_id,
        func.count().label('rows'),func.sum(case((Measurement.value.is_(None),1),else_=0)).label('missing'),
        func.min(Measurement.value).label('min'),func.max(Measurement.value).label('max'),func.avg(Measurement.value).label('mean'),
        func.max(Measurement.metadata_json['unit'].as_string()).label('unit'),
        func.min(Measurement.t_rel_ms).label('first_t_ms'),func.max(Measurement.t_rel_ms).label('last_t_ms'))
        .where(Measurement.dataset_id==dataset.id).group_by(Measurement.channel,Measurement.sensor_id)
        .order_by(Measurement.channel,Measurement.sensor_id)).mappings().all()
    return [dict(r) for r in rows]


def measurement_page(db,dataset,offset,limit,channel=None):
    channels=channel_catalog(db,dataset)
    if channel and channel not in {c['channel'] for c in channels}:
        raise ValueError('Measurement channel not found')
    if dataset.report.get('storage')=='native-wide':
        definition=next((c for c in channels if c['channel']==channel),channels[0])
        index=definition['index']
        observations=db.scalars(select(SourceObservation).where(SourceObservation.dataset_id==dataset.id)
            .order_by(SourceObservation.t_rel_ms,SourceObservation.seq).offset(offset).limit(limit)).all()
        items=[]
        for o in observations:
            flags=o.metadata_json.get('flags',[])
            items.append({'channel':definition['channel'],'sensor_id':definition['sensor_id'],'seq':o.seq,
                't_rel_ms':o.t_rel_ms,'value':o.values_json[index],'unit':definition['unit'],
                'original_value':o.original_values[index],'original_unit':definition['source_unit'],
                'source_timestamp':o.source_time,'source_file':definition['source_file'],
                'source_line':o.metadata_json['source_line'],'source_column':definition['source_column'],
                'quality':flags[0] if flags else ('missing' if o.values_json[index] is None else 'unit_unresolved' if definition['unit']=='unresolved' else 'calibration_unverified'),
                'flags':flags,'calibration_status':'unverified','provenance':'experimental_raw'})
        return items,{'offset':offset,'limit':limit,'total':definition['rows'],'channel':definition['channel']},channels
    conditions=[Measurement.dataset_id==dataset.id]
    if channel:
        conditions.append(Measurement.channel==channel)
    rows=db.scalars(select(Measurement).where(*conditions).order_by(Measurement.t_rel_ms,Measurement.channel,Measurement.sensor_id,Measurement.seq).offset(offset).limit(limit)).all()
    total=sum(c['rows'] for c in channels if not channel or c['channel']==channel)
    return [{'channel':m.channel,'sensor_id':m.sensor_id,'seq':m.seq,'t_rel_ms':m.t_rel_ms,'value':m.value,**m.metadata_json} for m in rows],{'offset':offset,'limit':limit,'total':total,'channel':channel},channels


def chart_series(db,dataset,channel,max_points):
    channels=channel_catalog(db,dataset)
    selected=[c for c in channels if c['channel']==channel]
    if not selected:
        raise ValueError('Measurement channel not found')
    total=sum(c['rows'] for c in selected)
    stride=max(1,math.ceil(total/max_points))
    if dataset.report.get('storage')=='native-wide':
        index=selected[0]['index']
        rows=db.execute(select(SourceObservation.seq,SourceObservation.t_rel_ms,SourceObservation.values_json[index].as_float().label('value'))
            .where(SourceObservation.dataset_id==dataset.id,or_(SourceObservation.seq % stride==0,SourceObservation.seq==total-1))
            .order_by(SourceObservation.t_rel_ms,SourceObservation.seq)).mappings().all()
    else:
        # Rank within the selected channel; sensor-local seq can restart across sensors.
        ranked=select(Measurement.seq,Measurement.t_rel_ms,Measurement.value,
            func.row_number().over(order_by=(Measurement.t_rel_ms,Measurement.sensor_id,Measurement.seq)).label('position'))
        ranked=ranked.where(Measurement.dataset_id==dataset.id,Measurement.channel==channel).subquery()
        rows=db.execute(select(ranked.c.seq,ranked.c.t_rel_ms,ranked.c.value).where(or_((ranked.c.position-1)%stride==0,ranked.c.position==total)).order_by(ranked.c.position)).mappings().all()
    return {'channel':channel,'unit':selected[0]['unit'],'total':total,'sampled':stride>1,
            'sampling':'Every Nth observation plus the last; use the paginated table for exact records.',
            'items':[dict(r) for r in rows]}
