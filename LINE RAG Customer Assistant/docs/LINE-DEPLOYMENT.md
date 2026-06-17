# Connecting a Live LINE OA Channel (Gate C)

Goal: take the running webhook and connect a real **LINE Official Account** so a phone
can chat with the assistant. Capture one real conversation for the portfolio.

## Prerequisites
- A LINE Official Account (create at <https://manager.line.biz>)
- A **Messaging API channel** in the LINE Developers Console (<https://developers.line.biz>)
- The service running and reachable over **HTTPS** (LINE requires TLS)

## Step 1 — Create the Messaging API channel
1. LINE Developers Console → create a provider → create a **Messaging API** channel
   (or link your existing OA: OA Manager → Settings → Messaging API → Enable).
2. From the channel's **Basic settings**, copy **Channel secret** → `LINE_CHANNEL_SECRET`.
3. From **Messaging API** tab, issue a **Channel access token (long-lived)** →
   `LINE_CHANNEL_ACCESS_TOKEN`.
4. Put both in `.env`.

## Step 2 — Expose the webhook over HTTPS

**Dev / demo (fastest):** ngrok
```bash
make serve                 # runs uvicorn on :8000
ngrok http 8000            # gives https://<random>.ngrok-free.app
```

**Production:** Google Cloud Run (matches Koh's GCP experience)
```bash
gcloud run deploy moomhom-line-rag \
  --source . --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars "LLM_API_KEY=...,LINE_CHANNEL_SECRET=...,LINE_CHANNEL_ACCESS_TOKEN=..."
# → returns an https URL, scales to zero when idle
```

## Step 3 — Register the webhook URL
1. LINE Developers Console → Messaging API → **Webhook URL** =
   `https://<your-host>/webhook`
2. Click **Verify** (should return success → our `/webhook` returns 200).
3. Turn **Use webhook = ON**.
4. Under **LINE Official Account features**, turn **OFF** "Auto-reply messages" and
   "Greeting messages" so they don't collide with the bot (optional).

## Step 4 — Test from a phone
1. Add the OA as a friend via its QR code / basic ID.
2. Send: *"กลิ่นไหนช่วยให้นอนหลับ"* → expect a Calm Down recommendation in Thai.
3. Send an out-of-scope question (*"มีกลิ่นกุหลาบไหม"*) → expect the escalation reply.
4. **Screen-record this conversation** → add the GIF/clip to the README (Gate D).

## Troubleshooting
- **Webhook verify fails** → host not HTTPS / not reachable; check ngrok or Cloud Run URL.
- **401 / Invalid signature** → `LINE_CHANNEL_SECRET` mismatch.
- **Bot silent but verify OK** → "Use webhook" is OFF, or auto-reply is intercepting.
- **Slow / timeout** → LINE needs a fast 200; for heavy load, ACK first and process
  the RAG turn on a worker (see ARCHITECTURE §3.5).

> If live hosting stalls, the project still ships at **Gate B** (container + CI +
> local webhook test). Do not let the live channel block the portfolio.
