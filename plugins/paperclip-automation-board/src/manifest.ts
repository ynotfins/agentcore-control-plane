import type { PaperclipPluginManifestV1 } from '@paperclipai/plugin-sdk';
import { PLUGIN_ID } from './constants.js';

const manifest: PaperclipPluginManifestV1 = {
  id: PLUGIN_ID,
  apiVersion: 1,
  version: '0.1.0',
  displayName: 'AgentCore Automations',
  description: 'Scheduled-task silent-run health board with repair actions for AgentCore automation on this PC.',
  author: 'AgentCore',
  categories: ['automation'],
  capabilities: ['ui.page.register', 'ui.sidebar.register', 'api.routes.register'],
  entrypoints: { worker: './dist/worker.js', ui: './dist/ui' },
  apiRoutes: [
    // Board actors have no implicit company, so each route declares how the host
    // resolves one. Without this the host answers 400 before dispatch.
    { routeKey: 'catalog', method: 'GET', path: '/catalog', auth: 'board', capability: 'api.routes.register', companyResolution: { from: 'query', key: 'companyId' } },
    { routeKey: 'repair-silent', method: 'POST', path: '/repair/silent', auth: 'board', capability: 'api.routes.register', companyResolution: { from: 'query', key: 'companyId' } },
    { routeKey: 'repair-disable', method: 'POST', path: '/repair/disable', auth: 'board', capability: 'api.routes.register', companyResolution: { from: 'query', key: 'companyId' } },
  ],
  ui: {
    slots: [
      { type: 'page', id: 'automation-board', displayName: 'Automations', exportName: 'AutomationBoardPage', routePath: 'automations' },
      { type: 'sidebar', id: 'automations-nav', displayName: 'Automations', exportName: 'AutomationsSidebarLink' },
    ],
  },
};

export default manifest;
