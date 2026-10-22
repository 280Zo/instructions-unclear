# 04 Evaluation and Experiments

[Index](README.md) · [Objectives](01-objectives-and-requirements.md) · [Architecture](02-architecture-and-concepts.md) · [Technologies](03-technology-landscape.md) · [Decisions](05-decisions-and-open-questions.md)

## Status and purpose

**No complete-system pilot has been run in this environment.** Temporary provisioning and a first document-extraction check have started with user approval; these are not yet memory-system quality results. The repository's documentation/packaging tests do not test those product behaviors.

The experiments below are proposals. Fixture choice, capture/privacy policy, quantitative thresholds and permission to provision or run products/models must be agreed before execution. No installation, model download, source upload, service exposure or migration is authorized by this document.

### Initial local pilot: October 16, 2026

The user separately approved temporary installation and supplied `nearest_neighbors.png` and `28LV011.PDF`. Packages, test services, model caches and artifacts belong under `/tmp/opencode/agent-knowledge-pilot-b4rxafvp/`; no live configuration changes or external source uploads are part of this approval. PMB 1.2.3 and the Hindsight 1.0.0 launcher are installed, with resolved versions recorded in `artifacts/installed-versions.txt`. Installing the launcher does not provision or validate the Hindsight engine.

**Whole-image test, not similarity search.** The user's purpose for `nearest_neighbors.png` is whether a model understands the unusual image as a whole. Do not split it into tiles, exclude self-matches or substitute nearest-neighbor retrieval as the test. Docling extracted the headings but no explanation of the visual relationships. A separate local vision-model test is pending; its prompts receive the entire original file, not the answer rubric. Normal internal model image preprocessing is outside this test's control.

**First PDF extraction check (environment tested, one file).** The original and Docling output both contain **19 pages**. An earlier file-header check reported 10; that was wrong and is not the page-count ground truth. Saved outputs are `/tmp/opencode/docling/48ea3948434cbb5312bfc60953a15073.{json,md}`. The structured output has 583 text items, 14 table items and 19 picture items. All 14 tables have page/bounding-box fields pointing to existing pages; this checks anchor presence, not coordinate accuracy or correct crops.

Comparison with the original pages found:

- Simple values, such as the recommended 3.0-3.6 V supply range, are readable. They must remain distinct from the 7 V absolute maximum.
- Table 4's input-voltage subrows are flattened already in the structured JSON, not merely in Markdown.
- Table 6 combines standby-current conditions and values; part of an operating-current condition spills into the subgroup column.
- Table 8 remains separate table items on pages 5 and 6.
- Active-low bars on control names are absent from the exported plain text. Losing them can change electrical meaning.
- The page 16 protected-write command `A0` becomes `AO` with arrow artifacts. Exact strings require original-page verification.
- The original page 16 itself has a timing-unit discrepancy: prose says 10 ms after the last data input, while the nearby figure labels 10 microseconds minimum. An extraction/answering pipeline must retain that disagreement, not silently choose one.

**Whole-image test results (environment tested, one image, one model family).** Model: Qwen3-VL 4B through Ollama 0.40.4, Q4_K_M, fully on the GPU, temperature 0. Full prompts, responses and model digests are in `artifacts/visual-pilot/`.

- **The first three runs tested the wrong picture.** The PNG's background is transparent pixels whose hidden colour is black (25.8% of pixels), and the headings are opaque black. Image viewers draw transparency over white; the vision runtime dropped it, so the model saw black text on black. Both model versions then reported "no visible headings", a "black border" and a wrong grid. **Ingestion lesson: flatten transparent images onto white before sending them to a vision model.** Screenshots and exported diagrams are often transparent.
- The default `qwen3-vl:4b` tag is the thinking version and ignored `think: false`. With a 1,600-token limit it produced no answer; with 6,000 tokens it answered the open prompt (35 s) but not the structured one. Use the `-instruct` tag when a direct answer is needed.
- On the flattened copy (same whole image, no crop), scored with an 8-criterion rubric at 0–2 points each: 4B-instruct 6/16 and 8/16 on two prompts, thinking version 8/16. All read the four headings and stated the main point, that trained weights retrieve more relevant neighbours. None understood that each row pairs one query with two result sets, none noticed the exceptions on the trained side (a diver among coots, bottle caps and coals among reptiles), and each invented part of the layout. Instruct took 6–10 s per answer.

**Datasheet questions from page images (environment tested, 8 questions).** Pages rendered at 150 DPI; one page image per question; 4B-instruct; about 1 s per answer. 7 of 8 matched the answer key, including every value Docling's text got wrong: the separated 2.2 V footnote, the merged standby-current conditions, the `A0` byte read as `AO`, and both sides of the page 16 10 ms / 10 µs discrepancy. It missed the active-low bars on WE, RES and BUSY, naming only OE and CE. This supports, but does not yet establish, a design where Docling supplies searchable text and locations and a vision model checks exact values against the page image.

