"""Idempotent, explicitly labeled examples generated through the real engine."""
from .db import Session, Record
from .corpus import RECORDS
from .service import create_run, advance, now


def main():
    with Session.begin() as db:
        if db.get(Record,'demo-scenario-v1'):
            return
        scenario=Record(id='demo-scenario-v1',kind='scenario',payload={'name':'Synthetic observation examples','question':'What do observations show after source reduction, source stop, or CO channel loss?','investigation_ids':['flex','cool-flames'],'version':1,'scope':'synthetic','created_at':now()})
        evidence=Record(id='demo-evidence-v1',kind='evidence',payload={'scenario_id':scenario.id,'snapshot':'curated-spec-v1','items':RECORDS[:2],'explanation':{'mode':'offline','message':'Source summaries from the supplied implementation document.','claims':[]},'created_at':now()})
        plan=Record(id='demo-plan-v1',kind='plan',payload={'scenario_id':scenario.id,'scenario_version':1,'version':1,'profile_ref':'synthetic-v1','approved':True,'approved_at':now(),'approval_origin':'Explicitly labeled seeded demonstration plan','evidence_ids':['flex','cool-flames'],'evidence_snapshot_id':evidence.id,'options':['SIM_REDUCE_SOURCE','SIM_STOP_SOURCE'],'required_channels':['flame_presence','thermal_excess','co_proxy','ventilation_proxy'],'verification_hold_s':30,'danger_clear_s':10,'scope':'Synthetic single-droplet only'})
        db.add_all([scenario,evidence,plan])
        db.flush()
        for preset,name in [('reduce','[Demo] Source reduction'),('stop','[Demo] Source stopped'),('data-loss','[Demo] Missing CO channel')]:
            run=create_run(db,plan,name=name,preset=preset)
            advance(db,run,140)
            run.payload={**run.payload,'status':'paused'}
    print('Created three labeled synthetic example runs.')

if __name__=='__main__':
    main()
