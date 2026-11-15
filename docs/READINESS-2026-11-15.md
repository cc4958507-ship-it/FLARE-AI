# FLARE AI readiness review — November 15, 2026

**Superseded agent/security checkpoint:** [Agent readiness](AGENT-READINESS-2026-11-15.md) documents the new three-role tool loop, durable jobs, 50-credit daily accounting, ECharts 6.1.0 and current checks. Statements below about absent agents, budgets, and the remaining ECharts advisory describe the earlier checkpoint.

## Implemented in this change

- Arabic/English selector with a saved preference, document language and direction, translated screens, status messages, accessibility labels and research summaries. Switching preserves in-progress form state. Original source filenames, channel identifiers, units and numeric data retain their technical values and left-to-right presentation.
- Arabic lexical search aliases for the small research index. This is not semantic retrieval.
- Arabic/English printable report headings and notices. Source citations, original scientific content and user-authored text remain intact. Machine-readable JSON stays unchanged.
- The selected language is passed to the Kie evidence-explanation request. Provider claims must cite allowed evidence, preserve its classification and contain at most three claims. Invalid responses still fall back to source summaries.
- Compatible security updates: React Router DOM 7.18.5 and Vite 6.4.6. The dependency audit went from four high and two moderate findings to one moderate finding in ECharts 5.6.0. The suggested ECharts fix is a major version upgrade and has not been included in this change.

## What the application actually does

1. **Evidence explanations:** `flare.ai.explain` is a single provider adapter. It receives a bounded evidence pack and validates the response. It cannot change the combustion decision, approve a plan, execute an intervention or control physical equipment.
2. **Scenario and plan workflow:** API endpoints create a versioned plan from selected evidence and require explicit approval. This is a deterministic workflow; it is not an independently reasoning planning agent.
3. **Simulation execution:** `flare.worker` advances the virtual clock with database locks and atomic batches. It is a background simulation worker, not an LLM agent.
4. **Experimental data:** NASA PSI-69 FLEX-007 observations are persisted separately and can be inspected/downloaded. They do not drive the synthetic verification profile.

Live configuration update: the supplied Kie key is now configured in the ignored server-side `.env`, with `AI_MODE=live`. One Arabic explanation through the application API completed successfully using returned model `gpt-6.1-sol` in 7.0 seconds. The response preserved the FLEX evidence reference and classification, and its text stayed within the supplied source summary. A scan confirmed the key is absent from the compiled browser assets. The API, database and worker remain running. This is one narrow live acceptance case, not a general capability certification.

The provider reported 144 output tokens, zero input tokens and 0.09 credits consumed. These are provider-reported fields only; accounting has not been reconciled against the billing ledger. No automatic paid retries were performed. The live English case and a broader reviewed evaluation set remain untested.

There is no multi-agent orchestrator, durable AI job queue, automatic tool-using research loop or autonomous scientific reviewer in this build. Do not present the prototype as having those capabilities.

## Remaining work, in priority order

1. Extend the passing Arabic live acceptance case to English and a documented evaluation set covering source-grounding, unknowns and refusal behavior. A successful API response alone does not establish intelligence or scientific validity.
2. Add persistent AI jobs, explicit request budgets, provider usage accounting, leases, bounded retries and recovery/idempotency before enabling autonomous or repeated paid work.
3. Implement and evaluate specific research-agent tasks, with explicit tools, authority limits and human review, if independent agents are required. Keep synthetic state calculation outside language-model authority.
4. Validate calibration/uncertainty metadata and fit/evaluate a physical model against independent NASA experiments. The current single-run image tables do not provide a calibrated chemistry model or real gas verification.
5. Add local embeddings/semantic retrieval and compare it against the current lexical baseline on reviewed questions.
6. Add authentication, resource ownership, authorization and production operations/backups before shared hosting. The current service remains bound to localhost.
7. Complete the normalized schema for scientific entities and AI jobs/calls; existing scenarios/plans/simulation runs still rely on snapshots.
8. Upgrade ECharts with chart regression checks to address the remaining moderate dependency advisory. Extend source-format adapters beyond the current FLEX-007 tables and add real-instrument fault diagnostics.

## Verification

Backend: 38 tests passed in the separate `flare_test` database, including Arabic search/reports, provider language handling, evidence references/classification, fallback behavior, persistent workflow, NASA original-file roundtrips and advanced simulated faults.

Build: TypeScript and Vite production build passed on Windows. Browser tests ran in headless installed Chrome with a separate `flare_e2e_20261115` database and private API/worker, keeping test runs out of the working application database. The full 16-test result is preserved in `work/e2e-full-results.json`. A final four-test language/layout smoke check also passed against the working app at localhost:8100 after packaging; its result is in `work/e2e-results.json`. The temporary test API/worker were stopped after verification. The working app returned HTTP 200, health status `ok`, database `connected` and model mode `offline`.

All 16 browser tests passed: complete research journey and controls, three independent simulation outcomes via the background worker, filters/comparison/network recovery, keyboard/modal behavior, accessibility scans in Arabic and English with both themes, language persistence and form-state preservation, English layouts at 320/390/768/1440px, Arabic layouts and imported NASA observations at 320/390/1440px. The signed source timestamp is isolated left-to-right within Arabic prose to retain its sign and unit order.

The automated tests validate software behavior. The additional one-case live check validates connectivity, Arabic output and evidence-contract handling. Experimental combustion thresholds, sensor calibration, broad model capability and provider billing remain unvalidated.
