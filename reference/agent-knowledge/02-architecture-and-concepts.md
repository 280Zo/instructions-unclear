# 02 Architecture and Concepts

[Index](README.md) · [Objectives](01-objectives-and-requirements.md) · [Technologies](03-technology-landscape.md) · [Evaluation](04-evaluation-and-experiments.md) · [Decisions](05-decisions-and-open-questions.md)

## A capability map, not a chosen stack

The following is a way to reason about the complete system. A product may implement several boxes; an existing memory application may supply most of them. Boundaries are responsibilities, not a requirement for separate services.

```text
agent interactions                 documents / photos / diagrams / tables
        |                                           |
  capture policy                            preserve original + identity
        |                                           |
  observations / decisions                   parse / OCR / vision
        |                                           |
        +----------> candidate facts and source anchors <---+
                              |
               entity resolution / typed relationships
               confidence / review / supersession policy
                              |
                  persistent knowledge + indexes
                              |
question + project scope -> retrieval planning / fusion / evidence checks
                              |
                 evidence delivered to the session agent
                              |
                  answer, citation or explicit uncertainty
```

Authorization, session identity, source lifecycle and maintenance apply throughout the flow. Adding a graph or vector index to one box does not establish the behavior of the others.

## Memory and knowledge are related but different

Use these terms consistently in this investigation:

- **Conversation/event history:** what was said or done. It is evidence of an interaction, not proof every assertion was correct.
- **Candidate memory/fact:** extracted or agent-authored information selected for reuse, with a source and interpretation status.
- **Curated knowledge:** a retained claim or decision with explicit identity, scope and confidence/confirmation policy. "Curated" need not mean manually entered, but the acceptance policy must be known.
- **Knowledge corpus:** source documents, code and other material that can be inspected independently of conversation history.

Memory systems can combine these. The architectural question is which representations to preserve and how derived claims remain connected to their sources, not whether to keep conversations or facts exclusively.

## Retrieval modes answer different questions

| Mode | Example target | Important boundary |
|---|---|---|
| Exact/keyword | `IF-42`, an error code, a quoted requirement | Semantic similarity alone is not exact identifier lookup |
| Text-vector | "Why did we choose this transport?" expressed in different words | A close vector match is relevance evidence, not proof a claim is true |
| Typed relationship | "What uses IF-42, and what depends on that component?" | Co-mention edges may help discovery but do not establish `uses` or `depends_on` |
| Direct image-vector | Find visually similar source images | Searching captions/OCR text is a different representation |
| Source inspection | Verify the returned fact against a page, region or code location | A stored summary cannot replace missing original evidence |

Hybrid retrieval means choosing and combining useful evidence, not invoking every index for every question. Evaluate identifier resolution, graph direction/type, ranking, filters, conflicts and citations together. Answer generation is a separate stage from finding the evidence.

## Document and image processing

Distinguish the jobs before choosing a model or parser:

1. **Preserve originals:** stable source identity, original bytes and source version.
2. **Extract structure/text:** document parsing, OCR, tables, reading order and page/region anchors where supported.
3. **Interpret pixels:** a vision-language model or the session model describes a photo/diagram or answers a visual question. Record the result as interpretation unless confirmed.
4. **Represent for retrieval:** text embeddings, optional image embeddings, exact indexes and source-grounded relationships.
5. **Maintain derivations:** changed/deleted originals must have defined effects on extracted content, facts and indexes.

Retaining image files does not mean interpreting them. Describing an image does not establish direct visual-similarity retrieval. Identifying diagram objects does not establish correct arrow direction or typed dependencies.

Examples and evidence for these different roles are retained in [03](03-technology-landscape.md), including Docling's document model and optional picture enrichment, and image/text encoders versus vision-language models.

## Processing choices are independent of storage choices

| Processing route | Question to evaluate |
|---|---|
| Calling session model writes selected knowledge | Can the agent make useful capture decisions without excessive context/tool overhead, and can other sessions retrieve them? |
| Separate local extraction/embedding/vision models | Which stages work locally, with what quality, provisioning and resource requirements? |
| External inference APIs | What content is sent, what credentials/costs apply, and which stages remain local? |
| Deterministic capture and structure extraction | What can be retained without generative inference, and what useful meaning remains unextracted? |

