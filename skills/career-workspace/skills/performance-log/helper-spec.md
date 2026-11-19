# perf_count.py specification

`performance-log` and `performance-review` count with this helper instead of counting by hand. The agent builds it from this page into the workspace on first use and checks it against the fixture below. Nothing here is shipped as code.

```text
SPEC_VERSION = 1
```

## Build

- One file: `performance/tools/perf_count.py`. Python 3, standard library only, no network, no writes outside the cycle folder it is given (and `index.md` inside it).
- Define `SPEC_VERSION = 1` near the top.
- Keep the code plain; it is read by the next agent that has to fix it.

## Command line

| Command | Does |
|---|---|
| `python3 performance/tools/perf_count.py --version` | Prints `SPEC_VERSION` and exits 0 |
| `python3 performance/tools/perf_count.py stats <cycle-dir> [--as-of YYYY-MM-DD]` | Prints the stats JSON below to stdout. `--as-of` defaults to today |
| `python3 performance/tools/perf_count.py index <cycle-dir>` | Rewrites `<cycle-dir>/index.md` in the format below and prints nothing |

Print JSON with `json.dumps(result, indent=2, sort_keys=True)`. Exit 1 with a one-line message on stderr when `<cycle-dir>/goals.md` is missing or its frontmatter lacks `cycle`, `cycle_start` or `cycle_end`.

## Inputs

- **Frontmatter** is the block between the first two lines that are exactly `---`. Each line is `key: value`. A value in `[...]` is a list: split on commas, strip spaces, `[]` is empty. `true` and `false` are booleans. Anything else is a string with surrounding spaces and quotes stripped.
- **`<cycle-dir>/goals.md`:** frontmatter gives `cycle`, `cycle_start`, `cycle_end`. Goal ids come from the body: a `## <Set>` heading sets the prefix (its first word, lowercased: `performance`, `promotion`), and each `### <slug> · <name>` heading under it is goal `<prefix>/<slug>`.
- **`<cycle-dir>/entries/*.md`:** one entry per file, sorted by file name. Required frontmatter keys: `date`, `date_inferred`, `employer`, `goals`, `projects`, `people`, `topics`, `above_and_beyond`, `highlight`, `source`.
- **`<cycle-dir>/calendar.md`** (optional): every line that starts with `- YYYY-MM-DD` names a non-workday. Other lines are ignored.

## Rules

- **Invalid entry:** a file missing any required key. It is listed in `invalid_entries` (`missing` sorted alphabetically) whatever its date, and left out of every other count and of `index.md`.
- **Range:** `start` = `cycle_start`, `end` = the earlier of `--as-of` and `cycle_end`. Both inclusive.
- **Counted entries:** valid entries whose `date` is inside the range.
- **Workdays:** Monday to Friday inside the range, minus `calendar.md` dates. A listed date that is already a weekend is not subtracted twice.
- **`workdays_with_entries`:** distinct `date` values of counted entries that are workdays. Work done on a holiday or weekend counts in `entries_total` but not here.
- **`by_goal`:** every goal id in `goals.md`, with 0 when unused, plus any other goal id that a counted entry names. Value is the number of counted entries naming it.
- **`by_project`, `by_person`, `by_topic`:** slug → number of counted entries naming it. Only slugs that appear.
- **`project_spans`:** for each project in `by_project`, the first and last `date` among counted entries.
- **`near_duplicates`:** compare slugs within each of projects, people and topics (not across kinds), using the slugs in the counted entries. A pair is near-duplicate when the slugs differ but are equal after lowercasing and removing every non-alphanumeric character, or when both are longer than 4 characters and their Levenshtein distance is 2 or less. Each pair is `[a, b]` with `a < b`; the list is sorted.

## stats JSON keys

`spec_version`, `cycle`, `range` (`{start, end}`), `workdays`, `workdays_with_entries`, `entries_total`, `by_goal`, `by_project`, `by_person`, `by_topic`, `project_spans` (`slug → {first, last}`), `near_duplicates`, `invalid_entries` (`[{file, missing}]`, `file` is the file name only, sorted by file).

## index.md format