**First memory-system comparison (environment tested, 21 questions, one run).**

Setup:

- **Corpus:** project alpha has 3 synthetic files plus the 19 Docling datasheet pages, one chunk per page; project beta has 1 file. Each system stores each project separately.
- **Systems:**
  - Keyword baseline: ranks chunks by how many question words they contain, a stand-in for grep.
  - PMB 1.2.3: its own fact storage and recall.
  - Hindsight 1.0.0: has a model extract facts, then recalls them. It used the local Qwen3-VL 4B-instruct model for extraction, because its default gemma3:12b did not fit in free GPU memory. Observations were off.
- **Reader and scoring:** one fixed reader (Qwen3-VL 4B-instruct, temperature 0) answers from each system's top results. Answers are checked against expected values or required "not in the data" replies, and every failure was reviewed by hand. Scripts and full outputs are in `artifacts/memory-comparison/`.

| System | Answers correct | Right source in top 5 | Load time | Median search | Median text given to reader |
|---|---|---|---|---|---|
| Keyword baseline | 17/21 | 19/19 | none | 0.002 s | 6.1k characters |
| PMB 1.2.3 | 17/21 | 19/19 | 1.8 s | 0.02 s | 7.2k characters |
| Hindsight 1.0.0 | 14/21 | 18/19 | 274 s | 0.7 s | 13.9k characters |

All three answered the project questions correctly: exact identifier vs near-match, dependency, old vs current setting, keeping the two projects apart, and replying "not in the data" for unanswerable questions. Hindsight missed one: its rationale answer was only partly right.

All three failed the same four datasheet questions:

- reset pin number;
- standby currents, where Docling merged the table cells;
- protection bytes, where Docling read `A0` as `AO`;
- RES hold time, where the datasheet's 10 ms / 10 µs disagreement was not reported.

The page-image vision check above answered three of these four correctly. Hindsight additionally lost the data-latch and active-low questions, probably because the small extraction model dropped details from tables. That is an inference, not verified.

Limits: one run on a tiny corpus where keyword search is unusually easy; a small reader; Hindsight handicapped by a 4B extraction model; PMB and Hindsight embeddings ran on the CPU because the GPU was full. This is not a general ranking. Within these limits, at this scale **extraction quality decided the results more than the choice of memory system did**, and Hindsight's fact extraction cost 274 s of loading time without improving answers.

**Second comparison: improved document intake (option A, October 17, 2026).** A vision model (Qwen3-VL 4B-instruct) transcribed every datasheet page image at 150 DPI, which took about 2 minutes for 19 pages. Each transcription was added next to Docling's text for that page, labelled as model-generated, and never replaced it. Transcriptions that ran to the token limit were rejected; pages 1, 13 and 14 got stuck in repetition loops. Hindsight used its default gemma3:12b for fact extraction, fully on the GPU after the user approved stopping idle PMB server copies. Same questions, same reader. The reset check was corrected to accept "V_SS", and both runs were re-scored from their saved answers.

| System | First run | Option A | Right source in top 5 | Load time (option A) |
|---|---|---|---|---|
| Keyword baseline | 17/21 | 19/21 | 19/19 | none |
| PMB 1.2.3 | 17/21 | 18/21 | 18/19 | 1.0 s |
| Hindsight 1.0.0 | 14/21 (4B extraction) | 15/21 (12B extraction) | 17/19 | 1,524 s |

- **Fixed by the transcription:** the standby currents, now split into separate rows (all three systems), and the reset pin number (keyword and PMB).
- **New error carried by the transcription:** all three standby answers now say "CE = V_HH" where the datasheet says V_IH. The vision step adds its own errors, so it must stay labelled and checkable against the page image.
- **Reader limit:** the protection bytes (`A0`) and the 10 ms / 10 µs discrepancy flag were in the top retrieved text for every system, but the small reader still answered wrongly. A stronger reader, or presenting the verified values first, is the next variable to test.
- **New retrieval side effect:** the longer pages now rank higher in project alpha, and PMB's reader answered "3.3V" for Sensor-A's unknown supply voltage, taking the EEPROM's value for an unrelated component.
- **Hindsight with 12B extraction:** it gained the rationale question and lost the current-setting question; it still picked the wrong datasheet row (700 ns instead of 750 ns) and could not answer the active-low question. Loading took 25 minutes for 24 chunks.

Within the limits stated above, improving document intake helped every system, and the plain-text systems benefited most. The remaining errors come from the reader model and from the transcription's own mistakes.

