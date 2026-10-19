import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

// Shared helper, not an extension: pi loads only top-level files and index.ts subdirectories.
//
// Subagent children re-run every extension's hooks, but they talk to a parent model, not the
// user. Subagent packages announce each in-process child on the parent's event bus (the
// pi-permission-system integration contract) before the child binds extensions. Each session has
// its own bus, so the ids live in a process-global set the child's extension instance can read.
// Out-of-process children carry PI_SUBAGENT_PARENT_SESSION instead.

const registry = globalThis as Record<symbol, Set<string> | undefined>;
const key = Symbol.for("pi-agent.subagent-children");
const children = registry[key] ?? new Set<string>();
registry[key] = children;

/** Records child sessions announced on this session's bus; call once per extension. */
export function trackSubagentChildren(pi: ExtensionAPI) {
  pi.events.on("subagents:child:session-created", (data) => {
    children.add((data as { sessionId: string }).sessionId);
  });
  pi.events.on("subagents:child:disposed", (data) => {
    children.delete((data as { sessionId: string }).sessionId);
  });
}

export function isSubagentChild(ctx: ExtensionContext): boolean {
  return (
    Boolean(process.env.PI_SUBAGENT_PARENT_SESSION) ||
    children.has(ctx.sessionManager.getSessionId())
  );
}