All valid entries, whatever their date. Four sections in this order: Goals, Projects, People, Topics. Within a section, keys sorted alphabetically; a key with no entries is left out; under each key, one line per entry sorted by file name: `- [<file stem>](entries/<file name>)`. Exactly one blank line between blocks, and the file ends with one newline. The fixture's expected `index.md` below is the reference.

## Check (the gate)

Everything the check writes stays in `performance/tools/selftest/`. It is the helper's own folder: it is kept between runs and never deleted, and nothing is written outside the workspace.

1. Write (overwrite) every fixture file below into `performance/tools/selftest/` with the paths shown, plus the expected stats as `selftest/expected-stats.json` and the expected index as `selftest/expected-index.md`.
2. Run `python3 performance/tools/perf_count.py stats performance/tools/selftest --as-of 2026-03-13` and compare the **parsed** JSON with `expected-stats.json`. They must be equal.
3. Run `python3 performance/tools/perf_count.py index performance/tools/selftest` and compare `selftest/index.md` with `expected-index.md`, ignoring only trailing whitespace at the end of the file.
4. Both equal: write `performance/tools/CHECKED` with two lines, `spec_version: 1` and `sha256: <sha256 of perf_count.py>`.
5. Anything differs: fix the script, not the fixture or the expected output, and run the check again. If it still fails after three fixes, stop and report what differs.

## Fixture

`selftest/goals.md`:

```markdown
---
cycle: TEST
cycle_start: 2026-03-02
cycle_end: 2026-12-31
---

## Performance

### detection-response · Detection
Fixture goal.

### vuln-mgmt · Vulnerabilities
Fixture goal.

### security-awareness · Awareness
Fixture goal.

## Promotion

### cross-team-leadership · Cross-team leadership
Fixture goal.

### strategic-impact · Strategic impact
Fixture goal.
```

`selftest/calendar.md`:

```markdown
# Non-workdays

- 2026-03-07 weekend listed by mistake
- 2026-03-09 holiday
```

`selftest/entries/2026-03-02_0900_alpha-kickoff.md`:

```markdown
---
date: 2026-03-02
date_inferred: false
employer: Example Corp
goals: [performance/detection-response]
projects: [alpha]
people: [jane-doe]
topics: [automation]
above_and_beyond: false
highlight: false
source: raw/2026-03-13_1700.md
---
- Fixture entry.
```

`selftest/entries/2026-03-02_1400_alpha-review.md`:

```markdown
---
date: 2026-03-02
date_inferred: false
employer: Example Corp
goals: [performance/detection-response, promotion/cross-team-leadership]
projects: [alpha]
people: [jane-doe, raj-patel]
topics: [automation, review]
above_and_beyond: true
highlight: true
source: raw/2026-03-13_1700.md
---
- Fixture entry.
```

`selftest/entries/2026-03-04_1000_patching.md`:

```markdown
---
date: 2026-03-04
date_inferred: false
employer: Example Corp
goals: [performance/vuln-mgmt]
projects: [patching]
people: [raj-patel]
topics: [patching]
above_and_beyond: false
highlight: false
source: raw/2026-03-13_1700.md
---
- Fixture entry.
```

`selftest/entries/2026-03-09_1100_holiday-work.md`:

```markdown
---
date: 2026-03-09
date_inferred: false
employer: Example Corp
goals: []
projects: [alpha]
people: [jane-do]
topics: [automation]
above_and_beyond: false
highlight: false
source: raw/2026-03-13_1700.md
---
- Fixture entry.
```

`selftest/entries/2026-03-12_1500_training.md`:

```markdown
---
date: 2026-03-12
date_inferred: true
employer: Example Corp
goals: [performance/security-awareness]
projects: []
people: []
topics: [training]
above_and_beyond: false
highlight: false
source: raw/2026-03-13_1700.md
---
- Fixture entry.
```

`selftest/entries/2026-03-12_1600_broken.md`:

```markdown
---
date: 2026-03-12
date_inferred: false
goals: []
projects: []
people: []
topics: [training]
above_and_beyond: false
highlight: false
---
- Fixture entry missing employer and source.
```

`selftest/entries/2026-03-16_0900_later.md`:

