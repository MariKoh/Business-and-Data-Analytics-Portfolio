# MooM HoM — LINE OA Fragrance Advisor (RAG)

A production-style **Retrieval-Augmented Generation (RAG)** chat assistant for a
home-fragrance brand, deployed on **LINE**. It recommends scents, answers product,
usage, pricing and shipping questions — grounded in a real knowledge base, replying
in natural spoken Thai — and hands off to a human on request.

> **Deployed end-to-end:** LINE Messaging API → FastAPI webhook → retrieval over
> Pinecone → grounded generation. Built following the *Custom AI with RAG* course
> stack (Pinecone + OpenRouter + free local embeddings), applied to a real brand.

<p align="center">
  <img src="docs/assets/demo.gif" width="300" alt="Live demo: greeting, scent recommendation, product carousel, and human handoff on LINE">
</p>

---

## What it does

A solo / SME e-commerce brand can't staff live chat 24/7. This assistant deflects
the repetitive pre-sale questions instantly and on-brand, while **escalating
anything it isn't grounded on to a human** — so it never invents a price or claim.

- 🧠 **RAG-grounded answers** — responds only from the product knowledge base; no hallucinated facts
- 🛡️ **Anti-hallucination guardrail** — when retrieval finds nothing, it never calls the LLM; it offers a menu or hands off
- 🙋 **Human handoff** — user types *"คุยกับแอดมิน"* → bot goes silent for 3h so an admin takes over, then auto-resumes (early resume via *"คุยกับบอท"*)
- 👋 **Warm small-talk** — greetings / thanks / "what can you do" get fast fixed replies (no LLM cost)
- 🛍️ **Product carousel** — product/price/browse queries return a swipeable card carousel with order buttons
- ⏳ **Typing indicator** — LINE loading animation while the answer is generated
- 📊 **Evaluation harness** — grounding accuracy + keyword recall, with an anti-hallucination unit test

---

## Architecture

```
                 ┌──────────────── offline (ingest) ────────────────┐
  knowledge_base/*.md ─► chunk (header+size) ─► embed (e5) ─► Pinecone (upsert)
                 └───────────────────────────────────────────────────┘

  LINE user ─► LINE Platform ─► POST /webhook (FastAPI, signature-verified)
        │
        ├─ show loading animation
        ├─ handoff state? ── in human window ─► stay silent (admin handles)
        ├─ greeting / thanks / menu? ─────────► fixed reply (no LLM)
        ▼
   embed query (e5) ─► Pinecone top-k ─► threshold filter
        │
        ├─ no hit ─► menu / escalation reply (LLM skipped)
        ▼
   prompt (grounding guardrail + Thai brand voice) ─► OpenRouter LLM ─► reply
        └─ product query? ─► + product carousel
```

Full detail in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Vector DB | **Pinecone** (serverless) | managed, scalable, production-credible |
| Embeddings | **sentence-transformers** `multilingual-e5-base` | free, local, strong **Thai** support |
| LLM | **OpenRouter** (OpenAI-compatible) | provider-agnostic; runs on `gpt-4o-mini` or any model via one config line |
| Service | FastAPI + Uvicorn | async webhook, health endpoint |
| Channel | LINE Messaging API (`line-bot-sdk` v3) | deployment surface |
| Packaging | Docker + docker-compose | reproducible, deployable |
| Quality | pytest + offline eval harness | guardrail tests + grounding/recall metrics |
| CI | GitHub Actions | lint + tests on every push |

---

## Evaluation

Scored offline on a curated Thai question set
([`eval/eval_questions.jsonl`](eval/eval_questions.jsonl)) spanning product, pricing,
usage, policy — and out-of-scope questions it must refuse:

```
Grounding accuracy : 10/10 (100%)   # in-scope answered, out-of-scope escalated
Keyword recall     :  9/9  (100%)   # grounded answers contained the right facts
```

Measured on `openai/gpt-4o-mini` with `multilingual-e5-base`. The most important
test ([`tests/test_rag.py`](tests/test_rag.py)) asserts that when retrieval returns
nothing, the chain **never calls the LLM** — the core anti-hallucination guarantee.

```bash
pytest -m "not integration" -q      # unit tests (guardrail, handoff, small-talk, carousel)
python -m eval.run_eval             # grounding + keyword metrics
```

---

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env                 # add OPENROUTER_API_KEY and PINECONE_API_KEY

python -m src.ingest                 # embed knowledge base → Pinecone
python -m scripts.simulate_chat      # try it locally, no LINE channel needed
uvicorn src.app:app --reload --port 8000   # run the webhook
```

Connecting a live LINE channel (ngrok / Cloud Run): [`docs/LINE-DEPLOYMENT.md`](docs/LINE-DEPLOYMENT.md).
Following the course step by step: [`docs/COURSE-COMPANION.md`](docs/COURSE-COMPANION.md).

---

## Repository layout

```
src/
  config · chunking · embeddings · pinecone_store   # ingestion + retrieval
  ingest · retriever · prompts · llm · rag_chain    # the RAG pipeline
  handoff · smalltalk · products · carousel         # conversation features
  handler · app                                     # decision layer + LINE webhook
data/knowledge_base/   products · fragrance_guide · faq · policies   (the RAG corpus)
scripts/   build_index · simulate_chat
eval/      eval set + offline evaluation harness
tests/     guardrail · retrieval · handoff · small-talk · carousel
docs/      PERSONA · HANDOFF · ARCHITECTURE · PDPA-DATA-GOVERNANCE · LINE-DEPLOYMENT · COURSE-COMPANION
Dockerfile · docker-compose.yml · .github/workflows/ci.yml
```

---

## Design decisions worth discussing

- **RAG over fine-tuning** — the catalog is small and changes often (prices, promos,
  new scents). Retrieval keeps answers current with a doc edit + reindex; no retraining.
- **Refuse well, not more** — for a customer-facing brand bot, a clean handoff beats a
  confident wrong answer. Hallucinated prices/claims are a real brand and legal liability.
- **e5 multilingual embeddings** — chosen for Thai; e5's "query:"/"passage:" prefixes
  (handled in `embeddings.py`) measurably improve Thai retrieval.
- **Clean module seams** — swapping Pinecone → pgvector/Chroma, or OpenRouter → another
  provider, is a one-file change. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
- **PDPA-aware** — minimal retention, purpose-limited use; see [`docs/PDPA-DATA-GOVERNANCE.md`](docs/PDPA-DATA-GOVERNANCE.md).

---

*Knowledge-base content reflects MooM HoM, a home-fragrance brand. Product images and
store links in the carousel are placeholders pending final assets. This repository is
an engineering portfolio project.*
