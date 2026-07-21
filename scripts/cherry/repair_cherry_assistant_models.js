/**
 * Assign a valid chat model to every assistant topic missing model.
 * Also set assistant.model when missing. Keeps Global Memory off.
 * Cherry must be quit. Does not print secrets.
 *
 * Usage:
 *   node repair_cherry_assistant_models.js --inspect
 *   node repair_cherry_assistant_models.js --repair --confirm
 */
const fs = require('fs')
const path = require('path')
const { Level } = require('level')

const CHERRY_ROOT = path.join(process.env.APPDATA, 'CherryStudio')
const LDB_DIR = path.join(CHERRY_ROOT, 'Local Storage', 'leveldb')
const BACKUP_DIR = path.join(
  'E:\\AgentCore-Backups',
  `cherry-assistant-model-repair-${new Date().toISOString().replace(/[:.]/g, '').slice(0, 15)}`
)

const TARGET = {
  id: 'deepseek-v4-pro',
  provider: 'deepseek',
  name: 'deepseek-v4-pro',
  group: 'DeepSeek',
}

function parseArgs(argv) {
  return { inspect: argv.includes('--inspect'), repair: argv.includes('--repair'), confirm: argv.includes('--confirm') }
}
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
function encode(str) {
  return Buffer.concat([Buffer.from([0x00]), Buffer.from(str, 'utf16le')])
}
function cherryRunning() {
  try {
    const { execSync } = require('child_process')
    return execSync('tasklist /FI "IMAGENAME eq Cherry Studio.exe"', { encoding: 'utf8' }).includes(
      'Cherry Studio.exe'
    )
  } catch {
    return false
  }
}
function modelOk(m) {
  return m && typeof m === 'object' && typeof m.id === 'string' && m.id && typeof m.provider === 'string' && m.provider
}

async function main() {
  const args = parseArgs(process.argv)
  if (cherryRunning()) {
    console.error('ERROR: quit Cherry first')
    process.exit(3)
  }
  const db = new Level(LDB_DIR, { valueEncoding: 'binary' })
  await db.open()
  try {
    let key = null
    let raw = null
    for await (const [k, v] of db.iterator()) {
      if (k.toString('utf8').includes('persist:cherry-studio')) {
        key = k
        raw = v
        break
      }
    }
    if (!key) throw new Error('persist key missing')
    const obj = JSON.parse(decode(raw))
    const assistantsRoot = parseMaybe(obj.assistants)
    const llm = parseMaybe(obj.llm) || {}
    const providers = Array.isArray(llm.providers) ? llm.providers : []
    const deepseek = providers.find((p) => p.id === 'deepseek')
    if (!deepseek || !deepseek.enabled || !deepseek.apiKey) {
      throw new Error('deepseek provider not enabled with api key; refusing repair')
    }
    // Prefer model object from provider catalog if present
    let target = { ...TARGET }
    const catalog = (deepseek.models || []).find((m) => (typeof m === 'string' ? m : m?.id) === 'deepseek-v4-pro')
    if (catalog && typeof catalog === 'object') {
      target = {
        id: catalog.id,
        provider: catalog.provider || 'deepseek',
        name: catalog.name || catalog.id,
        group: catalog.group || 'DeepSeek',
      }
    }

    let fixedTopics = 0
    let fixedAssistants = 0
    const beforeMissing = []
    const fixList = (list) => {
      for (const asst of list || []) {
        if (!modelOk(asst.model)) {
          asst.model = { ...target }
          fixedAssistants += 1
        }
        for (const t of asst.topics || []) {
          if (!modelOk(t.model)) {
            beforeMissing.push({ assistant: asst.name, topic: t.name || t.id })
            t.model = { ...target }
            fixedTopics += 1
          }
        }
      }
    }
    fixList(assistantsRoot.assistants)
    if (assistantsRoot.defaultAssistant) {
      const d = assistantsRoot.defaultAssistant
      if (!modelOk(d.model)) {
        d.model = { ...target }
        fixedAssistants += 1
      }
      for (const t of d.topics || []) {
        if (!modelOk(t.model)) {
          beforeMissing.push({ assistant: 'defaultAssistant', topic: t.name || t.id })
          t.model = { ...target }
          fixedTopics += 1
        }
      }
    }

    const report = {
      schema: 'agentcore.cherry.assistant-model.repair.v1',
      generated_at: new Date().toISOString(),
      target_model: target,
      before_missing_count: beforeMissing.length,
      before_missing_sample: beforeMissing.slice(0, 15),
      fixed_topics: fixedTopics,
      fixed_assistants: fixedAssistants,
      dry_run: !(args.repair && args.confirm),
    }
    console.log(JSON.stringify(report, null, 2))

    if (!(args.repair && args.confirm)) return

    fs.mkdirSync(BACKUP_DIR, { recursive: true })
    fs.writeFileSync(path.join(BACKUP_DIR, 'persist-raw-before.bin'), Buffer.from(raw))
    fs.writeFileSync(
      path.join(BACKUP_DIR, 'assistants-before.json'),
      JSON.stringify(
        {
          note: 'models only; prompts truncated',
          assistants: (assistantsRoot.assistants || []).map((a) => ({
            id: a.id,
            name: a.name,
            model: a.model ?? null,
            topics: (a.topics || []).map((t) => ({ id: t.id, name: t.name, model: t.model ?? null })),
          })),
        },
        null,
        2
      )
    )

    obj.assistants = JSON.stringify(assistantsRoot)
    await db.put(key, encode(JSON.stringify(obj)))
    console.error('WROTE_ASSISTANT_MODELS_OK backup=' + BACKUP_DIR)
  } finally {
    await db.close()
  }
}

main().catch((e) => {
  console.error(String(e && e.stack ? e.stack : e))
  process.exit(1)
})
