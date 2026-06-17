# Architecture & Scaling

Stack follows the Uncle Engineer "Custom AI with RAG" course (EP.8 Pinecone,
EP.9 LINE + OpenRouter), with free local e5 embeddings.

## 1. Two pipelines

**Offline (ingestion)** — run when the knowledge base changes (course EP.8):

```
data/knowledge_base/*.md
   │  chunk_markdown()  (split on headers → keep section title; size-bound + overlap)
   │  embed_passages()  (sentence-transformers multilingual-e5-base, "passage:" prefix)
   ▼
Pinecone serverless index  (cosine, namespace=moomhom)
```

**Online (serving)** — per user message (course EP.9):

```
LINE user → LINE Platform → POST /webhook  (FastAPI)
   │  verify X-Line-Signature with channel secret
   │  embed_query()  ("query:" prefix)
   │  Pinecone query top_k=4, include_metadata
   │  filter by score_threshold (drop weak matches)
   ├─ no hits → safe escalation reply (LLM NOT called)
   │  format context (with source/section labels)
   │  system prompt (grounding guardrail + Thai voice) + context + question
   │  OpenRouter LLM (e.g. gemini-2.0-flash-exp:free)
   ▼
reply via LINE Messaging API
```

## 2. Component boundaries (why it's split this way)

| Module | Responsibility | Swappable to |
|---|---|---|
| `chunking.py` | corpus → chunks (+ metadata) | semantic / token chunkers |
| `embeddings.py` | text → vectors (e5 prefixes) | OpenAI / Cohere / bge-m3 |
| `pinecone_store.py` | index lifecycle + handle | pgvector (EP.7), ChromaDB (EP.6), Qdrant |
| `retriever.py` | embed query + search + threshold | add reranker / hybrid search |
| `llm.py` | OpenRouter chat client | any OpenAI-compatible endpoint |
| `prompts.py` | behaviour / guardrails | A/B prompt variants |
| `rag_chain.py` | orchestration + fallback | add multi-turn memory |
| `app.py` | LINE transport | web widget, Messenger, Telegram |

Each boundary is a clean seam, so a stack swap touches one file — which is exactly
what lets this same project also run the EP.6 (ChromaDB) or EP.7 (pgvector) stacks.

## 3. Why these choices

- **Pinecone (managed)** over local FAISS: concurrent reads/writes, metadata
  filtering, scales without ops — and more production-credible for a portfolio.
- **e5 local embeddings**: free, offline, no per-call cost, and strong on Thai. The
  "query:"/"passage:" prefixes are required by e5 and handled centrally.
- **OpenRouter**: free model tier for a demo; one base-URL/key swap moves to OpenAI,
  Anthropic, or a self-hosted model later.

## 4. Scaling to production (priority order)

1. **Metadata filtering / multi-tenant** — namespace per brand or per language;
   filter by `source` to scope answers (e.g. policy-only queries).
2. **Caching** — cache query embeddings and answers for common FAQ to cut latency/cost.
3. **Reranking** — add a cross-encoder reranker between retrieval and generation for
   higher precision on ambiguous Thai queries.
4. **Conversation memory** — persist short per-user context (LINE `userId`) for
   multi-turn flows ("แล้วกลิ่นนี้ราคาเท่าไหร่").
5. **Async + queue** — LINE needs a fast 200; ACK the webhook immediately and run the
   RAG turn on a worker (Cloud Tasks / Celery) under burst load.
6. **Observability** — log grounding rate, escalation rate, latency, token cost.

## 5. Deployment options

| Option | Fit | Notes |
|---|---|---|
| **Cloud Run** (GCP) | recommended | scales to zero, HTTPS built-in, matches Koh's GCP experience |
| **Docker on a VM** | simple | `docker compose up` behind Caddy/Nginx for TLS |
| **ngrok** (dev only) | demo | expose local `:8000` to register the LINE webhook |

## 6. Monitoring & retraining loop (MLOps)

- **Offline eval** (`eval/run_eval.py`) in CI / pre-deploy: grounding accuracy +
  keyword recall must not regress.
- **Online signals** per turn: `grounded` flag, retrieval scores, escalation,
  latency, token cost.
- **"Retraining" for RAG = curation.** Rising escalation on a topic → add/fix a
  knowledge-base doc and re-run `make index`. Fast, cheap loop vs. model retraining.

## 7. Failure modes & safeguards

| Risk | Safeguard |
|---|---|
| Hallucinated price/claim | grounding guardrail + no-context fallback (LLM skipped) |
| Forged webhook calls | `X-Line-Signature` verification |
| LLM/provider outage | escalate to human; health endpoint for orchestrator |
| Medical/allergy questions | prompt rule: defer to professional, no medical advice |
| Stale catalog | re-ingest on KB change; CI eval catches broken facts |
| Threshold too strict/loose | `SCORE_THRESHOLD` tuned via `make eval` (e5 cosine sits high) |