"No second API key," "no additional model call," "no hosted inference" and "no model downloads" are different conditions. They must not be used interchangeably.

## Storage and integration alternatives

These are alternatives to evaluate, not recommendations:

| Alternative | What existing technology may already supply | What the complete-system evaluation still needs |
|---|---|---|
| Memory application as the primary knowledge service | Capture hooks, sessions, retrieval, consolidation and tools, sometimes ingestion and source storage | Actual typed relationships, provenance, media behavior, lifecycle and host integration |
| Knowledge/temporal-memory framework with agent integration | Entity/fact extraction, graph/vector retrieval, source episodes or corpus pipelines | Capture policy, session/project behavior, supported integration and operating model |
| Composed specialist services | Existing memory workflow plus parser/vision pipeline, source repository and retrieval stores | Cross-component identities, source/version propagation, synchronization, authorization and failure recovery |
| Multi-model engine behind existing or adapted workflows | Related facts, graph/vector/full-text primitives in one engine | Capture, knowledge acceptance, original-source handling and agent-facing behavior; storage primitives alone are not the whole application |

Prefer checking existing implemented capabilities before assuming custom development. A hybrid arrangement can reuse an application and specialist processors without replacing every part of the current setup.

MCP is an integration boundary for exposing capabilities to agents, not a guarantee of automatic capture, shared storage, model reuse or session isolation. Native hooks/plugins, polling, explicit tool calls and API proxies have different capture behavior. Test the actual OpenCode path rather than inferring it from an MCP badge.

## Data types and what they need from storage

The system should accept any source type. "Storing anything" is achieved by keeping every original as a file and adding the representations each question type needs, not by forcing all content into one index. Most representations fit in one multi-model engine; one, multi-vector page-image search, narrows the choice of engine.

| Data | Original | Derived representations | Storage requirement |
|---|---|---|---|
| Code | Repository files | Symbols and code relationships, text chunks | Lexical index, optional text vectors, relationship tables or graph; or live search with no index |
| Documents and datasheets | PDF/Office files | Parsed items with page/region anchors, text chunks, extracted facts | Lexical index, text vectors, provenance columns |
| Visually rich pages | Same PDF | Optional page-image embeddings (many vectors per page) | **Multi-vector late-interaction search**, which only some engines support natively (for example LanceDB, Qdrant, Vespa) |
| Photographs and diagrams | Image files | Labelled VLM interpretation, optional single image vector, OCR text | Single-vector index for image similarity; text indexes for interpretations |
| Session history | OpenCode session store | Verbatim records, extracted decisions and facts | Lexical index, text vectors, timestamps |
| Facts and relationships | References to the above | Typed edges with origin, validity times and support lists | Relational tables with recursive queries suffice for 2–3 hop questions at this scale; a graph engine adds value for deep or variable-length traversal and graph algorithms |
| Binaries and firmware | Files | Knowledge produced by analysis tools | Treated like other originals plus extracted facts |

Large binaries do not belong inside a database: keep them content-addressed on disk and store hashes and anchors. At the estimated scale, engine choice is driven more by concurrency, operational simplicity and multi-vector support than by data type.

### Size estimates

These are planning estimates under stated assumptions, not measurements. Assumptions per project: 10k–200k lines of code; 20–200 PDFs averaging 50–300 pages; 50–2,000 photographs at 3–8 MB; 50–1,000 sessions at 0.1–1 MB; 768-dimension float text vectors (about 3 KB each); ColPali-style page vectors at about 257 KB per page in 16-bit float or about 16 KB binary (1,030 vectors of 128 dimensions; figures from 03).

