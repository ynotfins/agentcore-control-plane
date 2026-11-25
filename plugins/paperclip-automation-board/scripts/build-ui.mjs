import * as esbuild from 'esbuild';
import { createPluginBundlerPresets } from '@paperclipai/plugin-sdk/bundlers';

const presets = createPluginBundlerPresets({ uiEntry: 'ui/index.tsx', outdir: 'dist' });
if (!presets.esbuild?.ui) {
  throw new Error('UI bundler preset missing');
}
// The SDK preset leaves jsx at esbuild's classic default, which emits
// React.createElement without importing React. Plugin UI modules run inside the
// host page with only the specifiers in the preset's external list rewritten, so
// a bare `React` reference throws at render and the host shows
// "<plugin>: failed to render". Use the automatic runtime the host already maps.
await esbuild.build({ ...presets.esbuild.ui, jsx: 'automatic' });
console.log('UI bundle written to dist/ui');
