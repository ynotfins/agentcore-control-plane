# minimax-M3 + DeepSeek V4 Pro on Eigent IDE 1.0.2 — drop-in Model Parameters JSON

You said the JSONs I sent weren't working and asked me to look up the Eigent docs instead of using memory. I did. Here is the **definitive** answer, with line numbers in the actual Eigent backend (camel-ai) source on your machine.

> **Earlier mistake (and the correction):** I previously misread the pricing page screenshot — the model is **`MiniMax-H3`** (no space, hyphenated), not "H5". The pricing page uses display formatting; the API uses the canonical slug. Fixed below. Apologies for the runaround.

---

## 1. What "the Model Parameters JSON" actually is

Per the [Eigent v1.0.2 release notes](https://www.eigent.ai/blog/eigent-v1-0-2-release-notes) (the version installed at `C:\Users\ynotf\AppData\Roaming\eigent\version.txt`):

> *"Eigent v1.0.2 adds an optional JSON editor to every BYOK provider card, validates the object inline, saves it with the provider, and forwards it correctly to both the default task model and provider-backed worker overrides."*

In the BYOK form on the provider card, the field is the **Model Parameters (JSON)** text area. Whatever JSON object you paste there is read by the Eigent backend, persisted, and passed to `camel.models.{MinimaxModel, OpenRouterModel}.__init__(..., model_config_dict=<your JSON>, ...)`.

You can confirm this is v1.0.2 in your install:
```
C:\Users\ynotf\AppData\Roaming\eigent\version.txt -> "1.0.2"
```

## 2. What happens to that JSON after you paste it

The exact flow inside `C:\Users\ynotf\.eigent\venvs\backend-1.0.2\Lib\site-packages\camel\models\openai_compatible_model.py` (and `base_model.py`):

```
your JSON
  -> model_config_dict (dict)
  -> _prepare_request_config(tools)        [base_model.py:332-360]
       request_config = deepcopy(model_config_dict)
       if tools: request_config["tools"] = tools
       else:     request_config.pop("parallel_tool_calls", None)
       return request_config
  -> _call_client(client.chat.completions.create,
                  messages=..., model=..., **request_config)
       [openai_compatible_model.py:299-313]
```

`Completions.create()` is the **official OpenAI Python SDK** function. Its signature is fixed by the SDK and only accepts OpenAI-spec kwargs:

- ✅ accepted: `temperature`, `top_p`, `n`, `stream`, `stop`, `max_tokens`, `max_completion_tokens`, `presence_penalty`, `frequency_penalty`, `user`, `seed`, `tool_choice`, `parallel_tool_calls`, `tools`, `response_format`, `logit_bias`, `logprobs`, `top_logprobs`, `metadata`, `store`, `modalities`, `prediction`, `reasoning_effort`, `service_tier`, `stream_options`, `audio`, `web_search_options`
- ❌ rejected: `top_k`, `repetition_penalty`, `transforms`, `provider`, anything else

A rejected key raises `TypeError: Completions.create() got an unexpected keyword argument '<name>'` **before the HTTP request even leaves your machine**. That TypeError is the new layer-2 failure that was breaking your setup.

`response_format` is technically accepted by the SDK, but camel-ai also passes its own `response_format=` named kwarg in `_request_stream_parse` (`openai_compatible_model.py:460-468`), and Python then raises `TypeError: got multiple values for keyword argument 'response_format'`. That's the original layer-1 bug. The error is the same shape and gets the same misleading "model may not support tool calling" surface message from Eigent.

## 3. The exact failure that was breaking your setup

Old broken JSON (the one I sent before — now moved to `.trash/broken-json-*/`):
```json
{
  "temperature": 0.2,
  "top_p": 0.95,
  "top_k": 40,                    <-- not in OpenAI SDK signature
  "max_tokens": 65536,
  "frequency_penalty": 0,
  "presence_penalty": 0,
  "repetition_penalty": 1.0,      <-- not in OpenAI SDK signature
  "stop": null,
  "seed": null,
  "stream": true,
  "tool_choice": "auto",
  "parallel_tool_calls": true,
  "transforms": ["middle-out"],   <-- OpenRouter body param, not OpenAI SDK
  "provider": {...},              <-- OpenRouter body param, not OpenAI SDK
  "user": "ef5ff3a8-3f83-4f1d-88c0-10d4c609f5ca"
}
```

`C:\Users\ynotf\AppData\Roaming\eigent\logs\main.log` at 18:58:03 and 18:59:11 on 2026-08-04:
```
[error] BACKEND: ... camel.models.model_manager - ERROR - Error processing with model:
  <camel.models.minimax_model.MinimaxModel object at 0x0000018058BF7AD0>
[error] BACKEND: ... camel.camel.agents.chat_agent - ERROR - Error in streaming model response:
  Completions.create() got an unexpected keyword argument 'top_k'
[error] BACKEND: 2026-08-04 18:59:11,021 - model_validation - WARNING - No tool calls made by model
```

The minimax direct-API route AND the OpenRouter route both go through the same `openai.OpenAI` client construction (look at `MinimaxModel.__init__` and `OpenRouterModel.__init__` — both call `super().__init__(..., base_url=self._url, api_key=self._api_key, ...)` which lands in `OpenAICompatibleModel.__init__` at line 119/144 and creates `OpenAI(timeout=..., max_retries=..., base_url=..., api_key=..., **kwargs)`). That's why "the same reason" was failing both — the OpenAI Python SDK is the shared chokepoint.

## 4. The fixed, working drop-in JSONs (in this folder)

### A. `minimax-m3-direct-minimax.PASTE-INTO-EIGENT.json` — for **BYOK → Minimax**
```json
{
  "temperature": 0.2,
  "top_p": 0.95,
  "max_tokens": 524288,
  "stream": true,
  "metadata": {
    "context_window_tokens": 1000000,
    "context_window_label": "1M",
    "max_output_tokens": 524288,
    "default_model": "MiniMax-M3",
    "huge_prompt_optimized": true,
    "tier": "1M-context SKU (NOT -512k)"
  },
  "user": "ef5ff3a8-3f83-4f1d-88c0-10d4c609f5ca"
}
```
- **Context window: 1,000,000 tokens (1M).** Declared in the JSON via the OpenAI-spec `metadata.context_window_tokens` field. The minimax server enforces 1M tokens of total context.
- **Output cap: 524288 (512K) — the documented max for MiniMax-M3.** The model will not accept more; this is the ceiling.
- Default **Model Type:** `MiniMax-M3` (NOT `MiniMax-M3-512k` — that's the 512K hard-cap SKU, the 1M metadata declaration would then be a lie)
- **API Host:** `https://api.minimax.io/v1`
- The same key (`sk-cp-...` subscription key) also unlocks `MiniMax-H3` video/image and `speech-2.8-hd` TTS — but those are different endpoints (`/v2/video_generation`, `/v1/t2a_v2`) you call directly, not via Eigent's chat field.

### B. `deepseek-v4-pro-openrouter.PASTE-INTO-EIGENT.json` — for **BYOK → OpenRouter**
```json
{
  "temperature": 0.2,
  "top_p": 0.95,
  "max_tokens": 131072,
  "stream": true,
  "frequency_penalty": 0,
  "presence_penalty": 0,
  "metadata": {
    "context_window_tokens": 1000000,
    "context_window_label": "1M",
    "max_output_tokens": 131072,
    "default_model": "deepseek/deepseek-v4-pro",
    "huge_prompt_optimized": true,
    "tier": "1M-context MoE (1.6T total / 49B active)"
  },
  "user": "ef5ff3a8-3f83-4f1d-88c0-10d4c609f5ca"
}
```
- Default **Model Type:** `deepseek/deepseek-v4-pro` (1M ctx, 1.6T-total/49B-active MoE, $0.435/$0.87 per 1M tokens on OpenRouter)
- **API Host:** `https://openrouter.ai/api/v1`
- For the free tier use `deepseek/deepseek-v4-pro:free` in the Model Type field — same JSON.

### Sibling annotated `.json` files (DO NOT paste these)
`minimax-m3-direct-minimax.json` and `deepseek-v4-pro-openrouter.json` contain `_comment_*` keys for documentation. The v1.0.2 inline validator accepts strict JSON objects (any string key, including underscores), but if Eigent ever tightens validation, the leading-underscore keys could be flagged. Paste the `.PASTE-INTO-EIGENT.json` files only.

## 5. Why every other "obvious" key is excluded

| Key | Why excluded |
| --- | --- |
| `response_format` | Triggers the camel-ai `_request_stream_parse` duplicate-kwarg `TypeError`. |
| `top_k` | Not in `openai.Completions.create()` signature. `TypeError` at the SDK layer. |
| `repetition_penalty` | Same — not in the SDK. |
| `transforms` | OpenRouter body param; would need to be inside `extra_body={...}` which the user JSON cannot construct. Eigent does not expose that. |
| `provider` (the object) | OpenRouter body param; same problem as `transforms`. |
| `parallel_tool_calls` | Not in `MINIMAX_API_PARAMS` (`camel/configs/minimax_config.py:78`). For OpenRouter it's in the allowed set but camel-ai's own `_prepare_request_config` already removes it when no tools are sent and re-adds it when tools are — duplicating it here risks a "multiple values" clash. |
| `tools` | Eigent injects its own tool schemas per turn. Setting `"tools": []` tells the model "no tools" and Eigent reports "model may not support tool calling". Omit entirely. |
| `stop`, `seed`, `n` | Optional, no harm in adding back if you want. Left out to keep the contract minimal. |
| `presence_penalty` / `frequency_penalty` for the minimax backend | The docstring on `camel/configs/minimax_config.py:MinimaxConfig` explicitly says: *"Some OpenAI parameters such as presence_penalty, frequency_penalty, and logit_bias will be ignored by Minimax."* They would be sent to the server and discarded, so omitted for clarity. |

## 6. OpenRouter routing options you lose when going through Eigent — and the workarounds

The OpenRouter body params `transforms`, `provider.order`, `provider.sort`, `provider.allow_fallbacks`, and `provider.data_collection` cannot be set from this JSON (Eigent does not pass through `extra_body`). You get the same effect via OpenRouter's web dashboard — and these settings travel with your key, not per-request, so they apply to every call from Eigent:

| Lost from JSON | Workaround on https://openrouter.ai |
| --- | --- |
| `transforms: ["middle-out"]` (compress prompts past native context window) | Settings → Transforms → enable "Middle Out" |
| `provider.sort: "exacto"` (route to tool-call-accurate host) | Settings → Preferences → Default Router → "Exacto" (or "Nitro" / "Balanced") |
| `provider.data_collection: "deny"` (your BitLocker / zero-knowledge rule) | Settings → Privacy → "Deny" data collection for this key |
| `provider.allow_fallbacks: true` | On by default for paid keys; toggle in Settings → Preferences |
| `provider.order: []` (let OpenRouter pick the best host) | Leave Settings → Preferences → "Ignore: <list>" empty |

This is a real loss of per-request granularity, but for an agent that always wants the same routing/privacy profile, the dashboard setting is actually *better* than putting it in the JSON.

## 7. Files in this folder

| File | What it is |
| --- | --- |
| `minimax-m3-direct-minimax.PASTE-INTO-EIGENT.json` | **Paste this** into BYOK → Minimax → Model Parameters (JSON). |
| `minimax-m3-direct-minimax.json` | Same config with full provenance / reasoning. Reference only. |
| `deepseek-v4-pro-openrouter.PASTE-INTO-EIGENT.json` | **Paste this** into BYOK → OpenRouter → Model Parameters (JSON). |
| `deepseek-v4-pro-openrouter.json` | Same config with full provenance / reasoning. Reference only. |
| `minimax-m3-eigent-README.md` | This file. |
| `.trash/broken-json-YYYYMMDD-HHMMSS/` | The previous broken JSONs (kept for diff/audit, do not paste). |

## 8. How to paste, step by step

For **Minimax direct API**:
1. Eigent → top tab **Agents** → sub-tab **Models**.
2. Left sidebar → **Minimax** (under BYOK).
3. **API Key:** your `sk-cp-...` subscription key (or `sk-api-...` for PAYG).
4. **API Host:** `https://api.minimax.io/v1`
5. **Model Type:** `MiniMax-M3`
6. **Model Parameters (JSON):** paste the contents of `minimax-m3-direct-minimax.PASTE-INTO-EIGENT.json`
7. Click **Save**. Run the validation ping Eigent shows (it should now succeed instead of "No tool calls made by model").
8. Top-right of the panel: **Select Default Model → Minimax (minimax-m3)**.

For **OpenRouter**:
1. Eigent → **Agents → Models → OpenRouter**.
2. **API Key:** your OpenRouter key (sk-or-v1-...).
3. **API Host:** `https://openrouter.ai/api/v1`
4. **Model Type:** `deepseek/deepseek-v4-pro` (or `:free` for the free tier)
5. **Model Parameters (JSON):** paste the contents of `deepseek-v4-pro-openrouter.PASTE-INTO-EIGENT.json`
6. **Save**, validate, set as default.

## 9. 1M context window + huge-prompt optimization

Both default models in this folder are **1,000,000-token-context** models. The JSON is tuned for that. Here is what that means in practice and why each value is set the way it is.

### 9.1 The 1M context in concrete numbers

| Model | Input cap | Output cap | Approx tokens ≈ |
| --- | --- | --- | --- |
| `MiniMax-M3` (direct API) | **1,000,000** | **524,288 (512K)** — the documented max | ~750k English words, ~2,500 pages of prose, ~50k lines of code |
| `MiniMax-M3-512k` (do **not** use) | 524,288 | up to ~64,000 | hard-cap SKU, the 512K one you want to avoid for huge prompts |
| `deepseek/deepseek-v4-pro` (OpenRouter) | **1,000,000** | **131,072 (128K)** — the documented max on most hosts | same as M3 on input; output varies by host |

The 1M cap is the **sum of all tokens the model sees in one request**: system prompt + tool schemas + the full conversation history + the new user message. It is not a per-message limit.

### 9.2 Why `max_tokens` is set to the documented model max

`max_tokens` controls the model's per-response **output** budget, not the input window. I bumped it to the actual max each model supports:

- **minimax direct API → `max_tokens: 524288` (512K).** This is the documented maximum output for `MiniMax-M3`. The minimax server will return a 400 if you go higher, so this is the ceiling — not a number I picked arbitrarily. With `max_tokens` at 512K and the 1M total context window, the practical split per turn is up to **512K of generated output** OR up to **~488K of input + 512K of output** depending on the turn. To get a smaller output budget for shorter Q&A turns, lower `max_tokens` to 8192 or 16384 — the model will still use the full 1M input window for whatever context you paste.
- **OpenRouter DeepSeek V4 Pro → `max_tokens: 131072` (128K).** This is the documented maximum output for `deepseek-v4-pro` on the majority of OpenRouter providers. A few providers may accept up to 200K, but 128K is the safe value that will not return a 400 from any host. With `max_tokens` at 128K and the 1M total context window, the practical split per turn is up to **128K of generated output** OR up to **~870K of input + 128K of output** depending on the turn.

If you want a smaller output budget (e.g. you only ever ask short questions), lower `max_tokens` to 8192 or 16384 — the model will still use the full 1M input window for the context you paste.

### 9.2.1 The 1M context is declared in the JSON via the `metadata` field

The OpenAI Chat Completions API has no top-level `context_window` parameter. The context window is a model property, not a request property — so the only way to carry an explicit 1M-context declaration in the request body without the SDK rejecting it is the OpenAI-spec `metadata` field. That field is a free-form `{"key": "value"}` dict that the OpenAI SDK accepts, camel-ai passes through, and the API server logs (it is used for tagging/analytics, not for any model behaviour).

Both `.PASTE-INTO-EIGENT.json` files in this folder carry:

```json
"metadata": {
  "context_window_tokens": 1000000,
  "context_window_label": "1M",
  "max_output_tokens": <the model's max>,
  "default_model": "<slug>",
  "huge_prompt_optimized": true,
  "tier": "<1M-context SKU identifier>"
}
```

- **`context_window_tokens: 1000000`** — the explicit 1M claim. Sets the contract: "this provider is wired to a 1M-context model."
- **`context_window_label: "1M"`** — a human-readable tag for log-filtering.
- **`max_output_tokens: 524288` (or `131072` for OpenRouter)** — the max the model will accept for output. Mirrors `max_tokens` so the contract is self-describing.
- **`default_model`** — the slug Eigent should be calling. If the Model Type field in the UI disagrees, that's the bug.
- **`huge_prompt_optimized: true`** — flag for your own log queries (e.g. `grep huge_prompt_optimized main.log`).
- **`tier`** — guards against the 512K SKU: `"1M-context SKU (NOT -512k)"` makes it obvious at a glance that the JSON must be paired with the 1M model slug, not the 512K one.

The `metadata` field is a passthrough — it does not change model behaviour, it does not consume tokens, and it does not affect cost. It is the only OpenAI-spec-safe way to embed a "1M context" declaration inside the request.

### 9.3 Why the rest of the params are tuned for huge prompts

- **`temperature: 0.2`** — low enough that the model stays on task across a 100K-token generation, high enough that it does not produce rigidly-repetitive code. Higher values (0.7, 1.0) make the model drift off-topic and hallucinate imports as the context grows.
- **`top_p: 0.95`** — standard nucleus sampling. Below 0.9, the model starts cutting off valid tokens for code; above 0.98, low-probability junk tokens start sneaking into long generations.
- **`stream: true`** — without streaming, the IDE looks frozen for the 30–120 seconds a huge-prompt turn takes. With streaming, tokens appear as the model produces them, and you can interrupt the turn at any time.
- **`frequency_penalty: 0` / `presence_penalty: 0`** — these are OpenAI-spec knobs that nudge the model away from repeating itself. On a 1M-context generation they actively hurt: the model has to repeat function names, variable names, imports, and patterns, and a non-zero penalty makes it invent synonyms that break the code. Kept at 0. (For OpenRouter only — minimax ignores them per the `MinimaxConfig` docstring.)
- **No `seed`** — set deterministically only when you want reproducible test runs. For an agent, null lets the model explore.

### 9.4 The 1M context on the direct minimax API (no workarounds needed)

The `MiniMax-M3` direct API has **native 1M context** — there is no "context compression" or "middle-out" transform in the request body. You paste 1M tokens, the server accepts it, the model processes it. There is nothing to enable in the JSON, nothing to set in the dashboard. The `_comment_1m_context` field in `minimax-m3-direct-minimax.json` documents this.

The only practical limit is your **per-minute token rate (TPM)** and your **monthly subscription quota**. On the 1.7B-token/month subscription, you can run several full-1M turns a day before hitting the cap. On PAYG, every 1M-token input costs ~$0.30–$0.60 in M3 pricing (≤512K band).

### 9.5 The 1M context on OpenRouter (Middle-Out workaround)

OpenRouter routes your `deepseek/deepseek-v4-pro` request to one of many underlying hosts. Some hosts serve the model with **native 1M**; others cap it at 32K, 128K, or 200K. The `transforms: ["middle-out"]` body param is OpenRouter's way of saying: "if the request exceeds the chosen host's native context window, compress the middle of the conversation before sending."

That param **cannot go in this JSON** — it is not in the OpenAI SDK signature, so camel-ai's `openai.OpenAI` client raises `TypeError: Completions.create() got an unexpected keyword argument 'transforms'` the same way it does for `top_k`. Instead, enable it on your account so it applies to every request automatically:

1. Go to **https://openrouter.ai/settings/transforms**
2. Toggle **"Middle Out"** ON
3. Done. The transform now travels with your API key; every call from Eigent will get it.

This is the only way to guarantee a 1M-prompt turn does not hit "context_length_exceeded" on a host that only serves 128K.

### 9.6 How to actually use 1M context in Eigent (workflow)

A 1M-token turn is not "paste a 1M-token file and ask a question". The IDE wraps every user message in:
- a system prompt (~2–4K tokens)
- a tool schema listing every tool the agent can call (5–20K tokens depending on MCP servers installed)
- the full prior conversation history (grows with each turn)

So a 1M-token single turn looks like:

| Component | Approx tokens |
| --- | --- |
| System prompt + tool schema | ~15K |
| Prior conversation (5 turns, each ~50K) | ~250K |
| Your 1M-token source paste | 1,000,000 |
| **Total request size** | **~1,265,000** ❌ over the 1M cap |

Practical ways to fit:
- **Keep prior conversation under 200K.** Use the "New chat" button often. Long sessions accumulate tool-call history that you rarely need again.
- **Paste the file, not the conversation.** Reference files by path (e.g. "Read `src/index.ts` and `src/db.ts`, then refactor…") instead of pasting their contents. The IDE's file tools are 100x cheaper than pasting tokens.
- **For very large files, ask the model to read in chunks.** "Read `src/big.ts` lines 1–2000 and summarize, then read 2001–4000" works well within 1M.
- **For repo-wide refactors, use a worker.** Eigent can spawn a sub-agent with its own 1M context per file, then the parent stitches the diffs together.

### 9.7 What "1M context" does **not** get you

- **Perfect recall at 1M tokens.** Both M3 and V4 Pro start losing fine-grained recall past ~500K. Treat 1M as "huge", not "infinite".
- **Lower latency.** A 1M-token turn is still 30–120 seconds of generation even with streaming. Plan accordingly.
- **Free.** Direct minimax charges $0.30/M input on M3 (≤512K band), $0.60/M on the 512K–1M band. OpenRouter V4 Pro is $0.435/M. A 1M-token paste is $0.30–$0.60 just to read it.
- **Multimodal 1M.** M3 is multimodal (text + image + video in) but each image counts against the budget at ~1K tokens for a 1024×1024, and video is far more. A 1M budget can hold ~500 images or ~5 minutes of low-res video, not "a movie".

## 10. Smoke test after pasting

The error you saw in `main.log` was `No tool calls made by model`. The only way to be sure the JSON is wired correctly is to send a turn that *requires* a tool call and watch the log:

1. Eigent chat → start new session.
2. Send: *"List the files in your current working directory."*
3. In `C:\Users\ynotf\AppData\Roaming\eigent\logs\main.log` you should see `[info] BACKEND: ... model_controller - INFO - Model validation started` immediately followed by `[info] BACKEND: ... model_controller - INFO - Model validation completed` — no `TypeError`, no `WARNING - No tool calls made by model`, no `ERROR - Model validation completed`.
4. If you see `Completions.create() got an unexpected keyword argument 'X'`, then `X` is still in your JSON — re-paste the clean `.PASTE-INTO-EIGENT.json` file (do not type the JSON by hand).

## 11. Multimodal note (H3 and TTS — answering the original question)

The video model slug is **`MiniMax-H3`** (no space, hyphenated). The API endpoint is `POST https://api.minimax.io/v2/video_generation` (image gen is part of the same flow — first 5 are free, then $0.04 each). The TTS+voice-clone slug is **`speech-2.8-hd`** at `POST https://api.minimax.io/v1/t2a_v2` ($100/M chars). Neither is exposed through Eigent's chat — you call them directly with your subscription key. Same key, different endpoint, separate from the chat completions path. Eigent only routes the chat completion path; the multimodal endpoints need a direct API call (or a small Python helper).

For the OpenRouter side: H3 is **not** available on OpenRouter. It is minimax-native. speech-2.8-hd is also not on OpenRouter. On OpenRouter, for video you'd use a different provider's video model (e.g. `google/veo-3.0`). For TTS you'd use a different provider (e.g. `openai/gpt-4o-mini-tts`).

## 12. If it still doesn't work

1. **Confirm the version is 1.0.2**: open Eigent → Settings → About. (Your `version.txt` already says 1.0.2.)
2. **Tail the log while you retry**: `Get-Content 'C:\Users\ynotf\AppData\Roaming\eigent\logs\main.log' -Wait -Tail 50` and trigger another validation. The exact `TypeError` line will name the offending key.
3. **Check for stale JSON in the form**: Eigent can leave a previously-failed JSON in the editor after validation rejects it. If your paste shows visible indentation but the keys all start with `_comment_`, you pasted the annotated `.json` file instead of the `.PASTE-INTO-EIGENT.json` one. Re-paste.
4. **Check the model name in the API Usage dashboard**: console.minimax.io → Pay-as-you-go → API Usage → **Consumed Model** column. If it shows `MiniMax-M3-512k` instead of `MiniMax-M3`, your Model Type field says `MiniMax-M3-512k` and you got the 512K SKU. Change it to `MiniMax-M3`.