| Item | Per project | Central, 20 projects |
|---|---|---|
| Originals (documents, photos, binaries) | 0.2–20 GB | 4–400 GB |
| Text, lexical and vector indexes, facts and relationships | 50 MB–2 GB | 1–40 GB |
| Text vectors | 10k–500k | 0.2–10 million |
| Optional page-image vectors | 0.3–15 GB 16-bit float, 16 MB–1 GB binary | 6–300 GB 16-bit float, 0.3–20 GB binary |
| Session history | 5 MB–1 GB | 0.1–20 GB |

Everything fits on a workstation disk. The constraint that changes with topology is memory: an in-memory vector index over 10 million 768-dimension float vectors needs roughly 30 GB of RAM, while per-project indexes, quantization or disk-based indexes keep only active data resident. Page-image retrieval is the largest optional cost and is worth enabling only for visually rich projects.

## Deployment is a separate axis

| Pattern | Questions, not assumed answers |
|---|---|
| Project-contained storage | What follows checkout deletion? How do independent processes share state, and what lives outside the directory anyway? |
| Central service with project scopes | How do identities route requests? Which operations enforce scope, including traversal, caches, exports and background jobs? |
| Separate physical stores under central management | Can agents share a service interface while stores remain distinct? What is the backup/deletion burden? |
| Shared reference corpus plus project stores/scopes | How are shared sources authorized, versioned and included deliberately? How are cross-project claims prevented from leaking? |

Physical separation, namespaces and access control solve different problems. Backend sharing alone does not prove capture, visibility, ordering or multi-writer correctness.

### Where knowledge is stored: options compared

