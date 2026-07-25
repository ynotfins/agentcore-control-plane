// Inject the AgentCore-generated provider list into Cherry Studio 1.9.12
// Local Storage leveldb under the `persist:cherry-studio` key.
//
// Storage layout (Chromium LocalStorage / Electron `localStorage`):
//   key   = "_file://" + 0x00 + 0x01 + "persist:cherry-studio"  (UTF-8 bytes)
//   value = 0x00  (type marker for plain string)
//         + UTF-16LE bytes of a JSON object whose top-level keys are
//           the redux-persist slice names. Each slice value is itself
//           a STRING containing a JSON-serialized LlmState (or
//           AssistantsState, etc.).
//
// Pre-conditions:
//   1. Cherry Studio is FULLY QUIT (no lockfile, no process).
//   2. The companion setup_cherry_providers.py script has produced
//      %APPDATA%\CherryStudio\Data\agentcore-cherry-providers-import.json
//   3. BIFROST_MCP_VIRTUAL_KEY is set in Windows User env so the
//      gateway MCP entry stays intact across the injection.
//   4. Node 18+ is on PATH and the local node_modules in this script's
//      _node_workspace has `level` v8.x installed.
//
// Effects:
//   - Reads `%APPDATA%\CherryStudio\Local Storage\leveldb` (LevelDB).
//   - Finds the persist key and replaces its `llm` slice with the
//     AgentCore-generated one, preserving every other slice verbatim.
//   - Re-encodes the value as 0x00 + UTF-16LE and writes it back.
//   - Optionally writes a JSON report to the same Data dir describing
//     the diff.
//
// Safety:
//   - --confirm flag is required for any non-dry-run write.
//   - --dry-run prints the resulting llm slice without writing.
//   - --rollback restores the latest backup created by
//     setup_cherry_providers.py.

'use strict'

const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')

// Resolve `level` from the sibling _node_workspace dir so the script
// works without a co-located node_modules.
const SIBLING_MODULES = path.join(__dirname, '_node_workspace', 'node_modules')
if (fs.existsSync(SIBLING_MODULES)) {
  module.paths.unshift(SIBLING_MODULES)
}
const { Level } = require('level')

const APPDATA = process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming')
const CHERRY_ROOT = path.join(APPDATA, 'CherryStudio')
const LDB_DIR = path.join(CHERRY_ROOT, 'Local Storage', 'leveldb')
const DATA_DIR = path.join(CHERRY_ROOT, 'Data')
const IMPORT_ARTIFACT = path.join(DATA_DIR, 'agentcore-cherry-providers-import.json')
const BACKUP_ROOT = 'E:\\AgentCore-Backups'

// Persist key with the Chromium LocalStorage prefix.
function persistKey() {
  return Buffer.concat([Buffer.from('_file://', 'utf8'), Buffer.from([0x00, 0x01]), Buffer.from('persist:cherry-studio', 'utf8')])
}

const REDUX_VERSION = 208

function parseArgs(argv) {
  const out = { confirm: false, dryRun: false, rollback: false, reportPath: null }
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--confirm') out.confirm = true
    else if (a === '--dry-run') out.dryRun = true
    else if (a === '--rollback') out.rollback = true
    else if (a === '--report') out.reportPath = argv[++i]
    else if (a === '-h' || a === '--help') {
      console.log(
        [
          'Usage: node inject_cherry_providers.js [--confirm] [--dry-run] [--rollback] [--report PATH]',
          '',
          '  --confirm   Required to actually write to the leveldb. Default is dry-run.',
          '  --dry-run   Read the current llm slice, merge with the import artifact, print the result.',
          '  --rollback  Replace the leveldb with the latest backup under E:\\AgentCore-Backups.',
          '  --report    Also write a JSON diff report to PATH.',
        ].join('\n')
      )
      process.exit(0)
    } else {
      console.error('unknown arg:', a)
      process.exit(64)
    }
  }
  return out
}

function userEnv(name) {
  const v = process.env[name]
  if (v && v.length) return v
  if (process.platform === 'win32') {
    try {
      const { execSync } = require('node:child_process')
      const out = execSync(`powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable('${name}','User')"`, { encoding: 'utf8' })
      const trimmed = out.trim()
      if (trimmed) return trimmed
    } catch (_) {
      // fall through
    }
  }
  return ''
}