```markdown
---
date: 2026-03-16
date_inferred: false
employer: Example Corp
goals: [performance/vuln-mgmt]
projects: [patching]
people: []
topics: [patching]
above_and_beyond: false
highlight: false
source: raw/2026-03-16_0930.md
---
- Fixture entry after the as-of date.
```

## Expected stats (`--as-of 2026-03-13`)

```json
{
  "by_goal": {
    "performance/detection-response": 2,
    "performance/security-awareness": 1,
    "performance/vuln-mgmt": 1,
    "promotion/cross-team-leadership": 1,
    "promotion/strategic-impact": 0
  },
  "by_person": {
    "jane-do": 1,
    "jane-doe": 2,
    "raj-patel": 2
  },
  "by_project": {
    "alpha": 3,
    "patching": 1
  },
  "by_topic": {
    "automation": 3,
    "patching": 1,
    "review": 1,
    "training": 1
  },
  "cycle": "TEST",
  "entries_total": 5,
  "invalid_entries": [
    {
      "file": "2026-03-12_1600_broken.md",
      "missing": [
        "employer",
        "source"
      ]
    }
  ],
  "near_duplicates": [
    [
      "jane-do",
      "jane-doe"
    ]
  ],
  "project_spans": {
    "alpha": {
      "first": "2026-03-02",
      "last": "2026-03-09"
    },
    "patching": {
      "first": "2026-03-04",
      "last": "2026-03-04"
    }
  },
  "range": {
    "end": "2026-03-13",
    "start": "2026-03-02"
  },
  "spec_version": 1,
  "workdays": 9,
  "workdays_with_entries": 3
}
```

## Expected index.md

```markdown
# Index

Built by perf_count.py from entries/. Rebuilt on every capture; don't edit by hand.

## Goals

### performance/detection-response
- [2026-03-02_0900_alpha-kickoff](entries/2026-03-02_0900_alpha-kickoff.md)
- [2026-03-02_1400_alpha-review](entries/2026-03-02_1400_alpha-review.md)

### performance/security-awareness
- [2026-03-12_1500_training](entries/2026-03-12_1500_training.md)

### performance/vuln-mgmt
- [2026-03-04_1000_patching](entries/2026-03-04_1000_patching.md)
- [2026-03-16_0900_later](entries/2026-03-16_0900_later.md)

### promotion/cross-team-leadership
- [2026-03-02_1400_alpha-review](entries/2026-03-02_1400_alpha-review.md)

## Projects

### alpha
- [2026-03-02_0900_alpha-kickoff](entries/2026-03-02_0900_alpha-kickoff.md)
- [2026-03-02_1400_alpha-review](entries/2026-03-02_1400_alpha-review.md)
- [2026-03-09_1100_holiday-work](entries/2026-03-09_1100_holiday-work.md)

### patching
- [2026-03-04_1000_patching](entries/2026-03-04_1000_patching.md)
- [2026-03-16_0900_later](entries/2026-03-16_0900_later.md)

## People

### jane-do
- [2026-03-09_1100_holiday-work](entries/2026-03-09_1100_holiday-work.md)

### jane-doe
- [2026-03-02_0900_alpha-kickoff](entries/2026-03-02_0900_alpha-kickoff.md)
- [2026-03-02_1400_alpha-review](entries/2026-03-02_1400_alpha-review.md)

### raj-patel
- [2026-03-02_1400_alpha-review](entries/2026-03-02_1400_alpha-review.md)
- [2026-03-04_1000_patching](entries/2026-03-04_1000_patching.md)

## Topics

### automation
- [2026-03-02_0900_alpha-kickoff](entries/2026-03-02_0900_alpha-kickoff.md)
- [2026-03-02_1400_alpha-review](entries/2026-03-02_1400_alpha-review.md)
- [2026-03-09_1100_holiday-work](entries/2026-03-09_1100_holiday-work.md)

### patching
- [2026-03-04_1000_patching](entries/2026-03-04_1000_patching.md)
- [2026-03-16_0900_later](entries/2026-03-16_0900_later.md)

### review
- [2026-03-02_1400_alpha-review](entries/2026-03-02_1400_alpha-review.md)

### training
- [2026-03-12_1500_training](entries/2026-03-12_1500_training.md)
```