Databases separate tenants (here, projects) in three standard ways: **shared tables** with a project column, a **namespace per project** inside one database, or a **database per project**. Developer tools add two more choices: whether data lives inside the project folder or in a central directory, and whether plain files or a database are the source of truth. The options below cover these. Sources are in [03](03-technology-landscape.md#project-separation-research).

**1. A database inside each project folder** (the user's original direction)

| Pros | Cons |
|---|---|
| Stored inside the project, not in a global data directory | Can be committed to Git by mistake; one tool's in-repo memory folder held plaintext credentials because it was not ignored |
| Removed when the project directory is removed | Also lost if the directory is deleted by accident |
| Separate projects use separate databases | Several sessions or subagents opening the same file at once hit lock errors or lost writes, unless one process owns it |
| An unrelated project cannot reach another project's database through normal configuration | Each clone or worktree gets its own copy. That splits worktrees of one project; whether separate clones should share is still open |
| Moves and renames follow the project | The database lands wherever the memory server starts; in E13, PMB created `.pmb` in a throwaway directory |

**2. One central database, shared tables with a project column**

| Pros | Cons |
|---|---|
| One database to run, back up and migrate | Separation is only a filter; one missing or wrong filter leaks data (documented incidents) |
| Searching across projects is trivial | Deleting or restoring one project is harder |
| Recommended by some stores for many small tenants | Shared vector indexes can lose recall when filtered by project |

**3. One central database, a namespace per project, each with its own tables** (the user's proposal: records and knowledge tables per project)

| Pros | Cons |
|---|---|
| One database to run and back up | Weaker isolation than separate databases: same process and credentials |
| Each project's tables are separate objects, so a forgotten row filter cannot mix projects; choosing the wrong namespace still can | Schema changes must be applied to every namespace |
| Deleting a project means dropping its namespace | Only some stores have real namespaces. SQLite does not: its equivalent is attached files, limited to 10 by default |
| Searching across projects is easy because everything is in one database | Not removed automatically when a project directory is removed |
| Supported natively by several candidate stores (SurrealDB namespaces, ArangoDB and Chroma databases, Postgres schemas, LanceDB namespaces) | Neon (vendor) advises against schema-per-tenant unless experienced with it; many Postgres schemas slow `pg_dump` and tools |

**4. One central service, a separate database file per project in a central directory**

| Pros | Cons |
|---|---|
| Simplest delete, backup and restore of one project | Searching across projects means opening many databases |
| No shared tables, indexes or credentials between projects; Azure rates this model's isolation highest | A service must be running |
| Citus (vendor) suggests a database per tenant is maintainable at 5–50 tenants | Schema changes must be applied to every file |
| Only the active project's indexes need to be in memory | Not removed automatically when a project directory is removed |

**5. Plain files as the source of truth, with a search index rebuilt from them**

| Pros | Cons |
|---|---|
| Knowledge is readable and editable in any editor, and diffable with Git | The index must be kept in sync; one tool's watcher and write path raced and broke a project |
| The index can be deleted and rebuilt without losing anything | Semantic search is unavailable while the index rebuilds |
| Deleting a project's folder deletes its knowledge | Typed relationships and two-layer records/knowledge are harder to express in files |
| Used by Basic Memory, EverOS, Letta MemFS and Claude Code's project memory | Consistency depends on the agent keeping files tidy |

### Keeping projects apart with no setup

The system must be fully transparent, like PMB: no logins, no prompts, no decisions for the user or the model about where data goes (D12 in [05](05-decisions-and-open-questions.md)).

Local memory tools for one user mostly work this way: claude-mem, PMB and Claude Code's project memory pick the project from the working folder or repository without any user setup (03, K5 and project separation research).

How the project is picked automatically:

1. The memory tool runs inside OpenCode, and every OpenCode session belongs to a folder.
2. The tool turns that folder, or its Git repository, into a project name. E13 confirmed the plugin receives a project ID and every hook carries the session ID.
3. That name selects the project's namespace for every read and write. The model never passes a project name, so it cannot pick the wrong one.
4. Searching across projects is a separate tool the model calls on purpose. Each such read is logged.

Database logins per namespace and sandboxing were considered (Kubernetes and AWS use stronger boundaries, see 03) and rejected: they add setup and protect against threats that do not apply to one user's local database.

### Points that apply to every option

- **Project identity.** Many reported failures came from identifying the project wrongly. Folder paths break on move or rename. The first Git commit (OpenCode's current method) makes separate clones of one repository share an ID, which is wrong if clones should be separate (open question 13 in 05). The Git remote URL fails for local-only repositories. No single key found survives moves, separates clones and is shared by worktrees. A design suggestion, not a found practice: generate an ID once, store it in the Git common directory (which worktrees share), and check it against known paths on each use.
- **Store-enforced separation beats filters, but selection can still go wrong.** Cognee returned other datasets when access control was off. With Graphiti on FalkorDB, which keeps a separate graph per group, a write switched the shared connection to the group just written, so later reads for other groups silently returned nothing. Both show that the scope must be set reliably, not just stored separately.
- **One writer.** Embedded databases (SQLite, Kuzu/Ladybug, Chroma) are unsafe with several writing processes. A single service owning writes avoids this in every option.
- **Cleaning up deleted projects.** Central storage leaves orphans when a project is deleted; VS Code users report 18–100 GB of them. Tools avoid automatic deletion, because unmounted drives look like deleted folders. They list orphans and ask before removing.
- **Files on disk.** No option stops an agent reading another project's files directly. That boundary comes from OpenCode's permission settings.

### What project separation can and cannot protect against

| Threat | Example | What helps | What does not |
|---|---|---|---|
| Accidental mixing | Knowledge from one project appears in another because of a wrong or missing scope key | Stable project identity, automatic scoping by the service, separate physical stores | Caller-supplied filters that one omitted parameter defeats |
| Injected cross-project access | Text in a firmware image, web page or repository instructs the agent to search or export another project's memory | Service binding each session to its project regardless of what the model asks, explicit cross-project operations, excluding sensitive projects from cross-project search | Memory isolation alone: OpenCode agents can still read other projects' files on disk unless OpenCode permissions or sandboxing restrict them |
| Another local user or process | A program on the machine reads the memory files or calls a local HTTP endpoint | File permissions, stdio or authenticated local endpoints | Any design with an unauthenticated localhost service |

The second row is a real risk for reverse-engineering and security work, where untrusted content is the input. The memory design can limit what an injected instruction retrieves through memory, but the strongest boundary for files on disk is the host's permission system, outside memory design.

## Maintenance is part of knowledge behavior

Define how the system handles duplicate observations, entity aliases, contradictory claims, source revisions, supersession, source removal, stale embeddings, interrupted jobs, index rebuilds and backup retention. Derived knowledge needs a defined relationship to the evidence that created it.

A graph fact can be invalidated without deleting its history. A source can be removed while backups still retain it. A successful write can precede search-index visibility. These are cases for the proposed tests in [04](04-evaluation-and-experiments.md), not implied guarantees of any candidate.

## Candidate search pipeline to test

A starting design from the retrieval research in [03](03-technology-landscape.md#retrieval-embedding-models-and-search-methods). Not a decision; each step is a setting to measure (04, E20).

1. **Split content into chunks:** code by syntax tree with path and symbol headers; documents with Docling's structure-aware chunker and heading paths; session memory one item per conversation turn, keyed by extracted facts and timestamps.
2. **Keyword index:** whole identifiers and paths, split sub-words, and a trigram field for partial matches, with symbol and path matches weighted higher.
3. **Vector index:** a local embedding model that handles code (for example Qwen3-Embedding-0.6B on the GPU, or a small Granite or ModernBERT model on the CPU).
4. **Route the question:** identifiers, paths and error strings go keyword-first; "uses / depends on / calls" questions add relationship expansion; everything else uses combined search.
5. **Merge results:** start with RRF; switch to a weighted combination per question type once there are labelled questions.
6. **Pin exact matches:** an exact identifier or path match goes to the top and skips the reranker.
7. **Rerank** the top 20–50 with a local reranker that handles code (Qwen3-Reranker-0.6B or jina-reranker-v3).
8. **Return** about 10–20 compact results (id, location, one-line snippet, time) plus a tool to fetch full detail.

## Candidate ingestion pipeline for documents and images

A starting design from the research in [03](03-technology-landscape.md#documents-and-images-ingestion-on-the-target-hardware). Not a decision.

**Every file**

1. Fingerprint the file (SHA-256). Unchanged: skip. Changed: store a new version and mark the old one superseded. Missing: mark its records and knowledge removed.
2. Store the original once, named by its hash, as a record.

**Documents (PDF, Office)**

3. Convert with Docling on the GPU: accurate tables, OCR only for scanned pages, picture classification on, figure images saved. Store Docling's structured output as a record, with the Docling version and settings.
4. Describe figures by type: charts through chart extraction, diagrams and schematics through a local vision model. Store descriptions labelled as model-generated, with model and prompt.
5. Repair known problems: merge tables split across pages; catch whole-page drawings that would produce no chunks.
6. Chunk with Docling's structure-aware chunker. Give each chunk a stable ID from the file hash and its position, and keep page, location box and heading path.

**Photos and screenshots**

7. Keep EXIF and metadata; make a thumbnail.
8. Read text with an OCR engine (PP-OCRv5 or RapidOCR), keeping a box for each line.
9. Describe the image with a local vision model (for example Qwen3-VL 4B or 8B), with boxes for each item it names.
10. Cross-check: strings the vision model reports are re-read by OCR on their box. Matches become facts; mismatches stay unverified. Values, counts and arrow directions from the vision model stay low-confidence.
11. Add one image vector per photo (for example Qwen3-VL-Embedding-2B) for finding similar images.

**Knowledge**

12. Extract facts and relationships with a local model. Each links back to chunk or box, so it can be checked against the original.

A page-image index for datasheets is optional. The research supports adding it only if tests show text search misses figure, pinout or diagram questions; the cheapest version is one vector per page in the existing database.

## Patterns the evidence supports evaluating

The research summarized in [03](03-technology-landscape.md#findings-by-objective) points to the following design patterns. They are candidates to test, not decisions; any of them could be supplied by an existing product, a combination, or an adapted component.

| Pattern | Objectives | Why the evidence points here | Open trade-off |
|---|---|---|---|
| Keep originals and verbatim records as the stored value; index them by extracted facts and keys | K1, K3, K6 | Pure fact extraction loses detail; extracted keys over verbatim values improved recall and QA on LongMemEval | Storage volume and the extraction cost of the keys |
| Separate capture from acceptance: hook captures enter as low-trust candidates; promotion to curated knowledge needs a stated policy | K1, K6 | Hook capture is noisy and duplicative; explicit writes are high-signal but easily skipped; bad records propagate into later records | Who promotes, how often, and with what review burden |
| Treat everything an agent reads as untrusted input to memory | K1, K5, K6 | Poisoning succeeds at very low rates; injection through ordinary content, and reportedly through queries alone, is described | How much automatic promotion remains acceptable, especially for "lessons" and rules |
| Classify every relationship by origin: **derived** (parser/compiler), **extracted** (LLM) or **asserted** (agent/human), each with tool/model/author and source span | K2, K6 | In one 10-document study, frontier-model triple F1 from prose was about 22–40% (lower bounds), with 4.2% for a small local model; deterministic code relations are more reliable but can silently miss whole edge types | Whether extracted relations are retrievable by default or only after confirmation |
| Constrain relationship types to a closed vocabulary; quarantine out-of-vocabulary output | K2 | Free-text relations and co-occurrence links do not support reliable `uses`/`depends_on` traversal | Vocabulary maintenance as projects evolve |
| Resolve entities by exact identifiers before embedding similarity | K2, K4 | Dense retrieval underperforms on rare entities; embedding-based merging risks collapsing look-alike identifiers | Handling aliases and renamed components |
| Record world time and system time, with explicit supersession links instead of silent overwrites | K6, K7 | Destructive reconciliation erased needed information; invalidation preserves history | Every read must filter on validity, and "current" must be defined |
| Track support per fact as a list of sources; on source deletion, retract only unsupported facts and re-derive the rest | K6, K7 | Single-creator provenance caused over-deletion; documented deletion semantics differed from code; rebuilds after deletion were costly | Re-derivation cost and consistency during rebuild |
| Route retrieval by question type: lexical first for identifiers, semantic for concepts, traversal for relationships, then rerank and return sources | K4, K6 | No single pipeline wins; graph retrieval on every query hurts simple lookups; lexical search beat dense retrieval on rare named entities, which E2/E20 would test for code identifiers | Rule-based routing versus letting the agent choose tools |
| Always-fresh search (grep, live code structure) for code, or indexes tied to repository state | K4, K7 | Staleness is a reported operational cost of code embeddings, with no measured accuracy impact found; evidence on grep versus embeddings is mixed | Re-indexing cost versus semantic recall |
| Keep a parsed layer for citable anchors; optionally add page-image retrieval for visually rich documents | K3, K4, K6 | Page-image retrieval wins on visually rich benchmark pages but cites whole pages; one study found an OCR pipeline with a strong VLM generalized better to unseen and degraded documents | Second index storage and whether the corpus is visually rich |
| Record VLM output as interpretation with model, prompt and date, linked to the cropped original | K3, K6 | VLMs fail most on arrows, counts, spatial relations and precise values, which are the facts agents act on | When a human or a second method confirms an interpretation |
| Derive the project scope key from a stable identity and test collisions; enforce scope at the service, not only by caller filters | K5 | Reported isolation failures came from basenames, worktrees, missing remotes and caller-supplied filters | Whether clones and worktrees of one repository share knowledge |
| Use one owning process for writable embedded stores; give local HTTP services authentication | K5 | Embedded stores restrict concurrent writers; zero lock timeouts lost writes; local HTTP servers were exposed to DNS rebinding | Operational overhead of a daemon versus per-project processes |
| Budget memory injection: inject at session start and after compaction, re-inject only on change, disclose detail progressively | K1, K4 | Duplicate injection consumed large token volumes in reported cases | Risk of missing relevant memory mid-session |

These patterns do not resolve the architectural questions in [05](05-decisions-and-open-questions.md); several depend on answers only the user can give.

## Origin

Written for this repo by 280Zo. This document defines the investigation's conceptual vocabulary and proposed alternatives; project-specific implementation evidence belongs in 03.