function cherryRunning() {
  const lock = path.join(CHERRY_ROOT, 'lockfile')
  if (fs.existsSync(lock)) return true
  if (process.platform === 'win32') {
    try {
      const { execSync } = require('node:child_process')
      const out = execSync('tasklist /FI "IMAGENAME eq Cherry Studio.exe"', { encoding: 'utf8' })
      if (out.includes('Cherry Studio.exe')) return true
    } catch (_) {
      // ignore
    }
  }
  return false
}

function listBackups() {
  if (!fs.existsSync(BACKUP_ROOT)) return []
  return fs
    .readdirSync(BACKUP_ROOT)
    .filter((d) => d.startsWith('cherry-providers-'))
    .map((d) => path.join(BACKUP_ROOT, d, 'leveldb'))
    .filter((p) => fs.existsSync(p))
    .sort()
}

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true })
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, e.name)
    const d = path.join(dst, e.name)
    if (e.isDirectory()) copyDir(s, d)
    else fs.copyFileSync(s, d)
  }
}

async function rollbackLatest() {
  const candidates = listBackups()
  if (!candidates.length) {
    console.error('no backups found under', BACKUP_ROOT)
    process.exit(5)
  }
  const src = candidates[candidates.length - 1]
  console.log('rollback_source=', src)
  if (cherryRunning()) {
    console.error('ERROR: Cherry Studio is running. Quit it first.')
    process.exit(3)
  }
  if (fs.existsSync(LDB_DIR)) {
    fs.rmSync(LDB_DIR, { recursive: true, force: true })
  }
  copyDir(src, LDB_DIR)
  console.log('rollback_complete target=', LDB_DIR)
}

function findLatestBackup() {
  const candidates = listBackups()
  return candidates.length ? candidates[candidates.length - 1] : null
}

// Chromium LocalStorage value encoding:
//   byte 0  = 0x00 -> type: plain string
//   byte 0  = 0x01 -> type: blob
//   following bytes = UTF-16LE encoded string (NOT UTF-8)
const VALUE_TYPE_STRING = 0x00

function encodeValue(s) {
  const body = Buffer.from(s, 'utf16le')
  return Buffer.concat([Buffer.from([VALUE_TYPE_STRING]), body])
}

function decodeValue(buf) {
  if (!buf || buf.length === 0) return ''
  if (buf[0] === VALUE_TYPE_STRING) {
    return buf.slice(1).toString('utf16le')
  }
  // best-effort fallback
  return buf.toString('utf16le')
}

function findPersistKeyBytes(ldb) {
  // Walk the DB and return the bytes of the key that ends with
  // "persist:cherry-studio" (after the Chromium LocalStorage prefix).
  // The canonical key is _file:// + 0x00 + 0x01 + "persist:cherry-studio".
  return ldb.keys({ reverse: false, limit: 200 }).all().then((keys) => {
    for (const k of keys) {
      if (!k || k.length < 8) continue
      // The trailing UTF-8 of the key should end with "persist:cherry-studio"
      const tail = k.toString('utf8')
      if (tail.endsWith('persist:cherry-studio')) return k
    }
    return null
  })
}

function mergeLlm(currentLlm, payload, env) {
  // Strategy: ADD/UPDATE, not replace. The existing 60+ system
  // providers (cherryin, silicon, aihubmix, etc.) stay in the list with
  // their empty keys; we only UPSERT the providers listed in the import
  // payload, replacing any existing entry with the same id so re-runs
  // converge to the same state.
  const existing = Array.isArray(currentLlm.providers) ? currentLlm.providers : []
  const byId = new Map(existing.map((p) => [p.id, p]))
  for (const p of payload.providers) {
    const envVar = payload.api_keys_env[p.id]
    const apiKey = envVar ? env(envVar) : ''
    byId.set(p.id, { ...p, apiKey })
  }
  const merged = Array.from(byId.values())

  const next = { ...currentLlm }
  next.providers = merged

  if (payload.defaultModel) next.defaultModel = payload.defaultModel
  if (payload.topicNamingModel) next.topicNamingModel = payload.topicNamingModel
  if (payload.translateModel) next.translateModel = payload.translateModel
  if (payload.quickModel) next.quickModel = payload.quickModel

  return next
}

