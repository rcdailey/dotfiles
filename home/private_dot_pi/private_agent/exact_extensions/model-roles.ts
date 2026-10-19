import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import {
  loadRoleTable,
  providers,
  ROLE_PROVIDER,
  resolveRole,
  roleNames,
} from "./lib/model-roles.ts";
import { isSubagentChild, trackSubagentChildren } from "./lib/subagent-children.ts";

// Registers a virtual model `role/<name>` per role in settings.json `modelRoles`. Agent files select
// roles, never physical models; each request routes to the role's model for the provider of the
// root session's selected model.

export default function modelRoles(pi: ExtensionAPI) {
  trackSubagentChildren(pi);

  const record = (provider: string | undefined, ctx: ExtensionContext) => {
    if (provider && provider !== ROLE_PROVIDER && !isSubagentChild(ctx)) providers.root = provider;
  };
  pi.on("session_start", (_event, ctx) => record(ctx.model?.provider, ctx));
  pi.on("model_select", (event, ctx) => record(event.model.provider, ctx));

  // Emitted on the parent's bus before the child binds extensions.
  pi.events.on("subagents:child:session-created", (data) => {
    if (providers.root)
      providers.children.set((data as { sessionId: string }).sessionId, providers.root);
  });
  pi.events.on("subagents:child:disposed", (data) => {
    providers.children.delete((data as { sessionId: string }).sessionId);
  });

  const table = loadRoleTable();
  for (const role of roleNames(table)) {
    pi.registerVirtualModel({
      provider: ROLE_PROVIDER,
      id: role,
      name: `Role: ${role}`,
      route: (_request, ctx) => resolveRole(ctx, table, role),
    });
  }
}
