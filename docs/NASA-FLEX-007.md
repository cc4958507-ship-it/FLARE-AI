# NASA PSI-69 / FLEX-007 measurement import

The application now includes NASA's **FLEX-007**, CIR test **20CAL13**, a free-floating heptane droplet experiment dated April 10, 2009. These are NASA-supplied tabulated image-analysis observations, not simulated values and not raw camera images.

- Investigation: https://psi.nasa.gov/physci/repo/data/investigations/PSI-69
- Citation: NASA Physical Sciences Informatics, Flame Extinguishment Experiment, https://doi.org/10.60555/mbq8-0451
- License declared by NASA's investigation record: CC0-1.0, https://spdx.org/licenses/CC0-1.0.html
- Retrieved: November 14, 2026. Investigation metadata version 5; selected original text files version 1, downloaded through the file endpoint with studyVersion=1. Each selected file's exact endpoint, ID, key, size and SHA-256 is in `backend/data/nasa/PSI-69/FLEX-007/manifest.json`.

## Source package

Five original text files retain their downloaded bytes: `FLEX-007_DropletData.txt`, `FLEX-007_ColorCamData.txt`, `FLEX-007_LLUVData.txt`, `FLEX-007_TestSheet.txt`, and `20CAL13_Readme.txt`. `investigation.json` is a UTF-8 saved snapshot of the public investigation JSON response. It is metadata, not a measurement file. The manifest records checksums for all six artifacts. No temporary signed download credentials are stored.

The public file catalog was retrieved with `POST https://psi.nasa.gov/geode-py/ws/files/v2`, using `fileType=study`, `studyId=PSI-69`, `version=1` and `folder=psi-data/PSI-69`. It contained 8,851 file entries. This implementation imports one selected run, not that entire archive.

## Mapping and validation

`flare.nasa_flex.load_flex` checks original file hashes and sizes before parsing. It accepts the known tab-delimited headers, including legacy carriage-return line endings, and rejects malformed rows, nonfinite values, non-increasing source timestamps and timestamp collisions after conversion. Unknown source schemas fail rather than being guessed.

| File | Channels | Observations per channel |
| --- | --- | --- |
| DropletData | Diameter, zeroed X position, zeroed Y position | 141 |
| ColorCamData | Flame diameter | 158 |
| LLUVData | Flame diameter, droplet X position, droplet Z position | 177 |

The result contains 1,112 channel observations across seven channels. The 282 missing X/Y values remain null; no interpolation is performed. Each observation retains the original numeric text and unit, original source time, source filename, line and column. Millimeters are normalized to meters. Zero diameters remain reported zeroes, not inferred extinction events. Positions can be negative.

Two flame-standoff columns have no explicit header unit. They remain in the downloadable original files and are explicitly excluded from normalized measurements; the parser does not assume they are millimeters or ratios.

The earliest supplied source timestamp is `-1.466667000000598 s`. Relative time is the source time minus this common origin, rounded half up to milliseconds. Relative zero means the earliest supplied observation, not ignition or extinction. Original source times retain their sign and precision. Each camera's separate source timestamps are preserved; channels are not resampled or asserted to be experimentally synchronized.

## Conditions and scientific limits

The test sheet reports heptane, pressure 1.00 atm, ambient temperature 300.44 K, oxygen mole fraction 0.21, nitrogen mole fraction 0.79, no supporting fiber and initial diameter 1.82 mm. These are reported test conditions, not time-series sensor readings or newly calibrated values.

The test sheet says a luminous flame obscures a substantial part of the droplet history and that the droplet burns to disruption. The associated readme calls the release preliminary and enumerates missing LLLUV/color image frames. The implementation preserves these limitations alongside the data. No independent calibration, uncertainty analysis, combustion status, atmospheric assessment or safety verification is performed.

The user-supplied NASA booklet *Combustion in Reduced Gravity* (NP-2015-10-034-JSC), pages 12–13, describes FLEX and FLEX-2; pages 33–34 explain cool-flame findings. It provides scientific context, not ground truth or calibration for FLEX-007. This run is not labeled as a cool-flame experiment based on that general discussion.

## Application use

Open `/datasets`, load NASA FLEX-007 and inspect the seven channels, recorded point plot, original timestamps and table. A dataset URL with `?dataset=<id>` preserves the selection across reload. Source artifacts can be downloaded independently and verified against their checksums.

`POST /api/v1/datasets/nasa/flex-007` validates and imports the bundled data without a live network call. Repeated imports reuse the same dataset. Migration `003` adds original binary source artifacts in PostgreSQL. Normalized observations and artifacts commit in the same transaction. Synthetic runs and their verification profile remain separate.

This provides documented experimental replay, not a calibrated physical/chemical model. Camera archives, camera calibration validation, other NASA run formats and scientific model fitting remain future work.

## Validation

36 backend tests passed in the dedicated PostgreSQL test database. The real-source tests verify known counts, unit conversion, negative source timestamps, preserved nulls, exclusion of unspecified-unit columns, checksum failure, non-increasing source time rejection, idempotent persistence and byte-for-byte original download roundtrip. TypeScript and Vite production builds passed. The running application successfully imported FLEX-007 into its local database, showed all seven channel choices and 282 missing values, and retained the selected dataset after page reload. Desktop and mobile layout were inspected; the primary-button hover contrast and four-item mobile navigation wrapping were corrected. Full Playwright suite execution remains outstanding.
