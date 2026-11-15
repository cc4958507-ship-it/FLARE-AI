"""Source-linked summaries transcribed from the supplied implementation document.
NASA FLEX-007 image-analysis tables are available separately in measurement imports.
"""
RECORDS = [
    dict(id='flex', title='Flame Extinguishment Experiment', short='FLEX', family='Liquid droplets', type='NASA metadata', classification='Experimental evidence', gravity='Microgravity', fuel='Liquid fuel droplets', geometry='Isolated droplet', channels=['Flame imaging'], raw_available=False,
         summary='A starting point for investigating droplet combustion in microgravity and the limits of visible flame as an observation.',
         finding='NASA describes low-temperature burning after visible flame extinction in some FLEX droplet experiments. This does not establish a universal extinction criterion.',
         unknowns=['Run-specific fuel and composition', 'Calibrated gas channels', 'Raw measurement timing'],
         source='NASA Physical Sciences Informatics', url='https://psi.nasa.gov/physci/repo/data/investigations/PSI-69', reference='R2 · PSI-69',
         note='PSI-69 FLEX-007 / 20CAL13 image-analysis tables are bundled in Measurement imports (CC0-1.0; DOI 10.60555/mbq8-0451). Camera images and independent calibration are not included. These observations do not drive synthetic verification.'),
    dict(id='cool-flames', title="You’re Hot, Then You’re Cold", short='Cool flames', family='Liquid droplets', type='Curated literature', classification='Experimental evidence', gravity='Microgravity', fuel='Liquid fuel droplets', geometry='Droplet experiment', channels=['Visible flame observation'], raw_available=False,
         summary='The scientific question behind the lab: what remains after a flame can no longer be seen?', finding='NASA reports cool-flame behavior in particular droplet experiments. Residual heat alone is not evidence of ongoing combustion.', unknowns=['Synchronized channel data', 'Run-specific thresholds'], source='NASA',url='https://www.nasa.gov/humans-in-space/youre-hot-then-youre-cold/',reference='R3 · NASA article',note='Qualitative background; not a calibrated verification profile.'),
    dict(id='suppression', title='Spacecraft Fire Suppression Testing and Evaluation', short='Suppression testing', family='Suppression research', type='Curated literature', classification='Scientific inference', gravity='Unknown', fuel='Unknown', geometry='See source', channels=[],raw_available=False,
         summary='Research context for comparing suppression approaches while retaining differences in test conditions.', finding='Use this reference for context on suppression testing, not for real equipment instructions or synthetic intervention parameters.',unknowns=['Comparable run geometry', 'Channel mapping', 'Validated applicability'],source='NASA Technical Reports Server',url='https://ntrs.nasa.gov/citations/20040161216',reference='R4 · NTRS 20040161216',note='Bibliographic record supplied by project specification; no experimental series imported.'),
    dict(id='cpm', title='The Combustion Product Monitor',short='Product monitor',family='Gas monitoring',type='Curated literature',classification='Scientific inference',gravity='Unknown',fuel='Not applicable',geometry='Monitoring system',channels=['Multiple gas channels (see source)'],raw_available=False,
         summary='Context for monitoring more than one combustion-related gas instead of relying on a single signal.',finding='Multi-channel monitoring informs the project’s observation strategy. FLARE does not claim to reproduce or validate the monitor.',unknowns=['Calibrated sensor response', 'Raw measurements', 'Available full text'],source='NASA Technical Reports Server',url='https://ntrs.nasa.gov/citations/20210012108',reference='R5 · NTRS 20210012108',note='Record/abstract reference; no raw data or instrument calibration available in this prototype.'),
    dict(id='cleanup',title='Post-Fire Atmospheric Cleanup and Monitoring',short='Post-fire monitoring',family='Atmosphere research',type='Curated literature',classification='Scientific inference',gravity='Unknown',fuel='Not applicable',geometry='See source',channels=[],raw_available=False,
         summary='A separate research question: how should post-fire atmospheric cleanup and monitoring be evaluated?',finding='Atmospheric contamination and combustion status must remain independent. A synthetic verification result is not breathing clearance.',unknowns=['Health exposure limits', 'Validated channel thresholds', 'Raw monitoring series'],source='NASA Technical Reports Server',url='https://ntrs.nasa.gov/citations/20090022745',reference='R6 · NTRS 20090022745',note='Literature context only; no health or operational safety threshold is implemented.'),
    dict(id='synthetic-v1',title='Single-Droplet Observation Model',short='Synthetic demo',family='Liquid droplets',type='Synthetic',classification='Model result',gravity='Simulated microgravity context',fuel='Abstract source (not a chemical fuel)',geometry='Single educational droplet',channels=['flame_presence','thermal_excess','co_proxy','ventilation_proxy','co2_proxy'],raw_available=True,
         summary='A seeded educational generator for testing the complete intervention, observation and verification loop.',finding='Stopping the model source changes future measurements. Reducing it can remove the visible flame while other observations retain a danger state.',unknowns=['Physical calibration', 'Real-world predictive validity'],source='FLARE implementation specification · sections 15–18',url=None,reference='synthetic-v1 · version 1',note='All values use sim_unit. Parameters test software behavior and are not derived from NASA data.')
]


def ranked(q='', family=None):
    aliases = {'قطرة':'droplet', 'قطرات':'droplet', 'القطرات':'droplet', 'لهب':'flame', 'اللهب':'flame',
               'احتراق':'combustion', 'الاحتراق':'combustion', 'إخماد':'suppression', 'الإخماد':'suppression',
               'انطفاء':'extinction', 'الانطفاء':'extinction', 'غاز':'gas', 'غازات':'gas', 'الغازات':'gas',
               'رصد':'monitor', 'مراقبة':'monitor', 'بارد':'cool', 'البارد':'cool', 'حرارة':'thermal',
               'اصطناعي':'synthetic', 'محاكاة':'synthetic', 'سلامة':'safety'}
    terms = [aliases.get(term, term) for term in q.lower().split()]
    result = []
    for row in RECORDS:
        if family and row['family'] != family:
            continue
        text = ' '.join(str(v) for v in row.values()).lower()
        matches = [t for t in terms if t in text]
        if terms and not matches:
            continue
        result.append({**row, 'score': len(matches), 'ranking_reason': f"Matched: {', '.join(matches)}" if matches else 'Curated research index; no similarity score implied.'})
    return sorted(result, key=lambda x: -x['score'])
