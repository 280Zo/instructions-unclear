# Searching with Exa

You have three tools:
- **`exa_web_search_exa`** -- search by query. Supports `query` and `numResults` params. Use `category: ` inline in the query string for category filtering.
- **`exa_web_fetch_exa`** -- read full content from known URLs. Use after search when snippets are insufficient.
- **`exa_web_search_advanced_exa`** -- search with real structured parameters (`category`, domain filters, date filters, text filters, content extraction). Use this when you need actual filters rather than an inline category hint. Each category accepts a different subset of parameters; unsupported ones return 400. Read `categories.md` (same directory as this file) before using it.

These three are the only Exa tools available. Do not use Bash, Grep, Read, or Write to process results. Filter and summarize results inline.

**Which to reach for:** start with `exa_web_search_exa` for ordinary discovery -- it is simpler and cheaper. Switch to `exa_web_search_advanced_exa` when the task genuinely needs a date window, a domain include/exclude list, text filters, or summary/highlight extraction.

## How Exa Search Works

Exa uses vector embeddings, not keywords. It finds pages semantically similar to your query. It does not match keywords exactly, directly understand boolean logic (AND/OR/NOT), or validate that results meet your criteria. You are describing a target page, and Exa returns the nearest neighbors in embedding space.

## Writing Good Queries

**Describe the page you want to find**, not the fact you want to know.

| Looking for | Bad query | Good query |
|---|---|---|
| Blog posts about X | "X" | "detailed blog post about X written by a practitioner" |
| Company doing Y | "Y company" | "category:company startup building Y for enterprise" |
| Person at company | "person at company" | "category:people senior engineer at Acme" |

Write queries as natural grammatical phrases.

**`numResults` sizing -- match to query precision:**

| Query precision | numResults | Example |
|---|---|---|
| Named entity (specific person/company) | 5 | `"WaveForms AI founding story funding details"` |
| Precise filter (narrow category + constraints) | 10 | `"category:company developer tools API testing Series A"` |
| Broad discovery (wide category, few constraints) | 15 | `"category:news engineer launches startup 2025 2026"` |

Never use numResults above 25. If you need more coverage, run more queries with different angles at n=10-15 rather than one query at n=50.

**Use category filters** when searching for a specific entity type. Available inline categories: `company`, `publication`, `news`, `personal site`, `people`. Add `category: ` at the start of your query string.

```
exa_web_search_exa { "query": "category:publication sparse attention mechanisms for long context", "numResults": 10 }
exa_web_search_exa { "query": "category:people VP Engineering AI infrastructure San Francisco", "numResults": 10 }
exa_web_search_exa { "query": "category:company developer tools for API testing", "numResults": 10 }
```

## Query Diversity

When you need to run multiple queries on the same topic, make sure they target genuinely different angles, not just synonym swaps. "overhyped" vs "overrated" vs "disappointment" are the same angle. A skeptic angle vs a builder angle vs a practitioner angle are genuinely different.

**Word order affects embeddings.** "Python async patterns for web scraping" and "web scraping async patterns in Python" can sometimes return different results. Use this to your advantage when you need coverage -- run 2-3 phrasings in parallel.

## Encoding Time

If your task involves time ("last week", "recent", "this month"), calculate exact dates FIRST from the current date in your environment context. Then, with `exa_web_search_exa`, encode dates semantically in the query: "published in March 2026". With `exa_web_search_advanced_exa` you can use real `startPublishedDate` / `endPublishedDate` filters instead -- but check `categories.md` first, since several categories reject date filters. Never eyeball dates.

## Anti-Patterns

- Boolean operators ("AND", "NOT") are just words to Exa, not operators
- Quotes don't force exact phrase matching
- Very short queries (1-2 words) produce scattered, low-quality results
- Don't use dates from examples -- always calculate from the current date
- Don't pass a filter parameter that the chosen `category` rejects -- it is a hard 400, not a silent ignore

## When Searches Return Nothing

If a query returns 0 or only irrelevant results:
a. Make the query longer and more specific
b. Try a different angle, not a synonym swap
c. If multiple angles return nothing, the topic likely has limited web coverage -- report that rather than fabricating results

## Category Strategy

If your task targets a specific entity type -- academic papers, financial filings, personal blogs, companies, people, news -- read `categories.md` (same directory as this file) for which `category` value to use, which parameters that category supports, and worked example calls.

## Domain Patterns

### Code and documentation

Always name the programming language and framework or library.

```
exa_web_search_exa { "query": "Stripe API create subscription Node.js code example", "numResults": 5 }
exa_web_search_exa { "query": "React hydration mismatch server client explanation fix", "numResults": 10 }
exa_web_search_exa { "query": "GitHub repository library example project open source", "numResults": 10 }
```

### Companies

Use `category:company` inline for simple discovery; use the advanced tool for structured company filtering after checking `categories.md`.

```
exa_web_search_exa { "query": "category:company AI infrastructure startups San Francisco", "numResults": 10 }
exa_web_search_exa { "query": "category:company Series B fintech payments", "numResults": 10 }
exa_web_search_exa { "query": "category:company companies like Stripe", "numResults": 8 }
```

For competitive intelligence, vary the angle: similar companies, category tools, and recent launch or funding announcements. For funding, pair a company-category query with a query for its funding round, amount, and investors.

### News

```
exa_web_search_exa { "query": "category:news topic announcement", "numResults": 15 }
exa_web_search_exa { "query": "topic news update latest development month year", "numResults": 15 }
exa_web_search_exa { "query": "event reaction analysis commentary", "numResults": 12 }
exa_web_search_exa { "query": "event criticism concerns issues bugs", "numResults": 15 }
```

### Publications

```
exa_web_search_exa { "query": "category:publication sparse attention mechanisms for long context transformers", "numResults": 12 }
exa_web_search_exa { "query": "category:publication topic comprehensive survey review", "numResults": 10 }
exa_web_search_exa { "query": "category:publication author name topic", "numResults": 5 }
```

For seminal work, find survey papers first, then fetch them to identify foundational references.

### People

Be specific about company, role, location, or time period; broad role-only queries produce irrelevant profiles.

```
exa_web_search_exa { "query": "category:people engineer at OpenAI", "numResults": 10 }
exa_web_search_exa { "query": "category:people Head of Growth B2B SaaS startup San Francisco", "numResults": 12 }
exa_web_search_exa { "query": "category:people Jane Smith Anthropic machine learning", "numResults": 5 }
```

For broad company coverage, search departments and seniority in parallel, then supplement with team pages and hiring announcements. Deduplicate by canonical LinkedIn URL, or name plus current company when absent.

### Hidden relationships

Direct relationship claims often surface commentary rather than evidence. Start with the subject's official platforms, then seek indirect signals such as interviews, testimonials, case studies, duration markers, and distinctive terminology.

```
exa_web_search_exa { "query": "subject official website blog podcast", "numResults": 5 }
exa_web_search_exa { "query": "company case study customer success story", "numResults": 5 }
exa_web_search_exa { "query": "subject years decades longtime worked with known since", "numResults": 10 }
```

## When `exa_web_fetch_exa` Fails

Retry once with a smaller batch of URLs. If it still fails, skip those URLs and work with the remaining sources. Note in your output which sources you could not read.

## After Getting Results

Exa returns similarity, not validation. You must review titles/snippets and discard irrelevant results using your judgment. Don't assume all results match your criteria. For the most promising results, use `exa_web_fetch_exa` to read the full content.

```
exa_web_fetch_exa {
  "urls": ["https://promising-url-1.com", "https://promising-url-2.com"],
}
```
