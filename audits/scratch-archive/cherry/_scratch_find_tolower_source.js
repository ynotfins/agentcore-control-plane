/**
 * Sanitize-inspect assistants + any undefined model/provider refs that can crash Home.
 * Cherry must be quit.
 */
const path = require('path')
const { Level } = require('level')

const LDB = path.join(process.env.APPDATA, 'CherryStudio', 'Local Storage', 'leveldb')

function parseMaybe(x) {
  if (typeof x === 'string') {
    try {
      return JSON.parse(x)
    } catch {
      return x
    }
  }
  return x
}

function decode(buf) {
  const b = Buffer.from(buf)
  return (b[0] === 0x00 ? b.slice(1) : b).toString('utf16le')
}

;(async () => {
  const db = new Level(LDB, { valueEncoding: 'binary' })
  await db.open()
  for await (const [k, v] of db.iterator()) {
    if (!k.toString('utf8').includes('persist:cherry-studio')) continue
    const obj = JSON.parse(decode(v))
    const assistants = parseMaybe(obj.assistants) || {}
    const llm = parseMaybe(obj.llm) || {}
    const settings = parseMaybe(obj.settings) || {}
    const list = Array.isArray(assistants)
      ? assistants
      : Array.isArray(assistants.assistants)
        ? assistants.assistants
        : []
    const issues = []
    for (const a of list) {
      const model = a.model
      const modelType = typeof model
      const modelId =
        typeof model === 'string'
          ? model
          : model && typeof model === 'object'
            ? model.id
            : null
      const provider =
        typeof model === 'object' && model
          ? model.provider || model.providerId
          : typeof model === 'string' && model.includes(':')
            ? model.split(':')[0]
            : null
      const bad =
        model == null ||
        modelId == null ||
        modelId === undefined ||
        (typeof model === 'object' && (model.provider == null || model.id == null))
      if (bad || !provider) {
        issues.push({
          id: a.id,
          name: a.name,
          modelType,
          modelId: modelId ?? null,
          provider: provider ?? null,
          modelKeys: model && typeof model === 'object' ? Object.keys(model) : null,
          rawModelPreview:
            typeof model === 'string'
              ? model.slice(0, 80)
              : model && typeof model === 'object'
                ? { id: model.id, provider: model.provider, name: model.name }
                : model,
        })
      }
    }
    const providers = Array.isArray(llm.providers) ? llm.providers : []
    const enabledBroken = providers
      .filter((p) => p.enabled)
      .map((p) => ({
        id: p.id,
        name: p.name,
        hasApiKey: Boolean(p.apiKey && String(p.apiKey).length),
        modelCount: Array.isArray(p.models) ? p.models.length : 0,
        modelsUndefined: Array.isArray(p.models)
          ? p.models.filter((m) => !m || (typeof m === 'object' && !m.id)).length
          : null,
      }))
    console.log(
      JSON.stringify(
        {
          assistant_count: list.length,
          assistant_issues: issues,
          defaultAgent: settings.defaultAgent ?? null,
          defaultModel: llm.defaultModel ?? null,
          topicDefaultModel: settings.defaultModel ?? assistants.defaultModel ?? null,
          enabled_providers: enabledBroken,
          persist_top_keys: Object.keys(obj).slice(0, 40),
        },
        null,
        2
      )
    )
  }
  await db.close()
})().catch((e) => {
  console.error(String(e))
  process.exit(1)
})