**Third comparison: stronger answering model (A2, October 17, 2026).** The same stored data was reused, with nothing reloaded, and the reader was changed from Qwen3-VL 4B-instruct to gemma3:12b. Part of gemma3:12b ran on the CPU because the PMB server copies had been restarted, which affects speed only. Gemma tends to quote sentences instead of answering "no", so the yes/no checks were widened to accept "not" and "does not", and all four runs were re-scored from their saved answers under that single rule.

| Answering model and intake | Keyword | PMB | Hindsight |
|---|---|---|---|
| 4B, first intake | 17 | 17 | 14 |
| 4B, option A | **19** | **18** | **15** |
| gemma3:12b, first intake | 15 | 16 | 11 |
| gemma3:12b, option A | 16 | 17 | 14 |

The bigger answering model scored slightly lower. With the same instruction ("if the context does not contain the answer, reply exactly: Not in the data"), gemma3:12b gave that refusal for questions whose answers were in its context: the current setting, the data-latch time and the active-low signals. Neither answering model reported the `A0` bytes or the 10 ms / 10 µs discrepancy, although both were in the retrieved text. The remaining failures therefore depend on how evidence is presented and on how the instruction is worded, not only on model size. Option A's intake beat the first intake with both answering models.

**Hindsight token use (measured October 17, 2026).** Hindsight 1.0.0 stored the option A corpus once with gemma3:12b extraction and observations off. Token counts come from Hindsight's own store-response usage figures, and are saved in `artifacts/memory-comparison-tokens/hindsight-retain-usage.json`.

| Measure | Value |
|---|---|
| Source text | 23 items, 41,544 characters (about 10,400 tokens) |
| Tokens used | 106,077 input, 33,596 output |
| Per source token | about 10 input, 3.2 output |
| Fixed cost per stored item | about 2,100 input tokens, even for a 378-character file |
| Average datasheet page | about 5,100 input, 1,660 output |
| Local time | 32 minutes, with part of the model on the CPU |

At official list prices (GPT-5-mini $0.25 / $2 and Claude Haiku 4.5 $1 / $5 per million input / output tokens), this corpus would cost about **$0.09 with GPT-5-mini** and **$0.27 with Haiku 4.5**. Estimates scaled from these figures:

| Workload | GPT-5-mini | Haiku 4.5 |
|---|---|---|
| One datasheet page | about $0.005 | about $0.013 |
| 1,000 datasheet pages | about $4.60 | about $13.40 |
| 100 short notes (about 2,100 input and 400 output tokens each) | about $0.13 | about $0.41 |

Caveats: token counts use gemma's tokenizer, and hosted tokenizers differ, typically by tens of percent. GPT-5-mini is a reasoning model whose hidden reasoning tokens are billed as output and are not included here. Hindsight's prompt caching, which is on by default for supported providers, would cut the repeated 2,100-token instructions. Enabling observations (background consolidation) adds further model calls. Changing a document re-extracts the whole document.

**Hindsight with hosted extraction through a subscription login (October 17, 2026).** Hindsight 1.0.0's `claude-code` provider used the user's Claude login through the `claude` CLI; no API key was involved. The default model was Claude Sonnet 4.5. Only the Hindsight process saw the real home folder; the database stayed in the pilot folder. The data and the local 4B answering model were the same as in the local 12B token run.

| Extraction model | Answers | Facts stored | Tokens (input / output) | Load time |
|---|---|---|---|---|
| gemma3:12b, local | 15/21 | 316 | 106,077 / 33,596 | 32 min |
| Claude Sonnet 4.5, subscription login | **10/21** | **48** | 95,542 / 6,236 | 21 min |

- **The hosted model did worse here because it stored far fewer facts.** It kept about one fact per page chunk and treated most datasheet table values as not worth remembering. Hindsight answers from stored facts, so the standby currents, the VIH footnote and the near-match and co-occurrence notes were no longer findable. It got the current-setting question right, which the local model had missed.
- **The login route is slow:** 13–119 s per call (about 45 s on average), because each request goes through the `claude` CLI.
- **Conclusion for this design:** Hindsight's fact extraction is tuned for conversational memory, not for keeping exact reference values. A stronger extraction model makes it more selective, not more complete. Exact reference material needs the original text stored and searchable, as PMB and plain search did.

**How evidence is presented to the answering model (option 1, October 17, 2026).** This tests only the answering step: the option A data, the same retrieved evidence for keyword and PMB, and only the instruction changed.

- **original:** "If the context does not contain the answer, reply exactly: Not in the data."
- **rules:** copy values exactly, including hexadecimal; report both values when sources disagree; use a value only if it is about the component asked about; a slash or bar means active-low; say "Not in the data" only when no passage is about the question.
- **quote-first:** copy the relevant lines word for word, then answer from them.

