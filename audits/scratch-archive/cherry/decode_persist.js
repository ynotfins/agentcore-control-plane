// Decode and pretty-print the persist:cherry-studio value to confirm encoding.
const fs = require('node:fs')
const path = require('node:path')
const { Level } = require('level')

const SIBLING_MODULES = path.join(__dirname, 'node_modules')
if (fs.existsSync(SIBLING_MODULES)) {
  module.paths.unshift(SIBLING_MODULES)
}

const LDB = path.join(process.env.APPDATA || '', 'CherryStudio', 'Local Storage', 'leveldb')

;(async () => {
  const db = new Level(LDB, { valueEncoding: 'binary' })
  await db.open()
  for await (const [k, v] of db.iterator()) {
    const keyStr = k.toString('utf8')
    if (!keyStr.includes('persist:cherry-studio')) continue
    console.log('key=', JSON.stringify(keyStr))
    console.log('raw_len=', v.length, 'first_bytes=', Array.from(v.slice(0, 16)).map((b) => b.toString(16).padStart(2, '0')).join(' '))
    // try utf16le decode
    const body = v[0] === 0x00 ? v.slice(1) : v
    const utf16 = body.toString('utf16le')
    console.log('utf16le_len=', utf16.length)
    // show the first 2000 chars
    console.log('--- utf16 preview (first 2000 chars) ---')
    console.log(utf16.slice(0, 2000))
    console.log('--- end preview ---')
    // try parsing it as JSON
    try {
      const obj = JSON.parse(utf16)
      console.log('JSON.parse OK; top-level keys:', Object.keys(obj))
      if (obj.llm) {
        let llm = obj.llm
        if (typeof llm === 'string') {
          try { llm = JSON.parse(llm) } catch (e) { console.log('llm second-level parse failed:', e.message) }
        }
        if (llm && typeof llm === 'object') {
          console.log('llm keys:', Object.keys(llm))
          console.log('llm.providers count:', (llm.providers || []).length)
          console.log('llm.defaultModel:', llm.defaultModel)
          console.log('llm.topicNamingModel:', llm.topicNamingModel)
          console.log('llm.translateModel:', llm.translateModel)
          console.log('llm.quickModel:', llm.quickModel)
          // show enabled providers with apiKey lengths
          const enabled = (llm.providers || []).filter((p) => p.enabled && p.apiKey)
          console.log('enabled_with_keys:', enabled.map((p) => ({ id: p.id, key_len: p.apiKey.length, model_count: (p.models || []).length })))
        }
      }
    } catch (e) {
      console.log('JSON.parse failed:', e.message)
    }
  }
  await db.close()
})().catch((e) => {
  console.error('FATAL', e && e.stack ? e.stack : e)
  process.exit(1)
})
