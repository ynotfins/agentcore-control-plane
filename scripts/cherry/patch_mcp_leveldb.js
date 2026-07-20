#!/usr/bin/env node
/**
 * Governed Cherry Studio LevelDB MCP patcher.
 * Writes exactly one active agentcore-gateway streamableHttp entry into
 * persist:cherry-studio → mcp.servers. Never prints the virtual key.
 *
 * Usage:
 *   node patch_mcp_leveldb.js --dry-run
 *   node patch_mcp_leveldb.js --confirm
 *   node patch_mcp_leveldb.js --inspect
 */
'use strict'

const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const { execSync } = require('node:child_process')

const localModules = path.join(__dirname, 'node_modules')
if (fs.existsSync(localModules)) module.paths.unshift(localModules)
const siblingModules = path.join(__dirname, '_node_workspace', 'node_modules')
if (fs.existsSync(siblingModules)) module.paths.unshift(siblingModules)

const { ClassicLevel } = require('classic-level')
const Level = ClassicLevel

const APPDATA = process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming')
const CHERRY_ROOT = path.join(APPDATA, 'CherryStudio')
const LDB_DIR = path.join(CHERRY_ROOT, 'Local Storage', 'leveldb')
const GATEWAY_NAME = 'agentcore-gateway'
const GATEWAY_URL = 'http://127.0.0.1:8080/mcp'
const TIMEOUT_SEC = 300
const REDUX_VERSION = 208
const FORBIDDEN_NAMES = [
  'agentcore-memory',
  'arabold-docs',
  'depwire',
  'tentra',
  'serena',
  'sequential-thinking',
  'playwright',
  'filesystem',
  'openrouter',
  'swarmrecall',
  'swarmvault',
  'swarmclaw',
  'openclaw',
  'clawx',
]
const VALUE_TYPE_STRING = 0x00

function parseArgs(argv) {
  const out = { confirm: false, dryRun: false, inspect: false }
  for (const a of argv.slice(2)) {
    if (a === '--confirm') out.confirm = true
    else if (a === '--dry-run') out.dryRun = true
    else if (a === '--inspect') out.inspect = true
    else if (a === '-h' || a === '--help') {
      console.log('Usage: node patch_mcp_leveldb.js [--inspect|--dry-run|--confirm]')
      process.exit(0)
    } else {
      console.error('unknown arg', a)
      process.exit(64)
    }
  }
  if (!out.confirm && !out.dryRun && !out.inspect) out.dryRun = true
  return out
}

function userEnv(name) {
  const v = process.env[name]
  if (v && v.length) return v
  if (process.platform === 'win32') {
    try {
      const out = execSync(
        `powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable('${name}','User')"`,
        { encoding: 'utf8' }
      )
      return out.trim()
    } catch (_) {
      return ''
    }
  }
  return ''
}

function cherryRunning() {
  const lock = path.join(CHERRY_ROOT, 'lockfile')
  if (fs.existsSync(lock)) return true
  if (process.platform === 'win32') {
    try {
      const out = execSync('tasklist /FI "IMAGENAME eq Cherry Studio.exe"', { encoding: 'utf8' })
      return out.includes('Cherry Studio.exe')
    } catch (_) {
      return false
    }
  }
  return false
}

function encodeValue(s) {
  return Buffer.concat([Buffer.from([VALUE_TYPE_STRING]), Buffer.from(s, 'utf16le')])
}