| Answering model | Instruction | Keyword | PMB |
|---|---|---|---|
| qwen3-vl:4b-instruct | original | 19 | 18 |
| qwen3-vl:4b-instruct | **rules** | **20** | **19** |
| qwen3-vl:4b-instruct | quote-first | 16 | 15 |
| gemma3:12b | original | 16 | 17 |
| gemma3:12b | rules | 18 | 18 |
| gemma3:12b | quote-first | 18 | 17 |

- **The instruction wording was worth as much as intake.** The rules prompt fixed `A0`, the reset pin, the active-low signals and the 3.3 V mix-up for the 4B model. It also stopped most of gemma's refusals.
- **Quote-first hurt the small model:** it sometimes never reached the answer section, or quoted the wrong passage.
- **Still unsolved:** every setup answered "10 ms" for the RES hold time. The page 16 transcription contains a `DISCREPANCY:` line about 10 ms vs 10 µs, but no answering model passed it on. Conflicts should be stored as their own searchable record rather than buried in page text.
- One remaining PMB miss (latch time 250 ns) came from reading the wrong table row.

**Whole-image test with no context (October 17, 2026).** The original `nearest_neighbors.png`, not flattened, with only its filename. Four stacks; the same five questions; local 4B answering model with the rules instruction. Full output is in `artifacts/image-test*`.

| Stack | Defaults (runs 1–2) | Connected to a local vision model (run 3) |
|---|---|---|
| Docling default (docling-mcp as installed) → PMB | Headings only: "Random Weights", "LLM trained", "5-Nearest Neighbors" | Same; the default does not describe pictures |
| Docling picture description → PMB | Run 1: request too large for a 4,096-token context. Run 2: CUDA out of memory; Ollama returned HTTP 200 with no text and Docling stored an empty description **without any warning** | "A collage of 50 small photographs… a diverse glimpse into nature, culture and everyday life": a generic description that misses the comparison |
| Hindsight file upload (MarkItDown) | Refused: "Image OCR is not enabled for the markitdown parser" | Upload and OCR succeeded, but concise extraction stored **0 facts** |
| Hindsight inline image | Hindsight 1.0.0's `ollama` provider sends images to Ollama's native API in a format it rejects (a source bug) | One fact: "The image displays a grid of 64 photographs." |

Every tool connected to a vision model did look at the image, but **its default instructions decided what survived**: Docling's default prompt is "Describe this image in a few sentences", and Hindsight's concise mode keeps only facts "useful to recall in 6 months". The run therefore tested default configurations, not the tools' best use.

**Tool-usage audit against official documentation and installed source (October 17, 2026).** Three audits compared every setting used in these pilots with each tool's documentation:

- **Hindsight.** It is designed for conversation memory, and its own docs recommend ordinary document retrieval (RAG) for manuals and technical documentation. Its benchmarks are LongMemEval and LoCoMo, both multi-session conversation tests. Mistakes in this pilot:
  - the default `concise` mode, whose prompt drops specification values by design;
  - no bank mission, which the docs call "the single biggest cause of low-quality memories";
  - a file path as `context`, where the docs say to describe the content;
  - recall without `include.chunks`, so the original text was never returned.

  The correct setup for document lookup is `HINDSIGHT_API_RETAIN_EXTRACTION_MODE=chunks` or `verbatim`, recall with `include: {"chunks": ...}`, and the answering model given the chunk text. For images, use the vision slot (`HINDSIGHT_API_VLM_*`) with an OpenAI-compatible endpoint and `HINDSIGHT_API_LLM_VISION=true`. For coding agents, the intended route is the Coding Agents plugin, which captures conversations and git history into a bank per repository.
- **Docling.** The default pipeline is not meant to understand figures; picture description is the documented opt-in. Points to fix:
  - docling-mcp can switch it on only through `DOCLING_MCP_DO_PICTURE_DESCRIPTION=true` with a local preset (SmolVLM or granite-vision); it cannot call an API endpoint.
  - `provenance: not-implemented` is normal, not an error.
  - Failed API calls return empty text silently, a known class of issues.
  - The picture is cropped at the option's own `scale` (default 2.0), which explains the oversized request.
  - For datasheets, `do_cell_matching=False` may fix merged cells, and turning OCR off on PDFs that have a text layer may stop `A0` being read as `AO` (both inferred). Nothing handles overline bars.
