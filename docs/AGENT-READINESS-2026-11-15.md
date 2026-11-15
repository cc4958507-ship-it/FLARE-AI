# FLARE AI agents — November 15, 2026

Current local limits were subsequently raised by the user to **100 reported credits and 100 model requests per day**; see [current budget configuration](KIE-BUDGET-2026-11-15.md). Earlier 50/20 values below are historical.

Later data extension: [research data integration](RESEARCH-DATA-INTEGRATION.md) adds the supplied-source library, three native datasets, full channel statistics and a checked `dataset_counts` contract for native-data reviewer outputs.

UI update: the daily Kie budget panel is hidden at the user's request. Server-side limits, admission checks and accounting remain active. Task availability/errors remain visible without displaying daily accounting figures.

The user also requested removal of the provider-sharing consent checkbox and its text from the task form. Task submission no longer requires that checkbox; provider processing and budget enforcement are unchanged.

This checkpoint supersedes earlier agent, budget, test-count and ECharts statements in the readiness review. The application remains a local research workbench with a synthetic simulation, not a calibrated combustion or atmosphere safety system.

## Delivered

- Three bounded, tool-using agent roles: evidence researcher, measurement reviewer and simulation reviewer. The model chooses a tool action, receives the saved result, and writes a source-referenced research note. A dedicated `agent-worker` runs independently of the simulation clock.
- Durable queue, per-step checkpoints, event history, scoped read-only tools, request idempotency, leases and recovery. A completed provider response is reused after interruption before checkpoint commit. Ambiguous paid outcomes stop for review rather than being submitted twice.
- Shared Kie admission/accounting for agents AND existing evidence explanations: **50 reported credits/day**, **20 requests/day**, **10 estimated credits reserved/request**, **1,200 output tokens/request**, default **4 requests/task** (2–6 permitted). Daily boundaries use Asia/Amman.
- Arabic/English `/agents`: assignment, explicit provider-data sharing notice, role/attachment selection, budgets, saved results, source links, steps, events, cancellation and per-request reported cost.
- Migration 004 adds `agent_jobs`, `agent_events`, and `llm_calls`. Existing simulation/scenario/plan payloads still use snapshots.
- ECharts **6.1.0**. Clean npm installation reported **zero vulnerabilities**. This dependency audit is not a full security audit.

## Tools and authority

| Role | Tools |
| --- | --- |
| `research` | `search_evidence`, `read_evidence`, inspection of explicitly attached dataset/run |
| `dataset_review` | `inspect_dataset`, `read_evidence` |
| `run_review` | `inspect_run`, `read_evidence` |

The assignment UI scopes evidence to FLEX and Cool Flames. The API permits selecting up to three of the six curated records. Search is lexical; no embeddings or automatic NASA browsing are implemented. Tools cannot execute shell commands, access arbitrary URLs, modify experiments, approve plans, change simulation decisions or certify safety. Generated text requires review: structural checks and allowed citations do not prove every statement true.

The measurement tool reports channel/sensor counts, null counts, units, time ranges, summary values and source limitations. The run tool reads up to five saved synthetic frames and provenance. Dataset/run review must use its corresponding inspection tool before finishing. Final findings can reference only source IDs returned by tools. Unknown tools, out-of-scope sources, duplicate tool actions and malformed responses stop the job.

## Recovery and costs

The queue permits at most 20 pending jobs. Workers claim jobs using row locks and 120-second leases. Provider HTTP 429 and connection failures are retried with 5/10-second delays, at most twice; dispatched attempts consume task/daily request allowances. Read timeouts, interrupted in-flight calls and missing cost fields stop paid admission until usage is reconciled. Invalid model output stops the task and preserves its response/checkpoints. Cancellation prevents future steps; an already sent request can still finish and consume credits.

`flare.reconcile` is an operator-only CLI, not an unauthenticated HTTP endpoint. After checking a call against Kie's billing ledger, run:

```powershell
docker compose exec -T api python -m flare.reconcile --call call_ID --credits 0.17 --billing-reference ledger-reference
```

Use actual confirmed amounts and references. Reconciliation is recorded, clears the unresolved-usage admission lock, and leaves the task stopped for review. It never automatically repeats an uncertain request. A known completed response can be reprocessed from its saved checkpoint by an operator after correcting a parser; its cache avoids another paid request.

**Budget limitation:** reported costs and estimated reservations are application admission controls. Kie can charge more than a reservation or report incomplete accounting. This is not a provider-enforced billing guarantee. Unknown usage freezes further paid admission across day boundaries. Requests before migration 004 are outside this ledger. The key remains server-side in ignored `.env` and is never returned by capability/job endpoints.

## Verification

- **54 backend tests passed** in guarded `flare_test`, with provider access disabled by default: concurrent admission, request/credit limits, idempotency, retry, ambiguous timeout, lease recovery, cached-response reuse, cancellation during a call, unknown-cost lockout, reconciliation, scoped tools and source references, plus existing scientific-data/simulation tests.
- **18 browser tests passed** in installed Chrome against separate offline API, simulation worker and agent worker on `flare_e2e_20261115`: existing workflow, ECharts, NASA measurements, agent submission/persistence/offline failure, AR/EN behavior, responsive layouts and axe checks in both languages/themes including `/agents`. Result: `work/e2e-agents-full-results.json`.
- Production TypeScript/Vite build passed on Windows and Docker. The chart chunk exceeds 500 kB; this is a performance advisory.
- All **three live cases succeeded**: Arabic measurement review (`inspect_dataset`), English evidence research (`read_evidence`), and English simulation review (`inspect_run`). Six total provider requests, **1.04 reported Kie credits**, zero unresolved calls. Details: `AGENT-LIVE-ACCEPTANCE-2026-11-15.json`. The Arabic case reported 1,112 rows, seven channels and 282 missing values, consistent with the saved tool result. The simulation case retained synthetic provenance and missing-CO uncertainty.
- The Arabic case initially stopped because commentary and final messages were concatenated. The corrected parser selects the explicit `final_answer` phase and rejects commentary-only output. Reprocessing its saved response completed the task without another paid request. This operator intervention is retained in the event log.
- Six targeted browser/accessibility checks passed again after the final UI changes. The working application's saved Arabic result, source links and mobile layout were checked in Chrome; no page errors or key in browser assets were found. Screenshot: `work/agents-live-ar-note.png`.

Software checks and narrow live cases do not certify general intelligence, scientific calibration or billing accuracy.

## Still required

1. **Calibration:** calibration/uncertainty files, instrument/channel/time metadata, independent training and held-out experiments, intended physical/chemical model and scientific review. The FLEX image tables do not establish calibrated chemistry or safe atmosphere thresholds.
2. **Semantic retrieval:** install a real multilingual embedding model, index a broader reviewed corpus, and evaluate representative Arabic/English questions against lexical retrieval.
3. **Experimental expansion:** further NASA runs/formats and source-specific adapters with original artifacts and independent validation. Real sensor timing/replay/saturation diagnostics require instrument-specific datasets.
4. **Production:** hosting/provider and domain, intended users/roles and sharing model, authentication/ownership/authorization, TLS/secrets, backups/restore checks and monitoring. The unauthenticated prototype remains bound to localhost.
5. **Full scientific schema:** normalize remaining scientific entities and versioned simulation payloads. Queue/accounting tables do not complete the entire proposed database design.
6. **Agent evaluation:** reviewed questions, grounding/refusal scores, malicious-source robustness and reconciliation against provider billing. Valid source IDs do not guarantee accurate prose.

No continuous autonomous schedule is enabled. Work occurs only for submitted tasks.