function decodeValue(buf) {
  if (!buf || buf.length === 0) return ''
  if (buf[0] === VALUE_TYPE_STRING) return buf.slice(1).toString('utf16le')
  return buf.toString('utf16le')
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

async function findPersistKeyBytes(db) {
  const keys = await db.keys({ reverse: false, limit: 200 }).all()
  for (const k of keys) {
    if (!k || k.length < 8) continue
    if (k.toString('utf8').endsWith('persist:cherry-studio')) return k
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

function sanitizeServers(servers) {
  return (servers || []).map((s) => {
    const auth = (s.headers && (s.headers.Authorization || s.headers.authorization)) || ''
    return {
      id: s.id,
      name: s.name,
      type: s.type,
      url: s.baseUrl || s.url || null,
      active: !!s.isActive,
      timeout: s.timeout,
      has_auth: !!auth,
      auth_env_placeholder: String(auth).includes('${env:'),
      auth_len: auth ? String(auth).length : 0,
      provider: s.provider || null,
    }
  })
}

function mergeMcp(currentMcp, gatewayServer) {
  const servers = Array.isArray(currentMcp.servers) ? currentMcp.servers.slice() : []
  const next = []
  let sawGateway = false
  for (const s of servers) {
    const id = s.id || s.name
    const name = String(s.name || id || '').toLowerCase()
    if (id === GATEWAY_NAME || name === GATEWAY_NAME) {
      if (!sawGateway) {
        next.push(gatewayServer)
        sawGateway = true
      }
      continue
    }
    // Keep built-in inactive inMemory servers; drop forbidden direct upstreams / swarm / shim.
    const url = String(s.baseUrl || s.url || '')
    if (url.includes(':8081/') || url.endsWith(':8081/mcp')) {
      continue
    }
    const isCherryBuiltin = name.startsWith('@cherry/')
    if (!isCherryBuiltin && FORBIDDEN_NAMES.some((f) => name === f || name.includes(f))) {
      continue
    }
    if (s.type === 'inMemory' && s.isActive) {
      next.push({ ...s, isActive: false })
      continue
    }
    next.push(s)
  }
  if (!sawGateway) next.push(gatewayServer)
  return {
    servers: next,
    isUvInstalled: currentMcp.isUvInstalled === true,
    isBunInstalled: currentMcp.isBunInstalled === true,
  }
}

function ensureMemoryOff(obj) {
  let memory = parseMaybe(obj.memory)
  if (!memory || typeof memory !== 'object') memory = {}
  memory.globalMemoryEnabled = false
  obj.memory = JSON.stringify(memory)
  return memory.globalMemoryEnabled
}

async function loadPersist(db) {
  const persistKeyBytes = await findPersistKeyBytes(db)
  if (!persistKeyBytes) throw new Error('persist:cherry-studio key not found')
  const currentRaw = await db.get(persistKeyBytes)
  const currentStr = decodeValue(currentRaw)
  const currentObj = JSON.parse(currentStr)
  let currentMcp = { servers: [], isUvInstalled: false, isBunInstalled: false }
  if (typeof currentObj.mcp === 'string' && currentObj.mcp.length > 0) {
    currentMcp = JSON.parse(currentObj.mcp)
  } else if (currentObj.mcp && typeof currentObj.mcp === 'object') {
    currentMcp = currentObj.mcp
  }
  return { persistKeyBytes, currentRaw, currentObj, currentMcp }
}

async function main() {
  const args = parseArgs(process.argv)
  if (!fs.existsSync(LDB_DIR)) {
    console.error('ERROR: leveldb missing at', LDB_DIR)
    process.exit(2)
  }
  if (!args.inspect && cherryRunning()) {
    console.error('ERROR: Cherry Studio is running. Fully quit it first.')
    process.exit(3)
  }

  const db = new Level(LDB_DIR, { valueEncoding: 'binary' })
  await db.open()
  try {
    const { persistKeyBytes, currentRaw, currentObj, currentMcp } = await loadPersist(db)
    const memory = parseMaybe(currentObj.memory) || {}
    const report = {
      schema: 'agentcore.cherry.mcp.patch.v1',
      generated_at: new Date().toISOString(),
      cherry_root: CHERRY_ROOT,
      servers: sanitizeServers(currentMcp.servers),
      globalMemoryEnabled: memory.globalMemoryEnabled === true,
      gateway_url_target: GATEWAY_URL,
    }
    if (args.inspect) {
      console.log(JSON.stringify(report, null, 2))
      return
    }

    const vk = userEnv('BIFROST_MCP_VIRTUAL_KEY')
    if (!vk) {
      console.error('ERROR: BIFROST_MCP_VIRTUAL_KEY not set')
      process.exit(4)
    }
    const gatewayServer = buildGatewayServer(vk)
    const nextMcp = mergeMcp(currentMcp, gatewayServer)
    currentObj.mcp = JSON.stringify(nextMcp)
    ensureMemoryOff(currentObj)
    if (currentObj._persist && typeof currentObj._persist === 'object') {
      currentObj._persist.version = REDUX_VERSION
    }
    const nextBuf = encodeValue(JSON.stringify(currentObj))
    const redacted = {
      ...gatewayServer,
      headers: { Authorization: 'Bearer ***' },
    }
    const writeReport = {
      ...report,
      gateway_server_redacted: redacted,
      servers_after: sanitizeServers(nextMcp.servers),
      size_bytes_before: currentRaw.length,
      size_bytes_after: nextBuf.length,
      dry_run: !args.confirm,
    }
    console.log(JSON.stringify(writeReport, null, 2))
    if (!args.confirm) {
      console.error('Refusing write without --confirm (dry-run only).')
      return
    }
    await db.put(persistKeyBytes, nextBuf)
    console.log('WRITE_COMPLETE gateway=', GATEWAY_NAME, 'url=', GATEWAY_URL)
  } finally {
    await db.close()
  }
}

main().catch((e) => {
  console.error('FATAL', e && e.stack ? e.stack : e)
  process.exit(1)
})