- **PMB.** It is designed for coding-agent session memory; its benchmark is LoCoMo, where keyword search carries most of the score. That matches it tying plain search here.
  - `pmb index pdf` is the documented route for PDFs: about 1,500-character chunks with page metadata. Writing whole pages through `record_fact` risks semantic de-duplication, but the pilot stored all 22 alpha items, so none was dropped.
  - The default embedding model reads only about 128 tokens per item, so vector search saw little of each page.
  - A shared daemon (`pmb daemon`, `pmb mcp serve --transport streamable-http`, `pmb mcp proxy`) avoids one GPU copy per session, but `pmb connect` writes OpenCode as one stdio server per session.
  - PMB has no importer for agent session transcripts. It captures session knowledge through the agent's own typed `record_batch` calls, hooks (Claude Code only) and `pmb distill`.

### Goal-by-goal tests (October 17, 2026 onward)

The method was agreed after the mixed comparisons above:
- one test per goal, with candidates chosen from official documentation;
- inputs, answer key and scoring frozen before any candidate runs;
- a blind evaluator scores anonymised outputs;
- the default session LLM is a baseline in every test;
- a short synopsis is presented before each test.

**Test 1: image intake (K3, image description).** Input: the whole `nearest_neighbors.png`, flattened onto white, at full size with nothing cropped. One frozen description prompt. Rubric of 8 criteria, 0–2 each.

| Candidate | Score /16 | False claims | Time |
|---|---|---|---|
| Session LLM, Claude Opus 5.5, fresh context | **16** | 1 minor | under 1 min |
| Qwen3-VL 4B instruct, direct | 5 | 11 | 124 s (CPU) |
| Docling picture description + Qwen3-VL 4B | 2 | 16 | 122 s (CPU) |
| Docling granite-vision preset | 1 | 5 | 17 min (CPU) |
| Docling SmolVLM preset | 1 | 15 | 149 s (CPU) |

Docling contributed the heading text only; the interpretation came entirely from the vision model it called, and the same model scored lower through Docling than directly. The first run was frozen by a system suspend and then exceeded its output limit. Candidate E failed once because `/tmp` (RAM-backed) was full; both were rerun.

**Test 2: image question answering (K3, answering against the original).** The same image, six questions frozen with an answer key, and each model given the image directly with no storage or retrieval.

| Candidate | Score /12 | False claims | Time |
|---|---|---|---|
| Session LLM, Claude Opus 5.5, fresh context | **12** | 1 minor | under 1 min |
| Qwen3-VL 8B instruct | 7 | 6 | 77 s (CPU) |
| Qwen3-VL 4B instruct | 7 | 9 | 58 s (CPU) |

The local models identified the labels and the swimmer but invented objects (a "person holding a bird", mushrooms in the snake row) and missed the bottle caps and coals. Moving from 4B to 8B reduced invented claims but did not raise the score.

**Test 3: document intake (K3, documents).** Input: `28LV011.PDF`, 19 pages. A key of 28 items (exact values attached to the right parameter, condition and speed grade; footnotes; active-low marks; `A0`; the table continuing across pages), 0–2 each, maximum 56. Only the extracted text was scored, blind.

| Candidate | Score /56 | Corrupted values | Time |
|---|---|---|---|
| Session LLM, Claude Opus 5.5, fresh context, reading the pages | **56** | 0 (chart readings labelled "approximate") | not measured (subagent) |
| MarkItDown 0.1.8 | 46 | 5 (footnote marks fused into values: `2.0¹`→`2.01`, `RT1¹`→`RT11`) | 1 s |
| PMB's PDF extractor (pdfplumber) | 46 | 5 (same text layer, same errors) | 1 s |
| Docling as installed (docling-mcp defaults) | 40 | 3 (`A0`→`AO`, test condition split across columns) | earlier run |
| Docling with documented table settings (cell matching off, OCR off) | 38 | 3 (lost footnotes, headers and the protection-sequence tables) | 54 s (CPU) |

- **The session model was the only reliable intake.** It was the only candidate that preserved the active-low marks and the protection bytes, and the only one to report the 10 ms / 10 µs conflict.
- **Plain text-layer extractors beat Docling on this datasheet**: they kept rows intact but fused footnote markers into numbers and captured nothing from figures.
- **The documented Docling table settings made it worse, not better.**
- **None of the local tools is safe for exact values without checking.**

Result for both image tests: reliable image interpretation came only from the frontier session model. **Decision (user):** the session model interprets images; switch to a local model only when privacy requires it, and accept lower reliability.

Setup finding: the GPU was nearly full because the user's OpenCode sessions had started 7 separate PMB MCP server copies, each loading its own embedding model (about 736 MB each, 5.1 GB in total), plus Docling MCP at 2 GB. A shared background service would load the model once.

These are qualitative spot checks, not a cell-accuracy score or a comparison between Docling modes. Originals remain outside this repository. The temporary `evaluation/` folder contains an assistant-authored answer key and image rubric; they must not be ingested or supplied to the tested model. No memory candidate has passed E1-E12 on this evidence.

