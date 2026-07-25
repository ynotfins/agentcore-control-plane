# Bifrost Provider Runbook

**Authority:** `renderers/bifrost/config.json` (providers section)  
**Updated:** 2026-07-24  

## Configured Providers

| Provider | Env Var (NAME ONLY) | Notes |
|---|---|---|
| openai | OPENAI_API_KEY | Standard OpenAI API |
| anthropic | ANTHROPIC_API_KEY_OI | OI-scoped key; valid Anthropic credentials |
| gemini | GEMINI_API_KEY | Google Gemini API |
| xai | XAI_API_KEY | xAI Grok API |
| deepseek | DEEPSEEK_API_KEY | DeepSeek first-class Bifrost provider |
| openrouter | OPENROUTER_API_KEY | LLM routing (distinct from OpenRouter MCP tool server) |
| ollama | (local) | Local Ollama at 127.0.0.1:11434; no API key |

## Adding a Provider

1. Verify the provider name in Bifrost's supported list (see docs/bifrost schema)
2. Add env var to Windows User scope (never commit values)
3. Add provider block to `renderers/bifrost/config.json` providers section using `env.VAR_NAME` reference
4. Copy to runtime config, restart Bifrost
5. Test with a low-cost model call

## Important Distinctions

- **OpenRouter as LLM provider** (OPENROUTER_API_KEY): Routes inference requests to other model providers
- **OpenRouter as MCP tool server** (OAuth via config.db): Discovery tools for model catalog; completely separate
- Do not configure MiniMax, DeepSeek, Venice, or Kimi under the openai provider to bypass validation
- For unsupported custom providers, verify Bifrost custom OpenAI-compatible endpoint mechanism first

## OpenRouter Special Note

OpenRouter must remain OPTIONAL and explicitly selected. Models are accessed via `openrouter/<model-name>` prefix. The OpenRouter LLM provider does not change any IDE's default model.

## Deferred Providers

Missing from Windows User env (keys not present): mistral, groq, cerebras, cohere, perplexity, nebius
MiniMax: not in Bifrost native provider list; configure via OpenRouter or direct API wrapper when needed
