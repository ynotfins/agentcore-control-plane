// Inject the AgentCore Bifrost gateway MCP server into Cherry Studio
// 1.9.12 Local Storage leveldb. Same encoding rules as the LLM
// injector (see inject_cherry_providers.js for full comments):
//
//   key   = "_file://" + 0x00 + 0x01 + "persist:cherry-studio"
//   value = 0x00 + UTF-16LE(JSON.stringify(outer))
//   outer.mcp = JSON.stringify({servers, isUvInstalled, isBunInstalled})
//
// Pre-conditions:
//   1. Cherry Studio is FULLY QUIT.
//   2. BIFROST_MCP_VIRTUAL_KEY is set in Windows User env.
//   3. The Bifrost gateway is healthy at http://127.0.0.1:8080/mcp.
//   4. Node 18+ on PATH; `level` v8.x in _node_workspace/node_modules.
//
// Usage:
//   node inject_cherry_mcp.js --dry-run
//   node inject_cherry_mcp.js --confirm
//   node inject_cherry_mcp.js --rollback
//
// Safety:
//   - --confirm required for writes.
//   - --dry-run shows the resulting mcp.servers array without writing.
//   - --rollback restores the latest LDB backup from E:\\AgentCore-Backups.

'use strict'

const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')

const SIBLING_MODULES = path.join(__dirname, '_node_workspace', 'node_modules')
if (fs.existsSync(SIBLING_MODULES)) module.paths.unshift(SIBLING_MODULES)
const { Level } = require('level')

const APPDATA = process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming')
const CHERRY_ROOT = path.join(APPDATA, 'CherryStudio')
const LDB_DIR = path.join(CHERRY_ROOT, 'Local Storage', 'leveldb')
const BACKUP_ROOT = 'E:\\AgentCore-Backups'

const GATEWAY_NAME = 'agentcore-gateway'
const GATEWAY_URL = 'http://127.0.0.1:8080/mcp'
const TIMEOUT_SEC = 300
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
          'Usage: node inject_cherry_mcp.js [--confirm] [--dry-run] [--rollback] [--report PATH]',
          '',
          '  --confirm   Required to actually write to the leveldb. Default is dry-run.',
          '  --dry-run   Read the current mcp slice, merge with the gateway entry, print the result.',
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

const VALUE_TYPE_STRING = 0x00

function encodeValue(s) {
  return Buffer.concat([Buffer.from([VALUE_TYPE_STRING]), Buffer.from(s, 'utf16le')])
}

function decodeValue(buf) {
  if (!buf || buf.length === 0) return ''
  if (buf[0] === VALUE_TYPE_STRING) return buf.slice(1).toString('utf16le')
  return buf.toString('utf16le')
}

async function findPersistKeyBytes(db) {
  const keys = await db.keys({ reverse: false, limit: 200 }).all()
  for (const k of keys) {
    if (!k || k.length < 8) continue
    const tail = k.toString('utf8')
    if (tail.endsWith('persist:cherry-studio')) return k
  }
  return null
}

function buildGatewayServer(vk) {
  return {
    id: GATEWAY_NAME,
    name: GATEWAY_NAME,
    type: 'streamableHttp',
    baseUrl: GATEWAY_URL,
    headers: { Authorization: `Bearer ${vk}` },
    timeout: TIMEOUT_SEC,
    provider: 'AgentCore',
    isActive: true,
    disabledTools: [],
  }
}

function mergeMcp(currentMcp, gatewayServer) {
  const servers = Array.isArray(currentMcp.servers) ? currentMcp.servers : []
  const byId = new Map(servers.map((s) => [s.id || s.name, s]))
  byId.set(GATEWAY_NAME, gatewayServer)
  // Remove any older agentcore-gateway duplicates (same name) so we converge.
  const merged = Array.from(byId.values()).filter((s, idx, arr) => {
    if ((s.id || s.name) !== GATEWAY_NAME) return true
    return arr.findIndex((x) => (x.id || x.name) === GATEWAY_NAME) === idx
  })
  return {
    servers: merged,
    isUvInstalled: currentMcp.isUvInstalled === true,
    isBunInstalled: currentMcp.isBunInstalled === true,
  }
}

async function inject({ dryRun, confirm, reportPath }) {
  if (!fs.existsSync(LDB_DIR)) {
    console.error('ERROR: leveldb not found at', LDB_DIR)
    process.exit(2)
  }
  if (cherryRunning()) {
    console.error('ERROR: Cherry Studio is running. Quit it first.')
    process.exit(3)
  }

  const vk = userEnv('BIFROST_MCP_VIRTUAL_KEY')
  if (!vk) {
    console.error('ERROR: BIFROST_MCP_VIRTUAL_KEY not set in Windows User env')
    process.exit(4)
  }
  const gatewayServer = buildGatewayServer(vk)

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

  let currentMcp = { servers: [], isUvInstalled: false, isBunInstalled: false }
  if (typeof currentObj.mcp === 'string' && currentObj.mcp.length > 0) {
    try {
      currentMcp = JSON.parse(currentObj.mcp)
    } catch (e) {
      console.warn('WARN: existing mcp slice did not parse; treating as empty.', e.message)
    }
  } else if (currentObj.mcp && typeof currentObj.mcp === 'object') {
    currentMcp = currentObj.mcp
  }

  const nextMcp = mergeMcp(currentMcp, gatewayServer)
  currentObj.mcp = JSON.stringify(nextMcp)
  if (currentObj._persist && typeof currentObj._persist === 'object') {
    currentObj._persist.version = REDUX_VERSION
  }

  const nextStr = JSON.stringify(currentObj)
  const nextBuf = encodeValue(nextStr)

  const redacted = JSON.parse(JSON.stringify(gatewayServer))
  redacted.headers = { Authorization: 'Bearer ***' }

  const report = {
    schema: 'agentcore.cherry.mcp.inject.v1',
    generated_at: new Date().toISOString(),
    cherry_root: CHERRY_ROOT,
    leveldb: LDB_DIR,
    persist_key_suffix: 'persist:cherry-studio',
    redux_version: REDUX_VERSION,
    gateway_name: GATEWAY_NAME,
    gateway_url: GATEWAY_URL,
    gateway_server_redacted: redacted,
    servers_added_or_updated: [GATEWAY_NAME],
    servers_preserved: (currentMcp.servers || []).map((s) => s.id || s.name).filter((id) => id !== GATEWAY_NAME),
    servers_total_after: nextMcp.servers.length,
    backup_source: findLatestBackup(),
    size_bytes_before: currentRaw.length,
    size_bytes_after: nextBuf.length,
    dry_run: !!dryRun,
  }
  if (reportPath) fs.writeFileSync(reportPath, JSON.stringify(report, null, 2))

  console.log('--- DRY RUN ---')
  console.log(JSON.stringify(report, null, 2))

  if (dryRun) {
    await db.close()
    return
  }
  if (!confirm) {
    console.error('Refusing to write without --confirm.')
    await db.close()
    process.exit(8)
  }

  await db.put(persistKeyBytes, nextBuf)
  await db.close()
  console.log('--- WRITE COMPLETE ---')
  console.log('gateway:', GATEWAY_NAME, '@', GATEWAY_URL)
  console.log('servers_total:', report.servers_total_after)
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
