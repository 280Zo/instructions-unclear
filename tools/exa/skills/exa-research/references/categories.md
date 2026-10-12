# Advanced Search Categories

Use `exa_web_search_advanced_exa` when a structured category or filter is required. `query` is required for every category. The documented category values are `publication`, `financial report`, `personal site`, `company`, `people`, and `news`.

## Category Use

| Category | Use for |
|---|---|
| `publication` | Academic papers, preprints, and scientific research |
| `financial report` | SEC filings, earnings reports, annual reports, investor materials, and statements |
| `personal site` | Personal blogs, portfolios, independent analysis, and practitioner tutorials |
| `company` | Company discovery and structured company metadata such as funding, headcount, location, and revenue |
| `people` | Public professional profiles, LinkedIn-weighted discovery, and biographies |
| `news` | Announcements, press coverage, interviews, and recent events |

## Complete Parameter List

| Group | Parameters |
|---|---|
| Core | `query`, `numResults`, `type` (`auto`, `fast`, `deep`, `instant`), `category` |
| Domains | `includeDomains`, `excludeDomains` |
| Dates | `startPublishedDate`, `endPublishedDate`, `startCrawlDate`, `endCrawlDate` |
| Text | `includeText`, `excludeText` |
| Extraction | `textMaxCharacters`, `contextMaxCharacters`, `enableSummary`, `summaryQuery`, `enableHighlights`, `highlightsNumSentences`, `highlightsPerUrl`, `highlightsQuery` |
| Additional | `userLocation`, `moderation`, `additionalQueries`, `maxAgeHours`, `livecrawlTimeout`, `subpages`, `subpageTarget` |

## Parameter Support and Errors

`OK` means the supplied category skill documents support. `No documented exception` means the supplied skills do not list a restriction; validate the call if it matters. `400` means the supplied skills explicitly document an error.

| Category | Domains | Dates | `includeText` | `excludeText` | Extraction and additional parameters |
|---|---|---|---|---|---|
| `publication` | OK | OK | OK, one item only | OK, one item only | OK |
| `financial report` | OK | OK | OK, one item only | 400: unsupported | No documented exception |
| `personal site` | OK | OK | OK, one item only | OK, one item only | No documented exception |
| `company` | 400: both domain filters unsupported | 400: all four date filters unsupported | One item only | One item only | No documented exception |
| `people` | `excludeDomains` 400; `includeDomains` only accepts LinkedIn domains | 400: all four date filters unsupported | 400: unsupported | 400: unsupported | No documented exception |
| `news` | OK | OK | One item only | One item only | No documented exception |

## Universal Restrictions

- `includeText` and `excludeText` accept only single-item arrays. A two-or-more-item array causes a 400 error wherever the parameter is supported. Put multiple terms in `query` or run separate searches.
- The `company` category rejects `includeDomains`, `excludeDomains`, `startPublishedDate`, `endPublishedDate`, `startCrawlDate`, and `endCrawlDate` with 400 errors.
- The `people` category rejects all published/crawl date filters, `includeText`, `excludeText`, and `excludeDomains`; `includeDomains` is restricted to LinkedIn domains such as `linkedin.com`.
- The `financial report` category rejects `excludeText` with a 400 error.
- Use ISO 8601 for date values.

## Worked Calls

Publication with date and text filtering:

```
exa_web_search_advanced_exa {
  "query": "transformer attention mechanisms efficiency",
  "category": "publication",
  "startPublishedDate": "2025-01-01",
  "includeText": ["LLM"],
  "numResults": 15,
  "type": "deep"
}
```

Financial reports without unsupported `excludeText`:

```
exa_web_search_advanced_exa {
  "query": "10-K annual report AI companies",
  "category": "financial report",
  "includeDomains": ["sec.gov"],
  "startPublishedDate": "2025-01-01",
  "enableHighlights": true,
  "highlightsQuery": "What are the main cybersecurity risks?",
  "numResults": 15
}
```

Personal sites excluding aggregators:

```
exa_web_search_advanced_exa {
  "query": "startup founder lessons",
  "category": "personal site",
  "excludeDomains": ["medium.com", "substack.com"],
  "numResults": 15,
  "type": "auto"
}
```

Company discovery without domain or date filters:

```
exa_web_search_advanced_exa {
  "query": "AI infrastructure startups San Francisco",
  "category": "company",
  "numResults": 20,
  "type": "auto"
}
```

People discovery without unsupported filters:

```
exa_web_search_advanced_exa {
  "query": "VP Engineering AI infrastructure London",
  "category": "people",
  "numResults": 20,
  "type": "auto"
}
```

News within a date window:

```
exa_web_search_advanced_exa {
  "query": "AI safety announcement",
  "category": "news",
  "startPublishedDate": "2025-01-01",
  "numResults": 15
}
```
