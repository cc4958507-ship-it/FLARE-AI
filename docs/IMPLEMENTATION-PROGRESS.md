# Extension progress — 2026-11-14

Current extension: [Agent readiness, November 15](AGENT-READINESS-2026-11-15.md): three bounded tool-using roles, persistent queue/recovery, shared Kie accounting (50 reported credits/day), ECharts 6.1.0, 54 passing backend tests and 18 passing browser tests.

Latest checkpoint: [November 15 readiness review](READINESS-2026-11-15.md) covers Arabic/English switching, actual AI capabilities, dependency updates, 38 passing backend tests and 16 passing browser tests. Earlier unexecuted-browser-test notes below describe historical checkpoints.

Update: [NASA FLEX-007 measurement import](NASA-FLEX-007.md) is now implemented. Five original NASA text files plus an investigation metadata snapshot are bundled with checksums; 1,112 observations across seven channels are parsed with source locations, units, missing values and time-origin mapping. The following initial-extension notes describe the earlier checkpoint; the linked NASA document supersedes its statement that no NASA measurements have been downloaded/imported. Scientific calibration and model fitting are still pending.

Implemented:

- Measurement imports page and `/api/v1/datasets` API, with bounded long-form CSV input.
- Original UTF-8 CSV preservation, SHA-256 and parser version, source URL, declared license, origin and unreviewed attribution.
- Normalized relational measurement rows in a separate table; missing values stay null. Supported explicit unit conversions, row quarantine and whole-import rejection on nonfinite values or conflicting duplicates.
- Transactional, concurrent-safe repeated import reuse. Download original and inspect validation report / paginated normalized values.
- Synthetic drop, freeze (failed heartbeat), replay, out-of-tolerance skew and saturation injection. Flags invalidate observations without changing latent source dynamics. Worker replay, branches, event ledger and reports retain faults.

Limits:

- This is a CSV interchange contract, not a parser for arbitrary NASA archives, video, MATLAB or instrument formats. It does not certify calibration, detect unknown real sensor faults, or infer units. Frozen stable readings alone are not treated as failure.
- Advanced fault injections explicitly declare known simulation faults. Skew quarantines the channel; timestamp/sequence-level real instrument diagnostics remain future work.
- `NASA raw` is an importer declaration, not verified NASA attribution. The importer marks all sources unreviewed. Imported observations cannot enter the synthetic verification profile.
- Experimental rows are normalized relational data; existing scenarios/plans/runs still use snapshots. This is not the full proposed schema migration.

NASA source investigation:

- User search: https://psi.nasa.gov/physci/repo/search?q=combustion&data_source=psi&data_type=investigation
- Public search service discovered from the repository application: `https://psi.nasa.gov/geode-py/ws/repo/search?term=combustion&source=psi&type=investigation`
- Search results include PSI-69 (FLEX) and PSI-68 (FLEX-2). No raw NASA measurements have been downloaded, transformed or imported in this change. A single guessed investigation detail endpoint returned 404; file navigation must use the repository's actual data listing contract.

Remaining requested work:

1. Retrieve a documented raw run and calibration files; preserve original archive, citation and units; implement its format-specific adapter and independent review.
2. Calibrated physics/chemistry and evaluation against held-out experiments.
3. Local embeddings and measured semantic retrieval improvement.
4. Durable Kie jobs, leases, bounded retry/recovery and transactional budget accounting.
5. User authentication and resource ownership/authorization; production host setup.
6. Remaining normalized scientific schema and migration of existing records.

Deployment remains local on loopback. No production hosting, paid model calls, or external accounts were created.

Validation: 32 backend tests passed in a separate PostgreSQL test database, including ingestion roundtrip/idempotency and advanced-fault branch persistence. TypeScript and production Vite build passed. Import screen and five fault controls were inspected in the running browser. OpenAPI and generated TypeScript declarations were refreshed. Full Playwright and accessibility suites were updated for the new route/control but were not executed on this Windows host (the existing browser configuration points to Linux Chromium). Existing npm dependency audit warnings remain unresolved.
