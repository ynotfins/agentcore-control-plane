// Quick LDB introspection: print all keys (truncated) and decode values when they look like UTF-8 JSON.
const fs = require('node:fs')
const path = require('node:path')
const { Level } = require('level')

const SIBLING_MODULES = path.join(__dirname, 'node_modules')
if (fs.existsSync(SIBLING_MODULES)) {
  module.paths.unshift(SIBLING_MODULES)
}

const LDB = process.env.LDB || path.join(process.env.APPDATA || '', 'CherryStudio', 'Local Storage', 'leveldb')

;(async () => {
  const db = new Level(LDB, { valueEncoding: 'binary' })
  await db.open()
  let n = 0
  for await (const [k, v] of db.iterator()) {
    n++
    const keyStr = k.toString('utf8')
    let valPreview = ''
    if (v && v.length) {
      const b0 = v[0]
      const tail = v.slice(1)
      if (b0 === 0x00) {
        // string value
        const s = tail.toString('utf8')
        if (s.length > 200) valPreview = `str[${s.length}] ${s.slice(0, 80).replace(/\n/g, ' ')}...`
        else valPreview = `str ${s.replace(/\n/g, ' ')}`
      } else if (b0 === 0x01) {
        valPreview = `blob[${tail.length}]`
      } else {
        valPreview = `raw[${v.length}] first=${b0}`
      }
    } else {
      valPreview = '<empty>'
    }
    console.log(`#${n} key=${JSON.stringify(keyStr)} val=${valPreview}`)
  }
  await db.close()
  console.log('total_keys=', n)
})().catch((e) => {
  console.error('FATAL', e && e.stack ? e.stack : e)
  process.exit(1)
})
