# Cherry Studio Skills Audit

**Date:** 2026-07-19  
**Install root:** `%APPDATA%\CherryStudio\Data\Agents\w-default\.claude\skills\`  
**Policy:** Inspect before enable; reject authority-bypassing bundles; pin reproducible checksums; optional skills deferred until an active project justifies them  
**Uninstalls:** none

## Inventory (SKILL.md SHA-256)

| Skill | SHA-256 | Scripts present | Disposition |
| -- | -- | -- | -- |
| brainstorming | E14914605F640E0841758E45D0AB2A53243B59B921F929E47921C99668F2E61D | helper.js, start-server.sh, stop-server.sh | approved / hash-pinned; scripts not auto-run by AgentCore |
| diagnosing-bugs | 3DFE5EC16B89A01DBC1BF606A1A1CFC32349E225F3BB75A3FB86117974A83CB8 | hitl-loop.template.sh | approved / hash-pinned |
| executing-plans | BBD8D28BB655A52817CC129CE49F9E46FA7C6303F72ED5DE95BFE914EF8E0CE8 | none | approved / hash-pinned |
| find-skills | F03DD516D0276E6DAE5F62712FE90A3D22057DF615D47392382AEAB5AB948222 | none | **not catalog-admitted** — license unverified in SKILL.md; deferred until project justification + license proof |
| playwright-skill | 855CD6515F617895AC3A32752D8928BB9D2311D3BC1E4BA876A3EB1AA96F4C35 | none | approved / v2.4.0 + hash |
| requesting-code-review | 1017CCDD5BC61FAB67C654CF118CBDB520464B313073A0A6B9A6B9AA647A3AD6 | none | approved / hash-pinned |
| skill-creator | C6A49624F0DBA126AF43ACD13C32DC32E4AC68ACE671659EBB7D3EFBBA8E8AB9 | multiple Python eval scripts | approved / hash-pinned; eval scripts operator-gated |
| systematic-debugging | 3B20719ECA4F0461CB51A195221320D775DCF03B6859271066A03A5132A6CE7A | find-polluter.sh | approved / hash-pinned |
| test-driven-development | B5B4717B8B761CCE15A6CFE9022E33FD959E0894C0C39D72C9CB49C23486C10E | none | approved / hash-pinned |
| using-superpowers | 55379FE7C1C473A02C61961C822996BFF30E1320D6921D9062509BC508482C05 | none | approved / hash-pinned |
| vercel-composition-patterns | E38E0EAA609316B10423A9A138ED95E35099ACCD3F735585295C8A8F165C28A3 | none | approved / v1.0.0 + hash |
| vercel-react-best-practices | 71ED7794962FA6E803EE83030517B5B93A9F70FBFEB431EC4535C5480A8D8355 | none | approved / v1.0.0 + hash |
| verification-before-completion | EA52D15AABAF72BC6B558EFE2C126F161B53961090DDCD712000273BFE8C7B6C | none | approved / hash-pinned |
| writing-plans | 272E1AF349F5062C28DC282B3E21B220D58D683A7314A10C455B7432EC91D845 | none | approved / hash-pinned |

## Authority checks

- No skill grants Bifrost admin, OpenRouter OAuth, or direct PostgreSQL credentials.
- Skills are procedural guidance inside Cherry agents; AgentCore memory remains the ten-tool gateway surface.
- Catalog `version_policy: latest` entries for obra/superpowers, mattpocock diagnosing-bugs, and anthropics skill-creator were corrected to `pinned-by-content-hash`.

## Extension security monitor (adjacent)

Report-only run 2026-07-19: `critical=0`, `high=2` (mavis-trash.js encoded-command patterns under `.mavis`/`.minimax` bins — outside Cherry skills; no destructive action taken).

## Status

`CHERRY SKILLS AUDITED — HASH-PINNED; NO AUTHORITY BYPASS DETECTED`