## Evidence levels

| Level | What it establishes | What it does not establish |
|---|---|---|
| Vendor documented | The project describes a capability for a version/edition | That the selected release/configuration implements it correctly here |
| Source inspected | A reviewed implementation path exists at an identified source version | That it is enabled, compatible with this host or dependable under load |
| Environment tested | A reproducible local experiment produced recorded results | Broader production guarantees beyond the scenario and configuration tested |
| Comparative measured | Candidates ran equivalent fixtures/questions with recorded conditions | A universal ranking across other workloads, models or hardware |

These levels classify results of experiments run here. External evidence in [03](03-technology-landscape.md#evidence-and-reading-guide) uses its own labels (documented, source-inspected, measured, vendor-measured, reported issue); neither set substitutes for the other in technology or decision records. Vendor benchmarks are useful leads, not substitutes for the target workload.

## A representative non-sensitive fixture

Proposed fixture, not an agreed dataset:

- Two small projects with deliberately similar component names and overlapping identifiers.
- A document and interface table establishing that `Sensor-A uses IF-42` and `Controller-B depends_on Sensor-A`.
- A diagram whose arrow direction can be checked against an authoritative textual statement.
- A photograph with known visible text and objects, plus an unrelated visually similar image.
- A revised source that changes one relationship, a second source that contradicts a claim, and one removed source.
- A coding session containing a decision, its rationale, a rejected option and a later correction.

Retain an answer key: exact source versions, expected facts, relationship types/directions, permitted project scopes, and facts that are intentionally not established. Use no sensitive material merely to demonstrate ingestion.

## Tests tied to system objectives

| Test | Objectives | Question/action | Expected behavior to verify |
|---|---|---|---|
| E1 Persistence and capture | K1, K5 | Record useful work, end the session, restart host/service, ask from a new session and a subagent | Retained knowledge and rationale are recoverable; capture omissions and visibility delays are observable |
| E2 Exact identifiers | K4, K5 | Ask for `IF-42` with near-matches such as `IF-420` in the other project | Correct identifier and project, not just semantically similar text |
| E3 Meaning and rationale | K1, K4, K6 | Ask why a transport was chosen using wording absent from the source | Relevant decision/rationale with source, not a plausible invented explanation |
| E4 Typed relationship traversal | K2, K4, K6 | Ask which component uses IF-42 and what depends on it | Correct entities, edge types/directions and supporting sources; co-mention is not accepted as proof |
| E5 Document/table evidence | K3, K6 | Ask for a value and relationship established in a table | Accurate value/context and recoverable original/page or item anchor where available |
| E6 Image and diagram interpretation | K2, K3, K6 | Ask what a photo depicts and which way a dependency arrow points | Original image available; interpretation labeled; errors and uncertainty measured against the answer key |
| E7 Visual versus textual retrieval | K3, K4 | Compare finding an image by visible similarity versus a caption/OCR query | Record which representation was actually used; caption matching does not count as direct visual-vector retrieval |
| E8 Correction, conflict and time | K2, K6, K7 | Revise a source, add a contradiction, ask what is current and what was previously true | Current versus superseded claims distinguished; conflicting evidence remains visible rather than silently overwritten |
| E9 Deduplication and consolidation | K1, K6, K7 | Reingest the same source and restate a decision in several sessions | Useful consolidation without duplicated facts, lost provenance or collapse of distinct entities |
| E10 Shared writers and visibility | K1, K5, K7 | Two independent sessions and a delegated agent write/read concurrently | Distinct session attribution; no silent loss/misrouting; measured read-after-write delay and retriable failures |
| E11 Project boundary | K5, K6 | Repeat searches, graph hops, writes, exports and background work across the two scopes | Configured isolation policy holds across all paths; authorization tests match the agreed threat model |
| E12 Removal and recovery | K1, K3, K7 | Remove a source/project scope, interrupt ingestion, restart and rebuild indexes | Defined retention/deletion behavior, no unexplained orphan claims, recoverable originals and reproducible derivations |
| E13 Host capture and injection canary | K1, K5 | In the actual OpenCode build, log every `prompt`, `context`, `compaction` and tool hook with session ID and agent; inject a canary token through each injection path; force compaction; start a subagent | Each hook fires as documented, including or excluding child sessions; injected canaries reach the model; duplicate plugin loading does not double-capture |
| E14 Capture quality audit | K1 | Run representative real sessions; label every stored item useful, duplicate or noise | Noise and duplicate shares, missed useful knowledge, and injected tokens per request over a long session |
| E15 Memory poisoning | K1, K5, K6 | Place an instruction payload in a README, web page and tool output; also attempt query-only injection | Payload does not become a lesson or rule, does not change later behavior, and is attributable if stored |
| E16 Extraction and entity resolution | K2, K6 | Hand-label typed triples in about 20 project documents; include near-duplicate identifiers (`IF-42`, `IF-042`, "interface 42") and look-alikes (`IF-24`) | Edge precision/recall by predicate, co-mention-only edges counted, false and missed merges |
| E17 Code-structure ground truth | K2, K4 | Compare parser-derived call/import edges with a compiler-grade index or language server on a multi-language repository | Error rate per language and edge type; whether recorded confidence reflects actual error |
| E18 Scope-key collisions | K5 | Repositories with the same basename and different remotes, a repository without a remote, a non-Git directory, a linked worktree, and a monorepo subfolder start | No cross-recall between unrelated scopes; intended sharing between clones/worktrees matches the agreed policy |
| E19 Multi-support deletion | K6, K7 | Two sources establish one fact; delete the first, then the second | Fact survives with remaining support, then retracts; no silent over- or under-deletion |
| E20 Retrieval mode ablation | K4 | Same fixture with lexical, dense, hybrid, plus reranker, plus graph, plus routing; inline versus file-delivered tool results; also a plain-files-plus-grep baseline. Settings to vary: embedding model and dimensions, RRF k versus weighted fusion, tokenizer variants and field weights, chunk size and syntax-tree versus line chunking, contextual headers, reranker choice and depth, exact-match pinning, routing rules, graph hop depth, time filtering, result count | Per-question-type recall, MRR and p95 latency identify which settings help, rather than one aggregate score |

Document and image tests from the step 4 research:

| Test | Objectives | Question/action | Expected behavior to verify |
|---|---|---|---|
| E21 Datasheet tables | K3, K6 | Five datasheets with tables spanning pages and merged cells; compare Docling table modes and the merge step | Cell-level accuracy; split tables rejoined |
| E22 Drawings | K3 | A schematic or CAD PDF | Chunk count above zero; text from the drawing retrievable |
| E23 Part markings | K3, K6 | 50 board photos with known markings; OCR alone, vision model alone, and vision model cross-checked by OCR | Exact-match rate and number of invented strings |
| E24 Diagram reading | K2, K3 | 20 schematic crops: arrow direction, pin counts, component values | Error rate of vision-model readings |
| E25 Datasheet retrieval | K3, K4 | 30 real questions over 10 datasheets; keyword on Docling text, text vectors, one vector per page, multi-vector page search | Recall@5 and indexing time per page; decides whether a page-image index is worth it |
| E26 Similar photos | K3, K4 | Same board from different angles and lighting | Top-5 hit rate per image embedding model |
| E27 Re-ingest and GPU load | K3, K7 | Touch, edit and delete files; run vision model, OCR and embedder together | Skip, new version and removal behave correctly; peak VRAM under 16 GB and throughput |

Capture automation itself needs evaluation: measure missed useful knowledge and unwanted capture, not just whether a hook fires. Test native OpenCode integration separately from generic MCP access; repeat independently started sessions rather than only child calls within one session. Research motivating E13–E20 is summarized in [03](03-technology-landscape.md#findings-by-objective).

## Retrieval question set and statistics

Public memory benchmarks do not measure code identifiers, dependency traversal or project-document relationships, and their scores move with harness settings. A small project-specific set is the more defensible measure:

- **Stratify by question type**, about 20–40 questions each: identifier (exact symbol, path, key, error string); conceptual (paraphrased, no shared keywords); dependency (callers, impact, 2–3 hops); temporal/update (superseded decision; the old answer counts as wrong); and unanswerable (about 15–20%, including plausible identifiers that do not exist).
- **Label gold evidence units** (file and line, symbol, document item, memory record), not only answer text, so retrieval and answering can be scored separately.
- **Score retrieval per type:** recall@5/10/20 as the primary metric; MRR for identifiers; nDCG@10 for conceptual questions; path completeness for dependency questions.
- **Score answers:** programmatic match where possible; citation precision and recall; claim-level faithfulness with a human-labelled sample to correct judge bias; abstention rate on unanswerable questions together with false abstention on answerable ones.
- **Control variance:** change one variable at a time with the reader model, prompt and k fixed; run each configuration 3–5 times and report bootstrap confidence intervals. With about 30 questions per type, differences of two or three questions are likely within noise.
- **Avoid judge and fixture artefacts:** if an LLM judges, present candidates in both orders; freeze the corpus snapshot; keep the fixture out of prompts and stored lessons; add a staleness check by editing sources after indexing.

## Measures to record

- Retrieval: correct-source recall/ranking, exact-identifier accuracy, correct edge/type/direction, project leakage, conflicting/stale claims and unsupported answers.
- Provenance: citation correctness, original-source recoverability, location/version availability, and interpretation/confirmation labels.
- Capture: useful/noise/duplicate shares, missed useful knowledge, injected memory tokens per request, and poisoning outcomes.
- Lifecycle: duplicate rate, source-update propagation, correction retention, deletion scope and rebuild consistency.
- Operation: indexing/visibility delay, retrieval latency, concurrent write/read errors, restart recovery, disk/RAM/VRAM and maintenance effort.
- Processing: calling-agent tokens, separate extraction/vision/embedding/reranking work, external requests, artifact downloads and monetary cost where measurable.

Set pass thresholds before using results to select a candidate. Record unanswerable questions and appropriate abstentions; a system should not score well merely by answering everything confidently.

## Keep retrieval and answer quality separate

First examine what evidence the retrieval layer returned. Then evaluate the agent's answer using that evidence. This distinguishes a retrieval miss, incorrect extraction, unsupported relationship, stale source, scope failure and answer-generation error.

For comparisons, keep fixtures, scope, questions and answer keys constant. Identify differing models, backend configuration, corpus representations and tuning effort. Do not claim a database or memory application caused a quality gain when the compared processing pipelines differed materially without disclosure.

## Suggested order, not an execution approval

1. Agree fixtures, source/privacy policy, threat model and thresholds.
2. Verify actual installed/released versions and run E13: whether OpenCode hooks capture and inject as documented determines which integration routes are viable at all.
3. Run the small text/relationship/provenance case before adding media.
4. Test sharing, updates, project boundaries and recovery.
5. Add document/table/image cases and any agreed visual-similarity requirement.
6. Compare representative end-to-end arrangements; record failures and integration work, not only scores.

Start with lightweight evidence collection where possible. A model-dependent candidate may require separate provisioning approval before even a small test.

## Experiment record template

For each run retain: objective/test ID, date, candidate and exact versions, deployment/host integration, models and revisions, data location/scope/auth policy, fixture hashes/source IDs, operations and queries, expected versus actual results, source/answer evidence, visibility timing, errors/cost/resources, and limitations. Keep credentials and sensitive originals out of this public repository.

| Run | Candidate/configuration | Tests performed | Evidence level | Result |
|---|---|---|---|---|
| E13, October 16, 2026 | Throwaway project-local logging plugin, OpenCode v2.0.29, `opencode run --standalone`, user's configured model; no product under test | Hook firing, prompt and context injection, subagent coverage, compaction, event stream | Environment tested | Pass for capture and injection, one item unconfirmed (details below) |
| Product pilots | Not selected | None executed | Documentation/source inspection only | No runtime pass/fail claim |

E13 details:

- **Prompt hook** fired once per admission, with `sessionID`, `messageID`, `prompt`, `metadata` and `delivery`. An appended canary reached the model as part of the user message.
- **Context hook** fired before agent-loop model calls, including after tool results and the first call after compaction, with `sessionID` and `agent`. A system addition containing the agent name reached the model: the parent reported `CANARY-CTX-build`, the subagent `CANARY-CTX-general`.
- **Subagents:** the `subagent` tool created a child session that ran both the prompt hook and the context hook with agent `general`. Tool hooks carry `tool`, `sessionID`, `agent`, `messageID`, call `id` and `input`. Tools called inside Code Mode `execute` also triggered tool hooks.
- **Compaction:** a plugin tool calling `ctx.session.compact` triggered the compaction hook with the transcript, then `session.compaction.started` and `session.compaction.ended` events.
- **Events:** subscription delivered lifecycle, MCP, session and streaming events; events carried location directories. Cross-location events were not tested.
- **Plugin location:** `ctx.location.project.id` was stable across runs in the same directory.
- **Unconfirmed:** whether injected context reaches the model after compaction. In that run the hooks fired and a model step started, but no output arrived within 15 minutes. Run 1 also ran 10 minutes of reasoning without finishing. Both look like model or provider delays rather than hook failures, but the cause was not established.
- **Side observation:** the globally configured PMB MCP server created a `.pmb` workspace in the throwaway directory, consistent with PMB binding storage to the process working directory.
- Five test sessions (four parent, one child) remain in OpenCode's session database, titled "E13 canary run 1–4"; artifacts are under `/tmp/opencode/e13`. No global configuration was changed.

Record actual decisions prompted by experiments in [05](05-decisions-and-open-questions.md), with links to results. Documentation link checks and repository regression tests should be recorded as packaging checks, not added to this product-results table.

## Origin

Written for this repo by 280Zo. Fixtures, procedures and measures are proposals derived from the stated objectives.
