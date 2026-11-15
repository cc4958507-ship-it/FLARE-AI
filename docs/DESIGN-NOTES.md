# FLARE AI interface working brief

Derived from the provided implementation specification and Craftwork interface-design, antislop-ui, better-accessibility and design-a-chart skills. This records implementation choices, not user-authored brand guidance.

Reading this as: a research workbench for combustion researchers, in a laboratory notebook visual language, ENERGY 2 / RHYTHM 2 / MOTION 1.

Domain: droplets, flame extinction, observation windows, provenance, intervention events, sensor gaps, evidence applicability.
Color world: off-white laboratory paper, graphite labels, oxidized copper equipment, amber cautions, red danger indicators, green completed checks.
Signature: an observation-window ruler that connects measured channels, the continuous verification hold, intervention times and the decision ledger.
Defaults replaced: ornamental statistics become real run state; feature-card grids become evidence rows; chat-first AI becomes source-linked explanation alongside deterministic rules.

Intent: researchers inspect evidence, approve a synthetic plan and observe how interventions change later measurements.
Hierarchy: the question and evidence library lead Explore; observed signals and current combustion state lead Lab; the approval summary leads Scenario.
Palette: neutral notebook surfaces with a copper action accent; semantic red/green/amber identify actual states with text.
Depth: borders and flat surface shifts keep charts and source text legible.
Surfaces: paper canvas, white reading panels, inset neutral controls. Dark mode uses graphite with the same hierarchy.
Typography: IBM Plex Sans for scientific labels and readable data; IBM Plex Mono only for timestamps and identifiers. Sizes 12/14/16/20/28/40 with tabular numeric values.
Spacing: 4px base; 12-16px controls, 24px panels, 40px major separation.
Navigation: Library, Simulation Lab and Run archive directly support the specified journey. Source records open investigation details; Compare is a contextual destination.
Motion: 140ms opacity/color feedback only. Measurement progress reflects actual worker updates and can be paused.

Component intent checkpoints:
- App shell: orient the researcher; compact identity and persistent route labels; flat paper/copper tokens; 16px type; 24px gutters.
- Evidence library: foreground the scientific question and source applicability; generous headline then dense review rows; source classifications stay adjacent.
- Investigation/compare: foreground scope differences and unknown fields; aligned definition rows, no invented quantitative claims.
- Scenario/plan: foreground explicit review and approval; native labeled inputs and a named immutable profile; 24px form grouping.
- Lab/chart: foreground observed signals and current state; line series answer change over time; zero baseline, named sim_unit, gaps remain gaps, data table alternative.
- Run archive/report: foreground reproducibility and event history; no fictional activity; named seed/profile/references and downloadable immutable output.

No generated raster imagery or invented NASA logos are used. The schematic droplet is explicitly labeled conceptual, not an experimental frame. No NASA affiliation is claimed.

Icon sourcing: Phosphor regular-weight icons are chosen for their compact scientific-tool legibility. Book = sources, line chart = lab, history = archived runs, branching = independent event history, warning = quality/danger, and play/pause = virtual-clock control. Icons duplicate a visible label or carry an explicit accessible button name. The text-only FLARE identity avoids inventing a brand mark.

Typography assets are bundled locally from Fontsource under the IBM Plex OFL license, so the interface does not depend on Google Fonts at runtime.
