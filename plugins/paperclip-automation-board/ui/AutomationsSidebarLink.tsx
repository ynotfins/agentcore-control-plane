import type { PluginSidebarProps } from "@paperclipai/plugin-sdk/ui";
import { useHostContext, useHostNavigation } from "@paperclipai/plugin-sdk/ui";
import { PLUGIN_ID } from "./constants.js";

export function AutomationsSidebarLink(_props: PluginSidebarProps) {
  const context = useHostContext();
  const hostNavigation = useHostNavigation();
  const href = context.companyPrefix
    ? `/${context.companyPrefix}/plugins/${PLUGIN_ID}/automations`
    : `/plugins/${PLUGIN_ID}/automations`;
  return (
    <a {...hostNavigation.linkProps(href)} style={{ display: "block", padding: "8px 12px" }}>
      Automations
    </a>
  );
}
