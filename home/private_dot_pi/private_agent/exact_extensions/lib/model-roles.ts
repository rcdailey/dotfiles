import {
  type ExtensionContext,
  getAgentDir,
  SettingsManager,
} from "@earendil-works/pi-coding-agent";

// Shared helper, not an extension: pi loads only top-level files and index.ts subdirectories.
//
// Roles (subagent types and compaction) map to a physical model and thinking level per provider,
// read from global settings.json `modelRoles`. The provider comes from the root session's
// selected model, so switching the main session's
// provider switches every role. Children run in the parent's process; the parent snapshots its
// provider for each child at spawn, so a mid-run switch never changes a running child's model.

export const ROLE_PROVIDER = "role";

export type ThinkingLevel = "off" | "minimal" | "low" | "medium" | "high" | "xhigh" | "max";

interface RoleModel {
  model: string;
  thinkingLevel?: ThinkingLevel;
}

/** provider -> role -> model. Malformed entries are dropped. */
export type RoleTable = Record<string, Record<string, RoleModel>>;

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

/** Reads `modelRoles` from global settings; pi reads it again on /reload. */
export function loadRoleTable(): RoleTable {
  const raw = SettingsManager.create(process.cwd(), getAgentDir()).getGlobalSettings() as Record<
    string,
    unknown
  >;
  const table: RoleTable = {};
  if (!isObject(raw.modelRoles)) return table;
  for (const [provider, roles] of Object.entries(raw.modelRoles)) {
    if (!isObject(roles)) continue;
    for (const [role, entry] of Object.entries(roles)) {
      if (!isObject(entry) || typeof entry.model !== "string") continue;
      table[provider] ??= {};
      table[provider][role] = {
        model: entry.model,
        thinkingLevel: entry.thinkingLevel as ThinkingLevel | undefined,
      };
    }
  }
  return table;
}

export const roleNames = (table: RoleTable) => [
  ...new Set(Object.values(table).flatMap(Object.keys)),
];

interface ProviderState {
  root?: string;
  children: Map<string, string>;
}

const registry = globalThis as Record<symbol, ProviderState | undefined>;
const key = Symbol.for("pi-agent.model-roles");
export const providers: ProviderState = registry[key] ?? { children: new Map() };
registry[key] = providers;

/** Provider whose role table applies to this session: its spawn snapshot, else the root's. */
export function providerFor(ctx: ExtensionContext): string {
  const provider = providers.children.get(ctx.sessionManager.getSessionId()) ?? providers.root;
  if (!provider) throw new Error("No root session provider recorded for role models");
  return provider;
}

/** Physical model and thinking level for a role; throws when the provider has no mapping. */
export function resolveRole(ctx: ExtensionContext, table: RoleTable, role: string) {
  const provider = providerFor(ctx);
  const entry = table[provider]?.[role];
  if (!entry) throw new Error(`No ${role} role model for provider ${provider}`);
  const model = ctx.modelRegistry.find(provider, entry.model);
  if (!model) throw new Error(`Unknown model ${provider}/${entry.model} for role ${role}`);
  return { model, thinkingLevel: entry.thinkingLevel };
}
