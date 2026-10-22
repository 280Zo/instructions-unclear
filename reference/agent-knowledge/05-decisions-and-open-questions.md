# 05 Decisions and Open Questions

[Index](README.md) · [Objectives](01-objectives-and-requirements.md) · [Architecture](02-architecture-and-concepts.md) · [Technologies](03-technology-landscape.md) · [Evaluation](04-evaluation-and-experiments.md)

## Confirmed investigation decisions

| ID | Decision | Basis and consequence |
|---|---|---|
| D1 | Investigate persistent project knowledge for agents, not transcript storage alone | User's stated purpose: accurate reuse across sessions with structured relationships, sources and retrieval |
| D2 | Understand existing implemented capabilities before assembling/selecting a stack | Compare complete memory applications as well as storage, ingestion and processing components; do not assume custom development is needed |
| D3 | Keep objectives, concepts, technology findings, experiments and decisions separate | The five-document structure makes requirements primary and prevents findings from silently becoming decisions |
| D4 | No replacement stack is selected | PMB/Docling are the existing baseline. The storage layout is decided separately in D11; the products that implement it are not |
| D5 | Source-available/GitHub-available projects are eligible regardless of OSI license status | License, paid-edition and model terms remain practical information, not automatic exclusions |
| D6 | Exclude archived Kuzu from active candidates; consider LadybugDB independently | User's explicit maintenance criterion; do not combine fork/upstream stars or assume identical current behavior |
| D7 | Preserve originals and distinguish evidence from interpretation | Summaries, captions and extracted facts must not silently become the only retained source or be treated as confirmed truth |
| D8 | Popularity is a discovery signal, not an architectural-fit decision | Fit depends on the complete behavior in 01 and evidence from 04 |
| D9 | The system accepts every source type: code, documents, datasheets, schematics, photographs, binaries and session history | User decision, October 16, 2026. Originals stay files; representations are added per type ([02](02-architecture-and-concepts.md#data-types-and-what-they-need-from-storage)) |
| D10 | Capture, trust and consolidation are fully AI-managed, with no manual review queue, in the manner of PMB | User decision, October 16, 2026. The system must therefore make trust decisions automatically and safely (see the trust policy below) |
| D11 | Projects are separated by namespace in one central database; separate databases are not needed | User decision, October 16, 2026, accepting P1 below. The main risk is accidental mixing by one user |
| D12 | Fully transparent operation: no logins, no prompts, no storage decisions by the user or the model | User decision, October 16, 2026, matching PMB. The project is detected automatically from the session's folder; cross-project search is a separate tool and its reads are logged ([02](02-architecture-and-concepts.md#keeping-projects-apart-with-no-setup)). Per-namespace logins and sandboxing are rejected |

### Proposed, awaiting user confirmation

"P1" and "P2" are short names for two proposals. P1 is about where knowledge is stored; P2 is about how the AI decides what to trust.

**P1 Where knowledge is stored: one central database with a namespace per project, each holding a records table and a knowledge table.** This is the user's proposal, option 3 in [02](02-architecture-and-concepts.md#where-knowledge-is-stored-options-compared). Consistent with the research and nothing found rules it out; untested here. **Accepted by the user as D11 on October 16, 2026.**

Why it fits:

- It is a standard database tenancy model ("bridge"), between shared tables and a database per project.
- A forgotten row filter cannot mix projects, because each project's tables are separate objects. Choosing the wrong namespace still can, hence the session-binding condition below. The documented leaks were in shared-table designs and filter-based memory products.
- One database to run and back up; deleting a project drops its namespace; searching across projects stays easy.
- 5–50 namespaces is small: SurrealDB documents no fixed limit, and Postgres has no hard schema limit.

Conditions it depends on:

- **A store with real namespaces.** SurrealDB, ArangoDB, Chroma, Postgres and LanceDB have them; SQLite does not.
- **One process owns writes,** so several sessions and subagents do not hit lock errors.
- **The namespace comes from the session, not the model.** Cross-project search is a separate, explicit action.
- **A stable project ID.** Suggested: an ID generated once and stored in the Git common directory, checked against known paths. OpenCode's own project ID gives separate clones the same ID; whether clones should share is open question 13.
- **Deleted projects are listed, not silently removed,** because unmounted drives look like deleted folders.

Alternative considered: option 4, a separate database file per project, for strict separation such as client work. The user judged namespaces sufficient.

**P2 How the AI decides what to trust.** Implements D10. Proposed defaults, not yet confirmed:

- Each project namespace keeps two layers, as the user suggested:
  - **Records:** everything captured, kept as it was seen (conversation turns, tool results, document extracts), with its source. Records are never edited, only deleted.
  - **Knowledge:** facts, decisions, relationships and rules the agents act on. Each item links to the records that support it.
- Keeping both means a wrong fact can be traced to where it came from and corrected; knowledge can be rebuilt from records; deleting a source record removes the knowledge it alone supported. This follows the research finding that keeping originals and indexing them by extracted facts works better than either alone (03, K1).
- Every stored item records its origin: user statement, user correction, agent observation of the repository, external content read by the agent, or model inference or extraction.
- Only user statements and corrections become behavior-changing rules or lessons automatically. External content is stored as knowledge with its origin, never as a rule. This is how PMB treats lessons from corrections, and it is the main defence against memory poisoning.
- LLM-extracted relationships are searchable immediately, labelled "extracted" with confidence. When they conflict with code-derived or user-stated relationships, the latter win.
- Repetition across independent sources, and later task outcomes, raise or lower an item's standing automatically.

These are user-directed investigation constraints and goals, not authorization to install, migrate, expose services, change live settings or select a product.

## Current baseline, not an endorsement

The repository contains PMB and Docling MCP definitions and a codebase-memory integration. Source inspection has identified capabilities and gaps, but installed-version parity, enabled capture/model paths and complete-system behavior remain unverified. Presence in configuration is not proof that a feature is active or dependable.

No candidate has passed a product pilot here. Static findings in [03](03-technology-landscape.md) must not be promoted to runtime guarantees.

## Active hypotheses to test

| ID | Hypothesis, not a decision | Evidence that could support or reject it |
|---|---|---|
| H1 | An existing memory application could supply most capture/maintenance/integration needs | End-to-end E1/E9/E10 results plus a gap map against K1–K7 |
| H2 | A temporal/corpus framework could improve typed relationships and source-supported retrieval | E4/E5/E8 results, with integration effort and extraction errors recorded |
| H3 | A composed arrangement could reuse current tools while adding missing knowledge capabilities | Equivalent fixture results, cross-component provenance/lifecycle tests and operational cost |
| H4 | A central service outside checkouts could simplify sharing without unacceptable scope/lifecycle risks | E10/E11/E12 results against the chosen threat model and retention policy |
| H5 | Per-project or centrally managed separate stores could give a better isolation/operational fit | The same tests and recovery/backup burden, rather than assuming physical separation is always better |
| H6 | Some useful capture/retrieval can avoid a second generative API while retaining adequate quality | Measured behavior of deterministic, session-model and local-small-model routes; token/compute costs kept distinct |
| H7 | For coding knowledge, agentic search over well-organized plain files and live code may match a dedicated memory store on many question types | E20 with the plain-files-plus-grep baseline; evidence so far is mixed and harness-dependent |
| H8 | Typed relationships for code are best derived deterministically, while relationships from prose need either confirmation or a lower trust level | E16/E17; one 10-document study reported frontier-model triple F1 of about 22–40% (lower bounds), and parser-derived edges have known coverage gaps |
| H9 | Page-image retrieval adds useful recall over parsed text only if the corpus is visually rich (schematics, datasheets, photographs) | E7 and a page-image versus parsed-text comparison on the user's own documents |
| H10 | OpenCode V2 hooks can support automatic capture and context injection in the current build | **Supported by E13 on v2.0.29:** hooks fired in parent and subagent sessions and injected context reached the model. Delivery after compaction remains unconfirmed |

## Open questions that affect architecture

1. **Knowledge boundary:** which records are project-only, which are shared reference knowledge, and which may be intentionally searched across projects?
2. **Capture and trust:** what should be captured automatically, what needs confirmation, what should never be retained, and how are contradictions or inferred relationships represented?
3. **Media behavior:** which photo/diagram tasks matter, and is direct image-vector similarity mandatory or optional alongside textual interpretation?
4. **Isolation:** answered by D11 and D12: the goal is preventing accidental mixing, with no logins or sandboxing.
5. **Processing:** what content may leave the machine, and which additional local models, API processing, downloads and costs are acceptable?
6. **Retrieval contract:** what exact-match, relationship, citation and abstention behavior is required, with what thresholds and visibility delay?
7. **Lifecycle:** what persists after checkout deletion, who can retire a source/scope, and how do backups, exports and rebuilds follow that policy?
8. **Operation:** what installation/runtime complexity, latency, resource consumption, maintenance and multi-client load are acceptable?
9. **Integration:** can each proposed arrangement capture and retrieve correctly for actual OpenCode sessions and subagents, rather than only expose generic MCP tools?
10. **Corpus:** which source material will the system actually hold (code, design documents, datasheets, schematics, photographs, session history), in what volume, and how visually rich is it? This determines whether H9 matters at all.
11. **Trust promotion:** which captured items may become curated knowledge or "lessons" automatically, and should content from outside the repository ever be promoted without review?
12. **Relationship trust:** should LLM-extracted relationships be retrievable by default, labelled as unconfirmed, or withheld until confirmed?
13. **Project identity:** should clones and worktrees of one repository share knowledge, and should a monorepo subfolder be its own scope?

Questions 1–8 and 10–13 depend on the user's needs, preferences and risk tolerance; research can inform them but not answer them. Question 9 is answerable by experiment (E13 and later integration tests).

Status after the user's October 16 answers: question 10 is answered by D9; questions 2, 11 and 12 by D10, with P2 proposing how; questions 1, 4, 7 and 13 are partly addressed by P1, which does not decide a shared corpus, the threat model or whether clones share. E13 answered the hook-delivery part of question 9. Research findings relevant to each are in [03](03-technology-landscape.md#findings-by-objective) and the candidate patterns in [02](02-architecture-and-concepts.md#patterns-the-evidence-supports-evaluating).

Do not silently resolve these by selecting a candidate's defaults. Unknown answers are legitimate research inputs.

## Not selected or not established

- A single multi-model database versus coordinated stores.
- Whether a shared reference corpus is needed (the storage layout itself is decided in D11).
- A particular memory application, graph engine, parser, embedding model, VLM or capture plugin.
- Mandatory zero-cloud operation, zero additional inference, image-vector retrieval, automatic capture of every event, or a specific performance SLA.
- A claim that PMB plus Docling is preferred, or that any more popular alternative is superior.

No general architecture has been rejected solely for failing to match the current setup. The archived Kuzu and Mem0 MCP repositories are not active deployment candidates in the current landscape; excluding those repositories does not reject LadybugDB or Mem0 itself. Deprecated Supermemory MCP v1 is distinguished from its current integration path.

## Recording future decisions

Add a decision only after explicit agreement. Record its date, scope, alternatives considered, objective/test IDs, supporting evidence, trade-offs, uncertainty and revisit condition. A proposed experiment is not a decision; a vendor claim is not a successful experiment; a successful small test is not a production guarantee.

Status reviewed: October 16, 2026, after the first objective-by-objective research pass. E13 ran the same day; the storage layout (D11) and transparency (D12) were decided.

## Investigation steps

1. Simplify requirements: transparent, automatic project detection, namespace per project. Done (D11, D12).
2. Compare candidate products against those requirements. Done ([03](03-technology-landscape.md#candidates-checked-against-the-decided-requirements)):
   - Closest memory layers: Hindsight (meets every requirement on paper; capture can run without an LLM in `chunks` mode, or keep original text with LLM metadata in `verbatim` mode), Cognee (embedded, runs without an LLM, OpenCode plugin; its embedded graph allows one writer) and agentmemory (built for coding agents; weak on documents and images). Mem0's open-source version lost its graph and its OpenCode plugin needs a cloud key; Graphiti needs manual capture and an LLM for every ingest.
   - Closest stores: LanceDB (embedded, built-in hybrid search, compressed disk indexes, page-image support; no graph), SurrealDB (native namespaces, graph and hybrid search in one engine; BSL licence; one process when embedded) and Qdrant (strongest vector features; a server; no graph). RuVector is experimental.
   - Most single users run one local process over SQLite or LanceDB with small local embeddings, which is how PMB already works.
3. Retrieval: local embedding models, combining keyword, vector and relationship search, reranking. Done ([03](03-technology-landscape.md#retrieval-embedding-models-and-search-methods), candidate pipeline in [02](02-architecture-and-concepts.md#candidate-search-pipeline-to-test)). Target hardware: AMD Ryzen 7 7800X3D (8 cores), 62 GB RAM, NVIDIA RTX 4070 Ti SUPER 16 GB.
   - Current memory products default to small embedding models not trained on code; Qwen3-Embedding-0.6B (GPU) or Granite R2 / gte-modernbert (CPU) are stronger and Apache-licensed.
   - Keyword search for code needs identifier-aware indexing; weighted fusion beat RRF once tuned; code-capable rerankers (Qwen3, jina-v3) far outscore bge-reranker-v2-m3 on code; exact matches should bypass the reranker.
   - Relationship expansion helps only relationship questions, so it should be routed, not always on.
4. Documents and images: how Docling output and photographs become records and knowledge. Done ([03](03-technology-landscape.md#documents-and-images-ingestion-on-the-target-hardware), candidate pipeline in [02](02-architecture-and-concepts.md#candidate-ingestion-pipeline-for-documents-and-images), tests E21–E27 in 04).
   - Docling keeps page and location for every chunk, but has known problems with tables split across pages, merged cells and whole-page drawings, and extracts no schematic connections.
   - The memory products checked discard Docling's provenance, so keeping it needs a small ingestion step of our own whichever product is chosen.
   - Vision models misread text; an OCR engine should be the source for exact strings, with the vision model cross-checked against it.
   - A page-image index is optional, to be added only if tests show text search misses figure and diagram questions.
5. Test the top one or two candidates on a small fixture of the user's data (04). In progress: user-approved temporary provisioning, synthetic projects, whole-image comprehension fixture and a supplied PDF; results are recorded in [04](04-evaluation-and-experiments.md#initial-local-pilot-october-16-2026).
   - First comparison, 21 questions: keyword baseline 17, PMB 17, Hindsight 14 (4B extraction model). The shared failures came from document extraction errors, three of which a page-image vision check fixed.
   - Transparent images must be flattened onto white before a vision model sees them.
   - Per-session PMB MCP servers each load their own embedding model on the GPU (7 copies, 5.1 GB).
   - Second run with vision transcriptions added next to Docling text: keyword baseline 19, PMB 18, Hindsight 15 (gemma3:12b extraction, 25 min loading). Transcriptions fixed the table errors but introduced their own (V_HH for V_IH); the remaining failures are reader-model limits.
   - Each OpenCode session's PMB server cannot be told apart from the others; stopping idle copies removed this session's PMB tools until OpenCode restarted them.
   - A bigger answering model (gemma3:12b) did not help: it refused more often with evidence present. Remaining failures depend on how evidence is presented and on instruction wording.
   - Hindsight with Claude Sonnet 4.5 through a subscription login (no API key) scored 10/21: it stored 48 facts against the local model's 316 and dropped most table values. Fact-extraction-only storage is unsuitable for exact reference material.
   - Answering instructions matter as much as intake: a "rules" prompt (exact values, report conflicts, same component only, refuse only when nothing is relevant) raised the 4B model to 20/21 with keyword search and 19/21 with PMB. No setup reported the datasheet's 10 ms / 10 µs conflict, so conflicts need their own stored record.
   - Methodology correction (user, October 17, 2026): the comparisons mixed layers. Keyword search and PMB were given raw text, while Hindsight had its "concise" curation step in the loop. Future tests measure intake, curation, storage and retrieval, and answering separately.
   - Documentation audit (October 17, 2026): the pilots tested Hindsight with settings its own docs advise against for document lookup (concise mode, no mission, no `include.chunks`), and on a workload its vendor assigns to RAG. Hindsight's document-lookup results are therefore not a fair verdict. Corrected re-tests: Hindsight `chunks`/`verbatim` with chunks returned; PMB through `pmb index pdf`; image description with a figure-specific prompt; session-memory capture tested on its intended workload (this session's transcript).
   - **Decision (user, October 17, 2026): the model running the session interprets images.** A hosted frontier model by default; switch the session to a local model when privacy requires it. Basis: in a blind-scored image-intake test, the session model (Claude Opus 5.5) scored 16/16 on the whole-image description, while Docling with three local vision models and Qwen3-VL 4B directly scored 1–5/16 with 5–16 false claims each.
   - Small runs only; no product is selected.
6. Decide.

## Origin

Written for this repo by 280Zo.
