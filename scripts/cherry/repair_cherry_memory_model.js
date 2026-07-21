/**
 * Inspect + optionally repair Cherry memoryConfig schema and report model health.
 * Does NOT print secrets. Requires Cherry quit.
 *
 * Usage:
 *   node repair_cherry_memory_model.js --inspect
 *   node repair_cherry_memory_model.js --repair --confirm
 */
const fs = require('fs')
const path = require('path')
const { Level } = require('level')

const CHERRY_ROOT = path.join(process.env.APPDATA, 'CherryStudio')
const LDB_DIR = path.join(CHERRY_ROOT, 'Local Storage', 'leveldb')
const AGENTS_DB = path.join(CHERRY_ROOT, 'Data', 'agents.db')
const BACKUP_DIR = path.join(
  'E:\\AgentCore-Backups',
  `cherry-memory-model-repair-${new Date().toISOString().replace(/[:.]/g, '').slice(0, 15)}`
)
const AGENT_ID = 'agentcore-workspace-agent'
const TARGET_MODEL = 'deepseek:deepseek-v4-pro' // enabled provider with key + chat model

function parseArgs(argv) {
  return {
    inspect: argv.includes('--inspect'),
    repair: argv.includes('--repair'),
    confirm: argv.includes('--confirm'),
  }
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

function decodeValue(buf) {
  const b = Buffer.isBuffer(buf) ? buf : Buffer.from(buf)
  if (b.length && b[0] === 0x00) {
    return b.slice(1).toString('utf16le')
  }
  return b.toString('utf16le')
}

function encodeValue(str) {
  return Buffer.concat([Buffer.from([0x00]), Buffer.from(str, 'utf16le')])
}

function cherryRunning() {
  try {
    const { execSync } = require('child_process')
    const out = execSync('tasklist /FI "IMAGENAME eq Cherry Studio.exe"', {
      encoding: 'utf8',
    })
    return out.includes('Cherry Studio.exe')
  } catch {
    return false
  }
}

function summarizeModel(m) {
  if (!m || typeof m !== 'object') return m
  return {
    id: m.id ?? null,
    name: m.name ?? null,
    provider: m.provider ?? m.providerId ?? null,
    group: m.group ?? null,
    keys: Object.keys(m).slice(0, 20),
  }
}

function schemaValidMemoryConfig(existing) {
  // Keep Global Memory OFF. Cherry's isModel() does `"provider" in obj` and throws
  // when embeddingModel/llmModel are undefined. Use explicit empty Model-shaped
  // stubs so the operator check is safe; do not attach API keys or enable memory.
  const stubModel = { id: '', provider: '', name: '' }
  const base =
    existing && typeof existing === 'object' && !Array.isArray(existing)
      ? { ...existing }
      : {}
  if (base.embeddingModel == null || typeof base.embeddingModel !== 'object') {
    base.embeddingModel = { ...stubModel }
  } else if (!('provider' in base.embeddingModel)) {
    base.embeddingModel = { ...stubModel, ...base.embeddingModel, provider: '' }
  }
  if (base.llmModel == null || typeof base.llmModel !== 'object') {
    base.llmModel = { ...stubModel }
  } else if (!('provider' in base.llmModel)) {
    base.llmModel = { ...stubModel, ...base.llmModel, provider: '' }
  }
  if (!('embeddingDimensions' in base)) base.embeddingDimensions = undefined
  if (!('customDimensions' in base)) base.customDimensions = undefined
  return base
}

async function findPersistKey(db) {
  for await (const [k] of db.iterator({ values: false })) {
    const s = k.toString('utf8')
    if (s.includes('persist:cherry-studio')) return k
  }
  return null
}

function inspectAgentsDb() {
  const Database = require('better-sqlite3')
  // fallback: use child python if better-sqlite3 missing
}

function inspectAgentsViaSqliteCli() {
  const { execFileSync } = require('child_process')
  // use python
}

async function main() {
  const args = parseArgs(process.argv)
  if (cherryRunning()) {
    console.error('ERROR: quit Cherry Studio first')
    process.exit(3)
  }
  if (!fs.existsSync(LDB_DIR)) {
    console.error('ERROR: missing leveldb', LDB_DIR)
    process.exit(2)
  }

  const db = new Level(LDB_DIR, { valueEncoding: 'binary' })
  await db.open()
  try {
    const key = await findPersistKey(db)
    if (!key) throw new Error('persist key missing')
    const raw = await db.get(key)
    const obj = JSON.parse(decodeValue(raw))
    const memory = parseMaybe(obj.memory) || {}
    const llm = parseMaybe(obj.llm) || {}
    const providers = Array.isArray(llm.providers) ? llm.providers : []

    const memConfig = memory.memoryConfig
    const report = {
      schema: 'agentcore.cherry.memory-model.repair.v1',
      generated_at: new Date().toISOString(),
      globalMemoryEnabled: memory.globalMemoryEnabled === true,
      memory_keys: Object.keys(memory),
      memoryConfig_typeof: typeof memConfig,
      memoryConfig_isNull: memConfig === null,
      memoryConfig_isUndefined: memConfig === undefined,
      memoryConfig_keys:
        memConfig && typeof memConfig === 'object' ? Object.keys(memConfig) : null,
      memoryConfig_summary: memConfig && typeof memConfig === 'object'
        ? {
            embeddingModel: summarizeModel(memConfig.embeddingModel),
            llmModel: summarizeModel(memConfig.llmModel),
            embeddingDimensions: memConfig.embeddingDimensions ?? null,
            customDimensions: memConfig.customDimensions ?? null,
          }
        : memConfig,
      llm_defaultModel: llm.defaultModel || null,
      enabled_providers_with_keys: providers
        .filter((p) => p.enabled && p.apiKey && String(p.apiKey).length > 0)
        .map((p) => ({
          id: p.id,
          name: p.name,
          modelCount: Array.isArray(p.models) ? p.models.length : 0,
          modelsSample: (p.models || [])
            .slice(0, 6)
            .map((m) => (typeof m === 'string' ? m : m?.id)),
        })),
      cherryin: (() => {
        const p = providers.find((x) => x.id === 'cherryin')
        return p
          ? {
              enabled: p.enabled,
              hasApiKey: Boolean(p.apiKey && String(p.apiKey).length),
              modelCount: Array.isArray(p.models) ? p.models.length : 0,
            }
          : null
      })(),
      deepseek: (() => {
        const p = providers.find((x) => x.id === 'deepseek')
        return p
          ? {
              enabled: p.enabled,
              hasApiKey: Boolean(p.apiKey && String(p.apiKey).length),
              models: (p.models || []).map((m) => (typeof m === 'string' ? m : m?.id)),
            }
          : null
      })(),
      minimax: (() => {
        const p = providers.find((x) => x.id === 'minimax')
        return p
          ? {
              enabled: p.enabled,
              hasApiKey: Boolean(p.apiKey && String(p.apiKey).length),
              models: (p.models || [])
                .slice(0, 8)
                .map((m) => (typeof m === 'string' ? m : m?.id)),
            }
          : null
      })(),
      recommended_agent_model: TARGET_MODEL,
    }

    // agents.db via python one-liner file already exists - read with child
    const { execFileSync } = require('child_process')
    try {
      const py = `
import json, os, sqlite3
from pathlib import Path
db=Path(os.environ['APPDATA'])/'CherryStudio'/'Data'/'agents.db'
con=sqlite3.connect(f'file:{db}?mode=ro', uri=True)
rows=[{'id':r[0],'name':r[1],'model':r[2],'mcps':r[3]} for r in con.execute('SELECT id,name,model,mcps FROM agents')]
print(json.dumps(rows))
`
      const out = execFileSync('python', ['-c', py], { encoding: 'utf8' })
      report.agents = JSON.parse(out)
    } catch (e) {
      report.agents_error = String(e.message || e)
    }

    if (args.inspect || !args.repair) {
      console.log(JSON.stringify(report, null, 2))
    }

    if (!args.repair) return

    fs.mkdirSync(BACKUP_DIR, { recursive: true })
    fs.writeFileSync(
      path.join(BACKUP_DIR, 'persist-memory-before.json'),
      JSON.stringify(
        {
          memory,
          note: 'provider secrets omitted; agents.db copied separately',
        },
        null,
        2
      )
    )
    try {
      fs.copyFileSync(AGENTS_DB, path.join(BACKUP_DIR, 'agents.db'))
    } catch (e) {
      console.error('WARN agents.db backup failed', String(e.message || e))
    }
    // Prefer keyed persist value backup over full LevelDB tree (LOCK can block cpSync).
    fs.writeFileSync(path.join(BACKUP_DIR, 'persist-raw-before.bin'), Buffer.from(raw))

    // Repair memory: keep globalMemoryEnabled false; ensure memoryConfig object exists
    const nextMemory = {
      ...memory,
      globalMemoryEnabled: false,
      memoryConfig: schemaValidMemoryConfig(memConfig),
      currentUserId: memory.currentUserId ?? 'default',
    }
    obj.memory = JSON.stringify(nextMemory)

    const nextBuf = encodeValue(JSON.stringify(obj))
    const writeReport = {
      ...report,
      backup_dir: BACKUP_DIR,
      memory_after: {
        globalMemoryEnabled: nextMemory.globalMemoryEnabled,
        memoryConfig: nextMemory.memoryConfig,
      },
      dry_run: !args.confirm,
    }
    console.log(JSON.stringify(writeReport, null, 2))

    if (!args.confirm) {
      console.error('Refusing LevelDB write without --confirm')
    } else {
      await db.put(key, nextBuf)
      console.error('WROTE_MEMORY_SCHEMA_OK')
    }

    // Repair agent model via python/sqlite
    if (args.confirm) {
      const pyFix = `
import json, os, sqlite3, time
from pathlib import Path
db=Path(os.environ['APPDATA'])/'CherryStudio'/'Data'/'agents.db'
con=sqlite3.connect(db)
cur=con.execute("SELECT id, model FROM agents WHERE id=?", ('${AGENT_ID}',))
row=cur.fetchone()
if not row:
    raise SystemExit('agent missing')
old=row[1]
now=time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
con.execute('UPDATE agents SET model=?, updated_at=? WHERE id=?', ('${TARGET_MODEL}', now, '${AGENT_ID}'))
con.commit()
print(json.dumps({'agent_id':'${AGENT_ID}','model_before':old,'model_after':'${TARGET_MODEL}'}))
con.close()
`
      const out2 = execFileSync('python', ['-c', pyFix], { encoding: 'utf8' })
      console.log(out2.trim())
      console.error('WROTE_AGENT_MODEL_OK')
    }
  } finally {
    await db.close()
  }
}

main().catch((e) => {
  console.error(String(e && e.stack ? e.stack : e))
  process.exit(1)
})
