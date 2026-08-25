# Production Analytics Runbook

## Data contract

Each source has a declared business key in `src/config.py`. Ingestion stores the original payload unchanged, records file arrival time and schema version, and rejects files missing required keys or required event timestamps. Contract failures stop the run and create an alert rather than silently producing partial metrics.

## Lineage

`data/raw` -> staging views -> data-quality audit -> cleaned tables -> golden dimensions/facts -> account-month features -> metric tables -> dashboard and memo. Every metric is defined in `outputs/tables/metric_dictionary.csv`; payment recovery is reconciled to the validated payment table before publication.

## Incremental processing and late data

Process new event files by source watermark with a seven-day lookback. The lookback absorbs late-arriving events and re-computes affected account-month partitions. Keep the raw event and ingestion timestamps so event time and arrival time remain distinguishable.

## Backfills

A backfill accepts an explicit start and end date, rebuilds all affected partitions plus the attribution window after the end date, and writes outputs to a run-specific staging location. Publish only after row-count, foreign-key, payment, and metric reconciliation checks pass.

## Data-quality controls

Monitor primary-key uniqueness, foreign-key match rate, null required fields, invalid timestamps, duplicate payment references, payment status conflicts, unmapped disposition codes, and denominator continuity. Preserve rejected rows and the reason for rejection in audit outputs.

## Monitoring and anomaly detection

Alert on failed contracts, unusual row-count changes, recovery totals outside a rolling historical band, sudden denominator changes, unexpected channel mix, and material divergence between raw and validated recovery. Dashboard publication is blocked when a critical control fails.

## Operational ownership

Data engineering owns ingestion and contracts. Analytics engineering owns clean/golden transformations and reconciliation. The collections analytics owner approves metric-definition changes. Leadership dashboards show the run timestamp, complete-month cutoff, data-quality status, and whether investment estimates are observed or modeled.
