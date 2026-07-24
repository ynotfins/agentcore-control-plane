/**
 * AgentCore Skills-Hub MCP wrapper — process-local home isolation.
 *
 * Sets process.env vars for the isolated skill root BEFORE the MCP server
 * module is imported. This ensures node:os.homedir() returns the isolated
 * path when skills-hub calls discoverSkills().
 *
 * Must be kept as an ESM module (.mjs) so that await import() is available
 * and the env mutation precedes module evaluation of the MCP entry point.
 *
 * Windows env var reads by node:os.homedir() (in priority order):
 *   USERPROFILE → HOMEDRIVE + HOMEPATH → os.tmpdir()
 *
 * Isolation root: H:\AgentRuntime\skills-hub\home
 * Scanned dirs:
 *   H:\AgentRuntime\skills-hub\home\.claude\skills
 *   H:\AgentRuntime\skills-hub\home\.cursor\skills
 *
 * NEVER write skills into C:\Users\ynotf\.cursor\skills or
 * C:\Users\ynotf\.claude\skills from Bifrost context.
 */

// Set process-local isolation vars BEFORE any module that calls homedir()
process.env.USERPROFILE = 'H:\\AgentRuntime\\skills-hub\\home';
process.env.HOME        = 'H:\\AgentRuntime\\skills-hub\\home';
process.env.HOMEDRIVE   = 'H:';
process.env.HOMEPATH    = '\\AgentRuntime\\skills-hub\\home';

// Dynamic import ensures env mutation precedes module-level side-effects
// in @skills-hub-ai/mcp that could call homedir() at import time.
await import('./node_modules/@skills-hub-ai/mcp/dist/index.js');
