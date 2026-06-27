# LLM Setup Guide — Hybrid Groq + Gemini

## Quick Start (For Demo)

### 1. Get Your API Keys

#### Groq LPU (Primary — Required)
1. Go to: https://console.groq.com/keys
2. Sign up with email or Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `gsk_...`)
5. **Free tier:** 30 requests/minute, 10,000 requests/day
6. **Model:** `llama-3.1-70b-versatile` (recommended) or `llama-3.2-3b-preview` (fastest)

#### Google Gemini (Fallback — Recommended)
1. Go to: https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click **"Create API Key"**
4. Copy the key (should start with `AIza...` or be a long alphanumeric string)
5. **Free tier:** 15 requests/minute, 1M tokens/month
### 2. Configure .env File

```bash
cd /mnt/d/patient-intake-with-ai-triage
cp .env.example .env
nano .env  # or use your preferred editor
```

**Paste your keys:**

```bash
# Primary provider
LLM_PRIMARY_PROVIDER=groq

# Groq (Primary — Fastest)
GROQ_API_KEY=gsk_your-actual-groq-key-here
GROQ_MODEL=llama-3.1-70b-versatile

# Gemini (Fallback)
GEMINI_API_KEY=AIza_your-actual-gemini-key-here
GEMINI_MODEL=gemini-2.0-flash-exp
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `groq==0.11.0` — Groq SDK
- `google-genai==1.0.0` — Gemini SDK

### 4. Test the Setup

```bash
# Start the backend
uvicorn app.main:app --reload

# In another terminal, test the API:
curl -X POST http://localhost:8000/api/v1/triage/analyze \
  -H "Content-Type: application/json" \
  -d '{"symptoms_text": "chest pain for 2 hours"}'
```

**Expected Response (from Groq in ~100ms):**
```json
{
  "source": "llm",
  "urgency": "urgent",
  "department": "emergency",
  "confidence": 0.92,
  "reasoning": "Chest pain radiating suggests cardiac issue requiring immediate attention"
}
```

---

## How the Hybrid System Works

### Flow Diagram

```
User clicks "Analyze"
         │
         ▼
┌─────────────────────┐
│ Try Groq LPU        │ ← Primary (fastest, 30 RPM)
│ (llama-3.1-70b)     │   ~100ms response
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
 Success      Rate Limit
    │         (429 error)
    │             │
    ▼             ▼
Return      ┌─────────────────┐
Result      │ Try Gemini      │ ← Fallback
            │ (gemini-flash)  │   ~300ms
            └────────┬────────┘
                     │
              ┌──────┴──────┐
              │             │
           Success       Fail
              │             │
              ▼             ▼
           Return        Show Manual
           Result        Dropdowns
```

### Code Logic

```python
async def call_llm(symptoms_text: str):
    # 1. Try Groq first (fastest)
    try:
        result = await _call_groq(symptoms_text)
        if result:
            return result  # ✅ Success! (~100ms)
    except RateLimitError:
        # 2. Groq rate limited (hit 30 RPM or 10K/day) → try Gemini
        result = await _call_gemini(symptoms_text)
        if result:
            return result  # ✅ Fallback succeeded! (~300ms)
    
    # 3. Both failed → manual mode
    return None
