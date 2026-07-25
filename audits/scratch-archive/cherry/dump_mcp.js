// Dump the mcp slice from the persist key to understand the schema.
const fs = require('node:fs')
const path = require('node:path')
const { Level } = require('level')

const SIBLING_MODULES = path.join(__dirname, 'node_modules')
if (fs.existsSync(SIBLING_MODULES)) module.paths.unshift(SIBLING_MODULES)

const LDB = path.join(process.env.APPDATA || '', 'CherryStudio', 'Local Storage', 'leveldb')

;(async () => {
  const db = new Level(LDB, { valueEncoding: 'binary' })
  await db.open()
  for await (const [k, v] of db.iterator()) {
    const keyStr = k.toString('utf8')
    if (!keyStr.includes('persist:cherry-studio')) continue
    const body = v[0] === 0x00 ? v.slice(1) : v
    const utf16 = body.toString('utf16le')
    const obj = JSON.parse(utf16)
    if (typeof obj.mcp === 'string') {
      try {
        obj.mcp = JSON.parse(obj.mcp)
      } catch (e) {
        console.log('mcp second-level parse failed:', e.message)
      }
    }
    if (obj.mcp) {
      console.log('--- mcp slice ---')
      console.log('mcp type:', typeof obj.mcp, 'isArray:', Array.isArray(obj.mcp))
      if (obj.mcp && typeof obj.mcp === 'object') {
        console.log('mcp keys:', Object.keys(obj.mcp))
        if (Array.isArray(obj.mcp.servers)) {
          console.log('mcp.servers count:', obj.mcp.servers.length)
          for (const s of obj.mcp.servers) {
            console.log('  -', s.id || s.name, 'type=' + s.type, 'url=' + (s.baseUrl || s.url || '?'), 'active=' + s.isActive)
          }
        }
        if (obj.mcp.serversByName) {
          console.log('mcp.serversByName keys:', Object.keys(obj.mcp.serversByName))
        }
      }
    }
  }
  await db.close()
})().catch((e) => {
  console.error('FATAL', e && e.stack ? e.stack : e)
  process.exit(1)
})
