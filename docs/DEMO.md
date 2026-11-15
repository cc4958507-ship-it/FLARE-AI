# Five-minute research demo

1. Open the library. Search `droplet`, open FLEX, inspect source, scope and missing raw measurements.
2. Select FLEX and the cool-flames article. Compare context, fuel and channels. Note the quantitative comparison limitation.
3. Create a scenario, choose `Reduce source at 20s`, retrieve evidence, review the required channels and approve the synthetic plan.
4. Set playback to 16× and start. After 20s the visible flame disappears, but Danger remains latched. Inspect the decision trace.
5. Create a branch at 19s. Apply `Stop source`, then start it. It rebuilds the same past and changes future measurements. After clearance and continuous hold, it becomes Verified within simulated conditions.
6. Create another scenario with `Stop at 0s + missing CO channel`. It remains Uncertain because required observations are absent.
7. Download JSON and open the printable HTML report. Refresh the lab and restart the API/worker: committed frames, events and plans remain in PostgreSQL.

Pause freezes virtual time. Reset view redraws the chart without changing data. New branch creates a distinct run. Completed runs require a branch for new actions. Atmosphere status remains independent from combustion status.
