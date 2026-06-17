# Course Companion — Uncle Engineer "Custom AI with RAG" → MooM HoM Project

A study guide that maps the 10-episode course to **this repository**. For each
episode: what it teaches, what you build in *your* project, the exact commands,
and a ship-gate checkbox so you keep moving (anti-stall).

> Important: I (Ray) could not watch the videos or open the slides (they're behind
> Google sign-in). This guide is built from each episode's title + description and
> standard RAG practice. Watch the video for the live coding; use this to apply it
> to MooM HoM. Where the video differs, the video wins — note the diff here.

**Course channel:** Uncle Engineer / Uncle Labs · **Stack:** Pinecone + OpenRouter
+ free local embeddings · **Your repo:** `moomhom-line-rag-assistant`

Each episode's slides live in its YouTube description. Keep them open while you watch.

---

## How to use this guide
1. Watch the episode.
2. Do the "Build in your repo" steps here against MooM HoM content.
3. Tick the ship gate. **Don't polish past the gate** — move to the next episode.
4. Note anything the video does differently in the "Notes from the video" line.

---

## EP.1 — Course overview + Python on Colab
**Teaches:** big picture of RAG; Python basics; running Python in Google Colab.
**Build in your repo:** nothing yet — orientation. Confirm you can run Python 3.11.
**Commands:**
```bash
python --version        # expect 3.11.x
```
- [ ] **Gate:** Python runs; you understand the RAG big picture (retrieve → augment → generate).
- Notes from the video: ____________________

## EP.2 — Python data structures (list / tuple / dict / set) + RAG example
**Teaches:** core Python containers; a first taste of a RAG example.
**Build in your repo:** read `src/chunking.py` — it uses lists + dataclasses; make
sure the structures make sense to you.
- [ ] **Gate:** you can read every line of `chunking.py` and explain it.
- Notes from the video: ____________________

## EP.3 — Compare vector DBs · CLI · venv · pip · files & modules
**Teaches:** how vector DBs differ (Pinecone vs Chroma vs pgvector…); terminal
basics; virtual environments; Python packaging.
**Build in your repo:** set up your environment.
```bash
cd moomhom-line-rag-assistant
python -m venv .venv
.venv\Scripts\activate          # Windows  (mac/linux: source .venv/bin/activate)
make install                     # or: pip install -r requirements.txt
```
- [ ] **Gate:** `.venv` active and `pip list` shows pinecone, sentence-transformers, openai.
- Notes from the video: ____________________
- Why we picked Pinecone: managed + free tier + scales (see `docs/ARCHITECTURE.md §3`).

## EP.4 — NLP basics + Prompt Engineering
**Teaches:** tokenisation, embeddings intuition; how to write good prompts.
**Build in your repo:** this is the episode for `src/prompts.py`.
- Open `src/prompts.py`. It already encodes: (1) grounding guardrail (answer only
  from context), (2) MooM HoM Thai brand voice, (3) escalation rule, (4) no medical
  advice. Tweak the wording to your taste as you learn prompt techniques.
- [ ] **Gate:** you can explain why the "answer only from context" rule prevents
  hallucinated prices. Edit one line of the system prompt and re-run `make chat`.
- Notes from the video: ____________________

## EP.5 — Transformer & RAG fundamentals
**Teaches:** how transformers/embeddings work; the RAG flow end-to-end.
**Build in your repo:** read `docs/ARCHITECTURE.md §1` — match each box to the
course diagram. Read `src/embeddings.py` (note the e5 "query:"/"passage:" prefixes).
- [ ] **Gate:** you can draw the offline (ingest) and online (serve) pipelines from memory.
- Notes from the video: ____________________

## EP.6 — Hands-on: Local LLMs + embeddings with Ollama + ChromaDB
**Teaches:** running models locally with Ollama; ChromaDB as a local vector store.
**Build in your repo:** OPTIONAL local-first track. Our default is Pinecone, but the
module seams let you try Chroma locally. If you want to follow EP.6 literally:
```bash
# optional experiment, not required for the portfolio build
pip install chromadb ollama
```
Then read `src/pinecone_store.py` and notice it's the only file you'd swap to use
Chroma. **Recommendation:** watch to understand local RAG, but stay on Pinecone for
the shippable project so you don't fork your effort.
- [ ] **Gate:** you understand that Chroma/Ollama is the same pattern, local. (Optional: got one local query working.)
- Notes from the video: ____________________

