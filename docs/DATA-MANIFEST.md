# Data and provenance manifest

Corpus `curated-spec-v1` contains six records. Source metadata and summaries were transcribed from the uploaded FLARE implementation document. This build has not downloaded or validated PSI measurement archives. The reference literature is research context; it is not calibration for synthetic-v1.

| ID | Provenance | Reference | Data available |
| --- | --- | --- | --- |
| flex | NASA metadata | R2: PSI-69 | Metadata summary only |
| cool-flames | Curated literature | R3: NASA article | Qualitative summary |
| suppression | Curated literature | R4: NTRS 20040161216 | Bibliographic context |
| cpm | Curated literature | R5: NTRS 20210012108 | Bibliographic context |
| cleanup | Curated literature | R6: NTRS 20090022745 | Bibliographic context |
| synthetic-v1 | Synthetic | Specification sections 15–18 | Seeded generated observations |

Field provenance for each metadata record is its adjacent named source and reference. Missing run-specific fuel, calibration, times, geometry or channels remain Unknown or explicitly stated gaps. Classifications (experimental evidence, scientific inference, model result) are distinct from provenance.

Generator 0.1.0 uses a fixed 1s step, initial source=1, thermal=.7, CO=.3, CO2=.6, and uniform seeded noise in ±.0002. Thermal update: +.09*source-.12*thermal. CO update: +.06*source-.04*CO. CO2 update: +.04*source-.012*CO2. Observations clip to [0,1] sim_unit. Flame is visible only while source>.5. These are authored educational parameters, not NASA measurements.

Required channels: flame_presence, thermal_excess, co_proxy, ventilation_proxy. CO2 is optional and does not determine combustion. `drop` removes CO observations only. No ppm, K, hardware commands or health limits are used.

All corpus content is embedded in backend/flare/corpus.py; reports export source references and the persisted evidence snapshot. No NASA logo or affiliation claim is used.
