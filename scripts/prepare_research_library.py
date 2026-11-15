"""Copy supplied archives into a deduplicated local library, without running content."""
import hashlib
import argparse
import json
from pathlib import Path
import re
import shutil
import zipfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-dir',required=True,type=Path)
parser.add_argument('--output-dir',type=Path)
args=parser.parse_args()
base=args.source_dir.resolve()
workspace=Path(__file__).resolve().parents[1]
root=(args.output_dir or workspace/'research_data').resolve()
(root/'objects').mkdir(parents=True,exist_ok=True)
first=base/'FLARE_Files_Part_01 (1).zip'
if not first.exists():
    first=base/'FLARE_Files_Part_01.zip'
sources=[first,*[base/f'FLARE_Files_Part_{n:02}.zip' for n in range(2,7)]]
assets={}
for source in sources:
    with zipfile.ZipFile(source) as archive:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            if Path(entry.filename).name!=entry.filename:
                raise ValueError('Unexpected non-flat supplied archive')
            with archive.open(entry) as handle:
                digest=hashlib.file_digest(handle,'sha256').hexdigest()
            name=entry.filename
            if digest in assets:
                assets[digest]['aliases'].append(name)
                continue
            target=root/'objects'/digest
            if not target.exists():
                with archive.open(entry) as handle,target.open('wb') as output:
                    shutil.copyfileobj(handle,output,1024*1024)
            with target.open('rb') as handle:
                if hashlib.file_digest(handle,'sha256').hexdigest()!=digest:
                    raise ValueError('Copied asset checksum mismatch')
            study=re.search(r'PSI-\d+',name)
            study_id=study.group() if study else ('PSI-20' if re.match(r'(19\d{3}|21\d{3})',name) else None)
            if name.endswith('_data.csv'):
                category='experimental_raw'
            elif 'Chamber_Readings' in name:
                category='experimental_raw'
            elif 'Analyzed Data' in name and name.endswith('.csv'):
                category='mixed_experiment_and_model'
            elif 'mfcSetpoints' in name:
                category='command_setpoints'
            elif 'metadata' in name:
                category='study_metadata'
            elif 'ScienceDirect' in name:
                category='paper_archive'
            elif name.startswith(('LCTF','SAFFIRE')) and name.endswith('.zip'):
                category='image_archive' if name!='LCTF089_2015.zip' else 'settings_archive'
            elif name.endswith(('.pdf','.docx')):
                category='reference_document'
            elif name.endswith('.ts'):
                category='video'
            elif name.endswith(('.jpg','.jpeg')):
                category='context_image'
            else:
                category='settings_and_timing'
            assets[digest]={'id':digest,'name':name,'aliases':[name],'bytes':entry.file_size,'sha256':digest,'object':'objects/'+digest,
                'category':category,'study_id':study_id,'source_archive':source.name,
                'source_url':'https://psi.nasa.gov/physci/repo/data/investigations/'+study_id if study_id else 'https://psi.nasa.gov/',
                'review_status':'user_supplied_unreviewed','calibration_status':'unverified',
                'provenance_note':'Supplied by the user. Study mapping requires review; no independent repository download was performed.'}
manifest={'version':1,'source_archives':[p.name for p in sources],'assets':list(assets.values())}
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'assets':len(assets),'aliases':sum(len(a['aliases']) for a in assets.values()),'bytes':sum(a['bytes'] for a in assets.values())}))
