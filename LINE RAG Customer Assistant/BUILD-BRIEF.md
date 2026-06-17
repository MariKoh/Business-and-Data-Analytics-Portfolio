# Build Brief — MooM HoM LINE RAG Assistant (Portfolio Project 2)

**Owner:** Koh · **Advisor:** Ray
**Purpose:** Flagship GenAI/RAG portfolio piece for the **Senior Data Scientist** application.
**Start:** 2026-06-16 · **Target ship (live demo):** see ship gates below.

---

## 1. Why this project (JD alignment)

The target JD lists, under Key Responsibilities and Preferred Qualifications:
*"Develop GenAI/LLM-based applications and automation tools"*, *"Experience with GenAI,
LLM applications, prompt engineering, or RAG pipelines"*, *"MLOps … deployment, monitoring …
CI/CD"*, *"retail / e-commerce / digital business"*, and *"data governance and PDPA"*.

This project hits **all five** with one coherent, real artifact: a customer-facing
**fragrance advisor** for MooM HoM, served over **LINE OA**, grounded in a real product
knowledge base via RAG.

> Positioning note (Ray): This is deliberately split from Portfolio Project 1
> (the retail ML repo). Project 1 proves classical DS (forecasting, segmentation,
> CLV/churn, MBA). **Project 2 proves applied GenAI in production.** Together they
> cover the full JD.

---

## 2. Scope (locked from scoping Q&A, 2026-06-17)

| Decision | Choice |
|---|---|
| Use case | **Customer fragrance advisor** (LINE) — scent recommendation, product, usage, FAQ, shipping |
| Stack | **Pinecone + OpenRouter + local e5 embeddings + FastAPI** (matches Uncle Engineer "Custom AI with RAG" course EP.8–9) |
| Depth | **Full live LINE OA deployment** — but built so the runnable core ships independently of live wiring |
| Learning | Follow the 10-episode course via `docs/COURSE-COMPANION.md` |

---

## 3. Module map (each maps to a JD bullet)

| # | Module | Files | JD bullet it proves |
|---|---|---|---|
| 1 | Knowledge base ingestion (load→chunk→embed→upsert) | `src/ingest.py`, `src/chunking.py`, `src/embeddings.py`, `data/knowledge_base/*` | "Build scalable data pipelines, feature engineering workflows" |
| 2 | Retrieval layer (Pinecone, thresholded) | `src/retriever.py`, `src/pinecone_store.py` | "RAG pipelines" |
| 3 | Prompt engineering (grounding guardrail, Thai brand voice, escalation) | `src/prompts.py` | "prompt engineering", "LLM applications" |
| 4 | RAG orchestration + anti-hallucination fallback | `src/rag_chain.py` | "GenAI/LLM-based applications" |
| 5 | LINE webhook service (signature-verified) | `src/app.py` | "deploy end-to-end AI solutions", "automation tools" |
| 6 | Evaluation harness (grounding accuracy, keyword recall) | `eval/run_eval.py`, `eval/eval_questions.jsonl` | "model evaluation", "monitoring" |
| 7 | MLOps: Docker, docker-compose, CI, healthcheck | `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` | "MLOps … CI/CD … monitoring" |
| 8 | Data governance write-up | `docs/PDPA-DATA-GOVERNANCE.md` | "data governance and PDPA considerations" |
| 9 | Architecture + scaling write-up | `docs/ARCHITECTURE.md` | "scalable, production-ready", communicate to stakeholders |

---

## 4. Ship gates (anti-stall — non-negotiable)

Ray's note: your pattern is to polish past "good enough." Each gate is DONE-and-move-on.
Do **not** start a later gate before the earlier one is committed to git.

- **Gate A — Runnable core (target: Day 1–2).**
  `make index && make chat` answers the 10 eval questions correctly in Thai.
  `make test` green. **Commit. This alone is a portfolio-worthy artifact.**
- **Gate B — Service + container (Day 2–3).**
  `make up` serves `/health` and `/webhook`; webhook tested with a sample LINE
  payload locally. CI green on GitHub. **Commit + push.**
- **Gate C — Live LINE channel (Day 3–4).**
  Real LINE OA channel connected, ngrok/Cloud Run public webhook, 1 real
  conversation screen-recorded for the portfolio. **Commit deployment notes.**
- **Gate D — Polish (timeboxed ≤ half a day).**
  README screenshots, demo GIF, architecture diagram export. **Then STOP.**

> If Gate C slips on credentials/hosting, the project is **still shippable** at
> Gate B with `docs/LINE-DEPLOYMENT.md` describing the live step. Do not let the
> live channel become a reason nothing ships.

---

## 5. Honest-gap handling

Same discipline as Project 1 — claim only what's real:
- Vector store is managed **Pinecone** (serverless free tier). The course also
  teaches local alternatives (ChromaDB EP.6, pgvector EP.7) — the clean module
  seams in `pinecone_store.py` make those swaps a one-file change, documented in
  `docs/ARCHITECTURE.md`.
- Embeddings run locally (e5) — free, no per-call cost; the trade-off vs. hosted
  embeddings is noted honestly.
- No fine-tuning. This is retrieval-augmented, which is the correct, defensible
  choice for a small, fast-changing product catalog — say exactly that in interview.

---

## 6. Definition of done

- [ ] Gate A committed (core + tests + eval pass)
- [ ] Gate B committed + pushed (Docker + CI green)
- [ ] Gate C committed (live LINE conversation captured) — or Gate B + deployment doc
- [ ] README tells the story in Senior-DS voice with a results/eval table
- [ ] Repo link added to `Kattiya-Resume-Senior-Data-Scientist.docx`
