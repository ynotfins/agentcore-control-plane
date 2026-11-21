import * as esbuild from 'esbuild';
import { createPluginBundlerPresets } from '@paperclipai/plugin-sdk/bundlers';

const presets = createPluginBundlerPresets({ uiEntry: 'ui/index.tsx', outdir: 'dist' });
if (!presets.esbuild?.ui) {
  throw new Error('UI bundler preset missing');
}
await esbuild.build(presets.esbuild.ui);
console.log('UI bundle written to dist/ui');