## EP.7 — Git 101 · Docker 101 · PostgreSQL + pgvector + pgAdmin
**Teaches:** version control; containers; Postgres as a vector DB (pgvector).
**Build in your repo:** the MLOps episode.
```bash
git init && git add . && git commit -m "MooM HoM RAG: course build"
# create an empty GitHub repo, then:
git remote add origin https://github.com/<you>/moomhom-line-rag-assistant.git
git push -u origin main
docker build -t moomhom-line-rag .      # Docker 101 applied to your project
```
- pgvector is an alternative to Pinecone (see `docs/ARCHITECTURE.md §2`). You don't
  need to migrate — just understand it's a one-file swap (`pinecone_store.py`).
- [ ] **Gate:** repo pushed to GitHub; `docker build` succeeds; CI (`.github/workflows/ci.yml`) green.
- Notes from the video: ____________________

## EP.8 — Pinecone vector DB + example Python RAG pipeline
**Teaches:** Pinecone setup; a full Python RAG pipeline.
**Build in your repo:** THIS is your ingestion + retrieval core.
```bash
# 1. create a free Pinecone account → API key → put in .env
# 2. create a free OpenRouter key → put in .env
make index      # chunk → embed (e5) → upsert MooM HoM KB to Pinecone
make chat       # ask: กลิ่นไหนช่วยให้นอนหลับ   → expect a Calm Down answer
make eval       # grounding accuracy + keyword recall
```
- Files in play: `src/ingest.py`, `src/embeddings.py`, `src/pinecone_store.py`,
  `src/retriever.py`.
- Tune `SCORE_THRESHOLD` in `.env` using `make eval` (e5 cosine scores sit high,
  ~0.80+; if good answers get dropped, lower it; if junk leaks in, raise it).
- [ ] **Gate (= Build-Brief Gate A):** `make chat` answers the 10 eval questions
  correctly in Thai; `make test` green. **Commit.** This alone is portfolio-worthy.
- Notes from the video: ____________________

## EP.9 — Hands-on: LINE chatbot + RAG (Pinecone + OpenRouter, all free)
**Teaches:** wiring a LINE chatbot to the RAG pipeline. (Course uses a coffee shop;
yours is MooM HoM fragrance.)
**Build in your repo:** the webhook + live channel.
```bash
make serve                      # runs FastAPI: GET /health, POST /webhook
# expose it and register the webhook — full steps in docs/LINE-DEPLOYMENT.md
ngrok http 8000                 # dev: get an https URL for the LINE console
```
- Files in play: `src/app.py` (LINE webhook, signature-verified), `src/rag_chain.py`.
- Map the course's coffee-shop KB to your `data/knowledge_base/*.md` (already done).
- [ ] **Gate (= Build-Brief Gates B→C):** webhook verified in LINE console; one real
  conversation from your phone, **screen-recorded** for the portfolio. **Commit.**
- Notes from the video: ____________________

## EP.10 — Wrap-up / finalize
**Teaches:** (no description — typically polish, deployment, Q&A.)
**Build in your repo:** finishing touches, timeboxed.
- Add README screenshots + the demo GIF from EP.9.
- Deploy to Cloud Run (optional) per `docs/LINE-DEPLOYMENT.md`.
- Paste your real `make eval` numbers into the README results table.
- [ ] **Gate (= Build-Brief Gate D):** README tells the story with a real eval table
  and demo clip. **Then STOP** and add the repo link to your résumé.
- Notes from the video: ____________________

---

## Stack cross-reference (course term → your repo)

| Course concept | Where it lives in your repo |
|---|---|
| Vector DB (Pinecone) | `src/pinecone_store.py`, `src/retriever.py` |
| Embeddings | `src/embeddings.py` (e5, free, Thai-capable) |
| Chunking | `src/chunking.py` |
| Ingestion pipeline | `src/ingest.py` (`make index`) |
| Prompt engineering | `src/prompts.py` |
| LLM call (OpenRouter) | `src/llm.py` |
| RAG orchestration | `src/rag_chain.py` |
| LINE chatbot | `src/app.py` (`make serve`) |
| Local test harness | `scripts/simulate_chat.py` (`make chat`) |
| Evaluation | `eval/run_eval.py` (`make eval`) |
| Docker / Git / CI | `Dockerfile`, `.github/workflows/ci.yml` |

## Where this project intentionally goes beyond the course
These are your "senior" differentiators to mention in an interview:
- An **evaluation harness** with grounding accuracy + keyword recall (most tutorials skip eval).
- A hard **anti-hallucination guardrail** with a unit test proving the LLM is skipped on no-context.
- **PDPA / data-governance** write-up (`docs/PDPA-DATA-GOVERNANCE.md`).
- **CI** that runs tests on every push.
- A documented **scaling path** (Chroma / pgvector / reranking / async) — showing you
  know the production roadmap, not just the demo.