async function inject({ dryRun, confirm, reportPath }) {
  if (!fs.existsSync(LDB_DIR)) {
    console.error('ERROR: leveldb not found at', LDB_DIR)
    process.exit(2)
  }
  if (!fs.existsSync(IMPORT_ARTIFACT)) {
    console.error('ERROR: import artifact not found. Run setup_cherry_providers.py first.')
    process.exit(4)
  }
  if (cherryRunning()) {
    console.error('ERROR: Cherry Studio is running. Quit it first.')
    process.exit(3)
  }
  const importPayload = JSON.parse(fs.readFileSync(IMPORT_ARTIFACT, 'utf8'))

  const db = new Level(LDB_DIR, { valueEncoding: 'binary' })
  await db.open()

  const persistKeyBytes = await findPersistKeyBytes(db)
  if (!persistKeyBytes) {
    console.error('ERROR: could not find persist:cherry-studio key in LDB')
    await db.close()
    process.exit(6)
  }

  const currentRaw = await db.get(persistKeyBytes)
  const currentStr = decodeValue(currentRaw)
  let currentObj
  try {
    currentObj = JSON.parse(currentStr)
  } catch (e) {
    console.error('ERROR: persist key did not parse as JSON. Aborting.')
    await db.close()
    process.exit(7)
  }

  // The LlmState is double-encoded: currentObj.llm is a string of JSON.
  let currentLlm = {}
  if (typeof currentObj.llm === 'string' && currentObj.llm.length > 0) {
    try {
      currentLlm = JSON.parse(currentObj.llm)
    } catch (e) {
      console.warn('WARN: existing llm slice did not parse as JSON; treating as empty.', e.message)
      currentLlm = {}
    }
  } else if (currentObj.llm && typeof currentObj.llm === 'object') {
    currentLlm = currentObj.llm
  }

  const nextLlm = mergeLlm(currentLlm, importPayload, userEnv)
  currentObj.llm = JSON.stringify(nextLlm)
  // Bump redux-persist version in the outer _persist if present
  if (currentObj._persist && typeof currentObj._persist === 'object') {
    currentObj._persist.version = REDUX_VERSION
  }

  const nextStr = JSON.stringify(currentObj)
  const nextBuf = encodeValue(nextStr)

  const report = {
    schema: 'agentcore.cherry.inject.v1',
    generated_at: new Date().toISOString(),
    cherry_root: CHERRY_ROOT,
    leveldb: LDB_DIR,
    persist_key_suffix: 'persist:cherry-studio',
    redux_version: REDUX_VERSION,
    providers_added_or_updated: importPayload.providers.map((p) => p.id),
    providers_preserved: (currentLlm.providers || []).map((p) => p.id).filter((id) => !importPayload.providers.find((p) => p.id === id)),
    providers_total_after: null,
    defaultModel: importPayload.defaultModel,
    topicNamingModel: importPayload.topicNamingModel,
    translateModel: importPayload.translateModel,
    quickModel: importPayload.quickModel,
    policy_notes: importPayload.policy_notes,
    backup_source: findLatestBackup(),
    size_bytes_before: currentRaw.length,
    size_bytes_after: nextBuf.length,
    dry_run: !!dryRun,
    new_llm_providers: nextLlm.providers.map((p) => ({ id: p.id, name: p.name, enabled: p.enabled, model_count: p.models.length })),
    new_llm_providers_total: nextLlm.providers.length,
  }
  if (reportPath) {
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2))
  }

  console.log('--- DRY RUN ---')
  console.log(JSON.stringify(report, null, 2))

  if (dryRun) {
    await db.close()
    return
  }
  if (!confirm) {
    console.error('Refusing to write without --confirm. Re-run with --confirm to apply.')
    await db.close()
    process.exit(8)
  }

  await db.put(persistKeyBytes, nextBuf)
  await db.close()
  console.log('--- WRITE COMPLETE ---')
  console.log('providers_updated:', report.providers_added_or_updated.join(', '))
  console.log('defaultModel:', report.defaultModel)
  console.log('Size: %d -> %d bytes', report.size_bytes_before, report.size_bytes_after)
}

async function main() {
  const args = parseArgs(process.argv)
  if (args.rollback) {
    await rollbackLatest()
    return
  }
  await inject(args)
}

main().catch((e) => {
  console.error('FATAL', e && e.stack ? e.stack : e)
  process.exit(1)
})
