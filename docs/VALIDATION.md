# FLARE AI validation record

Validated 2026-11-14 (Asia/Amman); local synthetic prototype version 0.2.0.

## Executed checks

- Python: 20 passing tests. Engine timing and scope; identical-seed replay; source reduction versus source stop; data-loss latching; verification revocation with historical timestamp retained; command validation; PostgreSQL persistence; command idempotency; worker pause; independent branches; immutable parent observations; ordered event cursor; JSON/HTML exports; provider-output rejection and offline fallback.
- Property checks: 20 generated seed/intervention-time combinations inside the engine property test.
- TypeScript production build: passed with bundled local font assets and separate chart/vendor chunks.
- Playwright: 10 passing tests, including the entire research journey, every preset observed through the worker, filtering/empty/error/retry states, source review, comparison limit, plan approval, pause/speed, interventions, CO dropout, branch, reload and JSON download.
- axe-core: no violations for the tested WCAG A/AA tags on library, scenario, lab and archive in both light and dark themes.
- Responsive checks: no document overflow at 320, 390, 768 or 1440px. Library captured in both themes; lab captured at every width.
- Independent source accessibility review: three defects identified, fixed and rechecked: unique dialog IDs, accessible full-series chart data, and focus continuity.
- Docker application image built successfully with certificate verification enabled. Compose configuration validates.

## Limits of verification

No manual screen-reader session or calibrated physical validation was performed. axe checks and source review are not a WCAG certification. Tests use synthetic observations and local PostgreSQL. Live Kie model listing and a source-linked application explanation were verified. Adapter rejection tests still use mocked HTTP responses; native provider JSON-schema enforcement and billing reconciliation remain unverified. Original PSI data were not imported. Source summaries remain attributed to the supplied specification. No public cloud deployment or remote authentication is included.

## antislop delivery gate

### Hard gate

- R-02 PASS: product copy uses no em dashes; source punctuation is retained only inside quoted titles when present.
- R-03 PASS: browser overflow assertions pass at 320/390/768/1440px.
- R-17 PASS: displayed counts come from records/runs; measurements are marked Synthetic demo.
- R-18 PASS: no testimonials, fictional customers or human-profile imagery.
- R-23 PASS: text wordmark and initial placeholder only; conceptual droplet is labeled as a schematic. Navigation follows the supplied product journey.
- R-24 PASS: all navigation destinations render implemented screens; sources carry actual reference URLs.
- R-25 PASS: axe color-contrast checks pass in both themes; secondary labels were darkened after the first failure.
- R-26 PASS: browser journey exercises filters, comparison, review, approval, run controls, branch, intervention, fault, inspection, reset and export.
- R-27 PASS: filtered empty state, no-run state, named loading states and network-error recovery exist; browser tests exercise empty/error/retry.
- R-28 PASS: no generic FAQ section exists.
- R-32 PASS: skip link, native keyboard controls, dialog Escape/focus return, focus styles and full-series table tested.
- R-33 PASS: behavior resides in React source and API modules; no runtime code-patching mechanism is shipped.
- R-34 PASS: both themes render and pass responsive/axe checks; chart colors observe theme changes.
- R-35 PASS: application built and ran against PostgreSQL with browser click-throughs and persisted reloads.
- R-36 PASS: no safety certification, compliance, customer or model-accuracy claims are made.
- R-37 PASS: design brief and ENERGY 2 / RHYTHM 2 / MOTION 1 declared in DESIGN-NOTES.md before UI implementation.
- R-38 PASS: six records are provenance-labeled; unknown fields and synthetic values are explicit.

### Purpose gate

- R-01 PASS: copper identifies the action path and conceptual droplet; no ornamental gradient.
- R-04 PASS: icon relevance and library weight are documented in DESIGN-NOTES.md; no sparkle/AI-orb motifs.
- R-06 PASS: local IBM Plex provides scientific labels; monospace is limited to times and identifiers.
- R-07 PASS: no background grid; chart grid lines encode values.
- R-08 PASS: arrows indicate navigation and source opening, not every control.
- R-09 PASS: badges report actual source classification, mode or run state.
- R-10 PASS: no glass/backdrop effects.
- R-12 PASS: only the floating comparison tray receives elevation for its overlay role.
- R-13 PASS: no decorative glow effects.
- R-14 PASS: evidence is presented as comparable research rows, not generic feature cards.
- R-19 PASS: only brief control feedback; virtual data progression has a working pause action and reduced-motion styling.
- R-22 PASS: droplet schematic has a direct observation-question role and is explicitly conceptual.

### Liveliness

- Dials PASS: ENERGY 2 / RHYTHM 2 / MOTION 1 documented and reflected by restrained workbench composition.
- Focal point PASS: research question leads Library; measured signals lead Lab; plan review leads approval.
- Rhythm PASS: source rows, structured forms, chart workspace and event ledger use content-specific layouts.
- Whitespace PASS: 4px scale with denser controls and larger question/section separation.
- Accent PASS: copper carries primary action and source navigation without decorating every surface.
- Signature PASS: observation motif appears in droplet boundary, measured time axis, hold ruler, intervention markers and timestamped ledger.
- Design read PASS: explicit research-workbench brief recorded before source UI generation.

### Craftsmanship and consistency

- C-1 / R-31 PASS: intent, palette, type, spacing, depth, controls and icon decisions are documented.
- C-2 PASS: controls perform real API/navigation/state actions; unavailable actions are disabled for a reason.
- C-3 / R-05 PASS: composition follows evidence → comparison → question → approved plan → observations → report.
- C-4 PASS: tested empty/loading/error, both themes, responsive widths and keyboard flows.
- C-5 PASS: no invented evidence or unlabelled physical measurements.
- R-11 PASS: small control radius, medium panel radius and larger native-dialog radius form a consistent scale.
- R-15 PASS: task-specific actions such as “Approve plan & open lab” and “Apply to next sample”.
- R-16 PASS: copy describes the actual workflow rather than generic AI marketing claims.
- R-20 PASS: research provenance, required-channel quality and continuous hold determine the interface's structure.
- R-21 PASS: functioning persisted light/dark toggle.
- R-29 PASS: neutral notebook/graphite palette with copper action accent and state semantics.
- R-30 PASS: no unrequested product clone or borrowed brand assets.

Additional operational checks: SSE reconnect with Last-Event-ID returned the next sequence (1 → 2); a PostgreSQL custom-format backup restored into a separate database with 5,066 frame rows at the time of the check. This checked local backup/restore only, not a cloud disaster-recovery procedure.

Fresh-image Compose smoke test: API and PostgreSQL reported healthy; worker started. First launch generated three examples with Danger, Verified and Uncertain outcomes in a new persistent volume. A new container-worker branch was started for an independent intervention check.

Kie activation: validated one live application explanation from gpt-6.1-sol against the FLEX evidence ID, persisted the evidence snapshot, and retained deterministic simulation authority. The API uses server-only configuration and a trusted runtime CA bundle with TLS verification enabled. See KIE-LIVE-VALIDATION.json for non-secret provider metadata.
