# Data Governance & PDPA Considerations

Thailand's **Personal Data Protection Act (PDPA)** governs personal data of LINE
users who interact with the assistant. This note documents how the design respects it
— the JD explicitly lists *"understanding of data governance and PDPA considerations."*

## 1. What personal data the system touches

| Data | Source | Why it exists |
|---|---|---|
| LINE `userId` | LINE platform (per event) | route the reply; optional per-user memory |
| Message text | user input | the question to answer |
| (Order flow) name, address, phone | user provides for purchase | fulfilment only |

The **knowledge base contains no personal data** — only product/policy content.

## 2. Principles applied

- **Purpose limitation.** User messages are used only to generate the reply.
  Fulfilment data (name/address) is used only to ship and for after-sales support.
- **Data minimisation.** The bot does not request more than needed. `userId` is not
  required to answer general questions; only used if per-user memory is enabled.
- **Lawful basis.** Answering an inbound question = legitimate interest / consent by
  initiating chat. Marketing follow-up would require separate explicit consent.
- **Retention.** Logs for quality/monitoring should be **pseudonymised** (hash
  `userId`) and time-boxed (e.g. 30–90 days), then purged. The demo logs message
  text to console only; production should redact before persistence.
- **No third-party disclosure** without consent (mirrors `policies.md`).
- **Data subject rights.** Users can request access / correction / deletion via the
  admin — surfaced in the policy knowledge base.

## 3. LLM-provider considerations

- Message text is sent to the LLM/embeddings provider. Choose a provider/region and
  data-processing terms consistent with PDPA; prefer endpoints that **do not train on
  inputs** (OpenAI API default, or a self-hostable model via OpenRouter).
- Avoid sending fulfilment PII (address/phone) to the LLM — that flow is transactional
  and should bypass the RAG generation path.

## 4. Security

- Secrets (`LLM_API_KEY`, `LINE_CHANNEL_*`) in `.env` / secret manager — never in git
  (enforced by `.gitignore`).
- Webhook authenticity enforced via `X-Line-Signature`.
- TLS terminated at the deployment edge (Cloud Run / reverse proxy).

## 5. Production hardening checklist

- [ ] Hash/pseudonymise `userId` before logging
- [ ] Set log retention + automatic purge
- [ ] PII redaction filter before any persistence
- [ ] Confirm LLM provider data-processing agreement & region
- [ ] Document retention + rights process in a public privacy notice
