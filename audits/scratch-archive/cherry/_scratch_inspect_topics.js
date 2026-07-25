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
    const a = parseMaybe(obj.assistants)
    const issues = []
    for (const asst of a.assistants || []) {
      const topics = asst.topics || []
      if (!topics.length) {
        issues.push({ assistant: asst.name, topicCount: 0 })
        continue
      }
      for (const t of topics) {
        const m = t.model
        const mid = typeof m === 'string' ? m : m && m.id
        const prov = typeof m === 'object' && m ? m.provider : null
        if (m == null || mid == null || (typeof m === 'object' && (prov == null || prov === undefined))) {
          issues.push({
            assistant: asst.name,
            topicId: t.id,
            topicName: t.name,
            hasModel: m != null,
            modelType: typeof m,
            modelId: mid ?? null,
            provider: prov,
            topicKeys: Object.keys(t).slice(0, 25),
          })
        }
      }
    }
    const sampleTopic = (((a.assistants || [])[0] || {}).topics || [])[0] || null
    let sample = null
    if (sampleTopic) {
      sample = {
        keys: Object.keys(sampleTopic),
        id: sampleTopic.id,
        name: sampleTopic.name,
        model: sampleTopic.model ?? null,
        promptLen: typeof sampleTopic.prompt === 'string' ? sampleTopic.prompt.length : null,
        messageCount: Array.isArray(sampleTopic.messages) ? sampleTopic.messages.length : null,
      }
    }
    console.log(
      JSON.stringify(
        {
          assistant_count: (a.assistants || []).length,
          issue_count: issues.length,
          issues: issues.slice(0, 40),
          sample_topic: sample,
          defaultAssistant_keys: a.defaultAssistant ? Object.keys(a.defaultAssistant) : null,
          defaultAssistant_model: a.defaultAssistant ? a.defaultAssistant.model ?? null : null,
          defaultAssistant_topics: a.defaultAssistant
            ? (a.defaultAssistant.topics || []).map((t) => ({
                id: t.id,
                name: t.name,
                model: t.model ?? null,
              }))
            : null,
        },
        null,
        2
      )
    )
  }
  await db.close()
})().catch((e) => {
  console.error(String(e && e.stack ? e.stack : e))
  process.exit(1)
})
