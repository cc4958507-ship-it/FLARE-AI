# Supplied research data integration

Implemented November 15, 2026. This supersedes the earlier review's statement that the supplied files have not been imported.

## Available in the running application

Open `/research-files` for the original-file library and imported datasets. All 82 supplied outer filenames are represented by **80 unique content-addressed files** (883,804,240 bytes), with identical aliases retained. No source archive was executed. Original objects are mounted read-only from `research_data`; SHA-256 and byte counts are verified during import.

| Native dataset | Source records | Channels per record | Channel values |
| --- | ---: | ---: | ---: |
| `19056A2_data.csv` | 31,316 | 35 | 1,096,060 |
| `19056D2_data.csv` | 30,841 | 35 | 1,079,435 |
| `C039H03_Chamber_Readings.txt` | 489 | 128 | 62,592 |
| Total | **62,646** | | **2,238,087** |

The pre-existing NASA FLEX-007 dataset remains separate and unchanged. Native observations use migration 005's `source_observations` table: one timestamped record stores channel vectors, original strings, source time, source line and timing flags. This avoids millions of copies of repeated per-cell metadata. `research_assets` persists the original-file catalog; the original large objects stay on disk.

The measurement API returns channel catalogs and exact paginated records. Native requests without a channel default to the first channel; choose `channel` explicitly for analysis. The viewer fetches 25 exact records per table page and a separate chart overview, rather than loading a dataset's millions of values into the browser. The chart uses every Nth record plus the last and explicitly labels sampling. Download the original source for complete analysis; the chart is not suitable for detecting every transient.

## Scientific boundaries

- ACME CSV channel units are not sufficiently declared in their headers. Values remain in their original scale, with `unit=unresolved` and unverified calibration. Negative values are preserved, not clamped or relabeled as physical quantities.
- Explicit chamber PSIA units convert to Pa using 6894.757293168; degrees Celsius convert to K with +273.15. These unit conversions do not establish calibration, uncertainty or sensor accuracy.
- Repeated source timestamps are preserved with sequence IDs and flags. The chamber source contains six extra rows when counting repeated timestamps. Clock reversals are flagged. Neither condition automatically proves freeze/replay faults. Source timezone and ignition origin are not invented.
- PSI-117 experiment/model tables are available as original source files in their own `mixed_experiment_and_model` category. They are **not** merged into measured channels. Native adapters for their separate experimental/model curves remain future work.
- MFC setpoint files are categorized as commands; settings and timing files remain distinct. Setpoints are not measured flow. Image/video archives and documents are available to inspect/download, but have not been converted into calibrated time series or embedded semantic indexes.
- Source attribution and licensing remain user-supplied/unreviewed for this batch. The library's study links are references, not proof of independently verified provenance. Unresolved study mappings are labeled.
- Imported data cannot enter the synthetic safety profile, approve plans, modify simulations or establish breathing clearance. Scientific model calibration is still pending.

## Agents

The library links directly to `/agents?dataset=ID`, preselecting the measurement reviewer and dataset without dispatching a paid request. The inspection tool uses complete stored channel statistics; it no longer truncates a dataset to the first 10,000 values. Optional `inspect_dataset` arguments can select a channel by exact name. Large overviews explicitly report omitted channel summaries, while selected-channel queries return that channel's full statistics.

Native dataset review notes must include `dataset_counts` with exact `source_records`, `channels` and `measurement_values` matching the tool result. A mismatch or omission stops acceptance. The first narrow live attempt exposed confusion between records and individual channel values; it was marked `needs_review`, with its response/accounting retained. This motivated the count contract. Prose still needs review: a valid count object does not prove every sentence scientifically correct.

The user's requested hidden daily budget panel and removed consent checkbox remain absent. Server-side budgeting and dispatch rules remain active.

## Rebuilding and backing up

Prepare a library from the supplied six parts:

```powershell
python scripts/prepare_research_library.py --source-dir C:\Users\LOQ\Downloads
docker compose up -d --build --wait
docker compose exec -T api python -m flare.research_data
```

The preparer accepts Part 01 with or without `(1)` and requires Parts 02–06. It creates a deduplicated object store and manifest without deleting source archives. The database importer checks every object before use; rerunning it reuses existing datasets instead of adding duplicates. Only three explicitly supported native filenames are converted to observations; other files remain categorized sources.

Back up **both** the PostgreSQL volume and the `research_data` directory. That directory is excluded from Git and the Docker build context to avoid bundling 843 MiB of supplied research into every image. Deployment requires mounting it alongside the database. The API's compose service already mounts it read-only at `/app/research`.

## Verification

- 63 backend tests passed in the dedicated `flare_test` database, including full actual imports, source checksums, exact final-record paging beyond 10,000 values, chart sampling bounds, duplicate timestamps, known unit conversions, unresolved-unit preservation, idempotency, scoped agent access and count mismatch rejection.
- Production TypeScript/Vite build passed. The existing chart-bundle size advisory remains.
- All **20 browser tests passed**, including native records in both languages, paging, attachment selection, existing simulation workflows and accessibility scans across seven routes in both themes/languages. Results: `work/e2e-research-data-results.json`. The final running application was also checked in Chrome after restart: 80 original assets, three native datasets, 62,646 source records, 2,238,087 channel values and no page errors.
- Two bounded live inspections each successfully read the full native statistics. The first generated note confused record and cell counts; it was held for review. The second passed the new structured count checks, but its prose claimed duplicate timestamps despite an observed duplicate count of zero, and was also held for human review. Both paid responses remain in the audit trail; neither note is presented as accepted scientific analysis. Total provider-reported cost of these two attempts: **1.57 Kie credits**. No further paid attempts were made. The tool/prompt now explicitly separates observed timing counts from generic retention policies. A broader grounding evaluation remains necessary.
- Software tests do not calibrate an instrument or a physics/chemistry model. Valid structured counts do not validate all generated prose.