```

---

## Why Groq + Gemini?

### Groq Advantages:
✅ **Fastest inference** — LPU chips, ~100ms response (3x faster than GPU)
✅ **Generous free tier** — 30 RPM, 10K requests/day (enough for 100+ demos)
✅ **Excellent JSON mode** — Reliable structured output
✅ **Open source models** — Llama 3.1 70B, Llama 3.2 3B
✅ **Easy setup** — Instant key, no credit card

### Gemini Advantages:
✅ **Reliable fallback** — Google infrastructure, never goes down
✅ **Large context** — Up to 1M tokens (though we use 150)
✅ **Good JSON mode** — Native `application/json` response type
✅ **Enterprise trust** — Google brand, data controls available

### Together:
🏆 **Best of both worlds** — Groq speed + Gemini reliability
🏆 **Zero cost for demo** — Both free tiers cover 100+ demo runs
🏆 **Production-ready** — Seamless failover, no downtime

---

## Cost Comparison

| Provider | Free Tier | Paid Rate (per 1M tokens) | Demo Cost (100 triages) |
|----------|-----------|---------------------------|-------------------------|
| **Groq** | 10K/day | $0.39 input / $0.79 output (70B) | **FREE** |
| **Gemini Flash** | 1M tokens/mo | $0.075 input / $0.30 output | **FREE** |
| **OpenAI GPT-4o-mini** | None | $0.15 input / $0.60 output | ~$0.30 |
| **NVIDIA NIM 70B** | 1K/mo | $0.72 input / $2.25 output | ~$0.50 |

**Groq + Gemini is the cheapest and fastest combination** for both demo and production.

---

## Troubleshooting

### "Groq API key invalid"
- Check key starts with `gsk_...`
- Ensure no extra spaces in .env file
- Restart backend: `docker-compose restart backend`
- Verify key is active: https://console.groq.com/keys

### "Gemini fallback also failed"
- Check key starts with `AIza...`
- Ensure Gemini API is enabled for your Google Cloud project
- Check quota: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com

### "Rate limit exceeded" (both providers)
- Groq: 30 RPM or 10K/day — wait or reduce frequency
- Gemini: 15 RPM — wait 1 minute between requests
- For demo: Use seed data instead of live triage if hitting limits

### "JSON parsing failed"
- Model returned markdown or non-JSON response
- Check logs: `docker-compose logs backend | grep "Failed to parse"`
- Try different model: `GROQ_MODEL=llama-3.2-3b-preview`

---

## Model Options

### Groq Models:

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `llama-3.1-70b-versatile` | Fast | ⭐⭐⭐⭐⭐ | Production, balanced |
| `llama-3.2-3b-preview` | ⚡ Fastest | ⭐⭐⭐⭐ | Demo, quick responses |
| `mixtral-8x7b-32768` | Medium | ⭐⭐⭐⭐⭐ | Complex reasoning |

**Recommended:** `llama-3.1-70b-versatile` (best balance)

### Gemini Models:

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `gemini-2.0-flash-exp` | ⚡ Fast | ⭐⭐⭐⭐ | Latest, recommended |
| `gemini-1.5-flash` | Fast | ⭐⭐⭐⭐ | Stable, proven |

**Recommended:** `gemini-2.0-flash-exp` (latest) or `gemini-1.5-flash` (stable)

---

## Production Deployment

### Environment Variables for Production

```bash
# Use managed secrets (AWS Secrets Manager, Azure Key Vault, etc.)
LLM_PRIMARY_PROVIDER=groq
GROQ_API_KEY=${GROQ_API_KEY_FROM_SECRETS}
GEMINI_API_KEY=${GEMINI_API_KEY_FROM_SECRETS}

# Enable monitoring
LOG_LEVEL=INFO
ENABLE_LLM_METRICS=true
```

### Monitoring LLM Usage

Add to your monitoring dashboard:

```python
# Log LLM provider and latency
logger.info(f"LLM request: provider={provider}, model={model}, latency_ms={duration}")

# Track fallback rate
if fallback_used:
    logger.warning(f"Groq failed, Gemini fallback used")
```

### Scaling Considerations

**For >1,000 triages/day:**
1. Groq paid tier ($0.39/1M tokens — still cheap)
2. Add caching for common symptom patterns
3. Consider self-hosted Llama 3.1 on your GPU (Ollama)

---

## Switching Providers

### Use Only Groq (Disable Fallback)

```bash
# .env
LLM_PRIMARY_PROVIDER=groq
GEMINI_API_KEY=  # Leave empty
```

### Use Only Gemini (Skip Groq)

```bash
# .env
LLM_PRIMARY_PROVIDER=gemini
GROQ_API_KEY=  # Leave empty
```

### Use Different Models

```bash
# Faster but less accurate
GROQ_MODEL=llama-3.2-3b-preview
GEMINI_MODEL=gemini-1.5-flash

# More accurate (but slower)
GROQ_MODEL=llama-3.1-70b-versatile
GEMINI_MODEL=gemini-2.0-flash-exp
```

---

## Security Best Practices

✅ **DO:**
- Store API keys in environment variables or secrets manager
- Rotate keys every 90 days
- Monitor usage dashboards weekly
- Set up billing alerts (even for free tier)

❌ **DON'T:**
- Commit `.env` to git (it's gitignored for a reason!)
- Hardcode keys in source code
- Share API keys in Slack/email
- Use personal keys in production

---

## Support & Resources

- **Groq Console:** https://console.groq.com
- **Groq Docs:** https://console.groq.com/docs
- **Gemini AI Studio:** https://aistudio.google.com
- **Gemini Docs:** https://ai.google.dev/gemini-api/docs
- **Issue Tracker:** Report LLM issues in project repo
- **Demo Checklist:** See README.md Pre-Demo section

---

**Last Updated:** June 2025  
**Tested With:** Groq Llama 3.1 70B, Gemini 2.0 Flash  
**Status:** ✅ Production Ready  
**Performance:** Groq ~100ms, Gemini ~300ms  
**Free Tier:** 10K+ requests/day combined