# Filtering Results

## Hard Filters

Apply binary constraints mechanically: dates, geography, numeric thresholds, category membership, and explicit exclusions. Remove failures without making a judgment call.

## Soft Filters

For criteria such as genuine opinion, actual production use, or high signal, fetch source content when snippets are insufficient, make a judgment, and attach a short keep/drop rationale. Semantic negation also requires content review because the excluded idea may be phrased indirectly.

## Order and Time

1. Apply hard filters first to eliminate rows cheaply.
2. Apply soft filters only to remaining rows.

Calculate exact boundaries for relative dates before filtering. If a date is ambiguous, state the uncertainty rather than silently deciding.

## Precision

- For exhaustive requests, include borderline rows and flag them.
- For best-of or top-N requests, prioritize precision and remove borderline rows.
- Otherwise, include borderline rows with a clear qualification.
