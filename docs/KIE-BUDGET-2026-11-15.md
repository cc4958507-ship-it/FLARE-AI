# Current local Kie limits

At the user's explicit request, the local server configuration now sets:

- `AI_DAILY_CREDIT_LIMIT=100` reported credits per Asia/Amman day.
- `AI_DAILY_CALL_LIMIT=100` provider requests per Asia/Amman day.

The API and agent worker read both settings from ignored `.env`; `.env.example` reflects the chosen configuration. Existing usage remains counted, not reset. The 10-credit estimated per-request reservation, per-task limits, unknown-outcome lock and accounting rules remain active. Provider-reported amounts are application admission controls, not a provider-enforced billing guarantee.

Earlier documents recording 50 credits / 20 calls describe the previous configuration. The daily budget panel remains hidden as requested.
