# 01 Objectives and Requirements

[Index](README.md) · [Architecture](02-architecture-and-concepts.md) · [Technologies](03-technology-landscape.md) · [Evaluation](04-evaluation-and-experiments.md) · [Decisions](05-decisions-and-open-questions.md)

## Purpose

Give OpenCode coding agents persistent, structured, searchable project knowledge that they can accurately reuse across sessions and subagents. The system should help agents remember useful work, understand source material, connect facts and retrieve the evidence needed for a particular question without repeatedly rediscovering it.

The investigation must first establish what existing technologies can accomplish, including complete memory applications, before deciding how to assemble them. It is not a search for a database or MCP server in isolation.

## Confirmed objectives

The following describe required system behavior, not a selected implementation. Quantitative thresholds, capture policy and operational guarantees still need agreement.

| ID | Objective | What successful behavior looks like |
|---|---|---|
| K1 | Persistent agent memory and maintenance | Useful knowledge survives context loss and process restarts. Sessions and subagents can recover it. Capture, deduplication, consolidation and maintenance are supported, rather than only transcript saving |
| K2 | Structured knowledge and relationships | Entities and claims have explicit identities and typed relationships. An agent can follow a connection and identify its supporting source; co-occurrence alone is not treated as a factual relationship |
| K3 | Document and image knowledge | Documents, photographs, diagrams and tables can contribute usable knowledge. Original sources remain available alongside extracted structure and model interpretations, not replaced by summaries/captions |
| K4 | Accurate, question-appropriate hybrid retrieval | Exact/keyword, semantic/vector and relationship-based retrieval work together where useful. Identifier questions, conceptual questions and dependency questions retrieve the right evidence, not merely similar text |
| K5 | Project-aware sharing across agents | Multiple sessions and subagents can access intended knowledge without unrelated-project leakage through normal use. Scope is explicit. Physical storage layout and adversarial isolation strength remain open |
| K6 | Provenance and evidence quality | A retrieved claim can be traced to its source and relevant location/version where available. Extracted text, model interpretations and confirmed knowledge remain distinguishable. Missing/conflicting evidence is visible |
| K7 | Knowledge lifecycle | Updates, corrections, supersession, deletion and rebuilds have defined behavior. Consolidation does not silently lose important evidence or keep unsupported claims active |

These objectives apply to the **complete system**. No single component must implement all seven, and using several components is not itself evidence they work together correctly.

## Required distinctions

| Area | Keep separate |
|---|---|
| Memory | Raw conversation history; extracted candidate facts; curated/confirmed knowledge |
| Graph | Retrieval associations/co-occurrence; typed factual relationships; code-derived structural relationships |
| Vectors | Semantic text retrieval; caption-text retrieval; direct image-vector retrieval |
| Storage | One multi-model engine; multiple coordinated stores; where original files live |
| Sources | Original files; deterministic extracted content; AI-generated interpretations |
| Agents | Access to a shared backend; automatic capture; supported cross-session visibility and concurrent operation |
| Projects | Separate physical databases; logical namespaces; enforced authorization |
| Processing | Work done by the calling session model; separate local models; external inference APIs |
| Lifecycle | Persistence; update propagation; supersession; deletion; index rebuild; backup retention |

## Operational preferences, not hard filters

Earlier notes favor local/self-hosted options, low operational overhead, automatic embeddings and avoiding an unnecessary second generative-model API. Keep those visible as comparison criteria, not assumed exclusions. Local processing can still require separate models and consume compute; using the session model still consumes its context and allowance.

GitHub-available/source-available technologies are in scope regardless of OSI license status. Record license, paid-edition and model-access implications when they affect feasible use, but do not rank architectural fit by license labels or star counts.

PMB and Docling are the current starting configuration, not a selected target architecture. Codebase-memory is another existing integration to consider for structural code knowledge, not automatically the repository for all project knowledge.

## Architectural questions still open

- One shared service outside checkouts, separate per-project stores, or a combination?
- Which knowledge should be project-specific, shared reference material or deliberately cross-project?
- Is project separation intended to prevent accidental retrieval, or also malicious/prompt-injected access?
- Which capture should be automatic, which knowledge needs confirmation, and what must never be captured?
- For images, are textual interpretation, visual question answering and direct visual similarity all required? **Answered October 17, 2026: yes, all three.** The system must store a searchable description, answer questions against the original image, and find visually similar images. Exact text reading (OCR) was not selected as a separate requirement.
- How should uncertainty, contradictory sources and inferred relationships be represented?
- What processing may leave the machine, and what additional local/API inference is acceptable?
- What visibility delay, latency, resource use and maintenance effort are acceptable?
- What should happen to persistent knowledge when a project directory is removed?

These questions belong in [05](05-decisions-and-open-questions.md), not in unstated product filters.

## User answers, October 16, 2026

- **Scope of content:** everything. The system must accept any source type; volume depends on topology and is estimated in [02](02-architecture-and-concepts.md#size-estimates).
- **Trust and capture:** fully AI-managed, with no manual review, in the manner of PMB. Automatic trust decisions are therefore a requirement of the system, not a user task.
- **Project separation:** one central database with a namespace per project (D11 in [05](05-decisions-and-open-questions.md)).
- **No setup:** fully transparent like PMB. No logins, no prompts, and no storage decisions by the user or the model; the project is detected automatically (D12). This is a single user's local system, so protections that add setup are out of scope.

## Non-goals and failure conditions

The objective is not maximum transcript retention, a mandatory graph database, one fashionable framework, zero models, or a star-ranked winner. Nor is it to build a custom memory application before checking existing implementations.

The system fails its purpose if it confidently returns stale/unsupported claims, cannot distinguish similar component names, hides a conflicting source, loses originals or source links, silently misses captured knowledge, or mixes project scopes. Large memory volume and impressive retrieval scores do not compensate for those failures.

## Concrete example

An agent encounters a component document, an interface table and a diagram. In a later session, another agent asks: **"Which component uses interface IF-42, what depends on it, and which source establishes that?"**

The target behavior is to resolve the exact interface, follow explicit source-supported relationships, return the relevant table/diagram/document locations and versions, and distinguish a parsed statement from an inferred diagram interpretation. If a revised source changes the relationship, the answer must not silently reuse the old claim as current.

This is a target scenario, not a tested capability of the current setup. [04](04-evaluation-and-experiments.md) turns it into an experiment.

## Status

Requirements baseline: October 16, 2026, derived from the user's stated objectives and distinctions. Proposed measurement methods are in 04; unresolved choices and approval boundaries are in 05. No product selection follows from this document.

## Origin

Written for this repo by 280Zo.
