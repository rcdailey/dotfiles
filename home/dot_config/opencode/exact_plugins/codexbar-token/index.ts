import type { Plugin } from "@opencode/plugin";
import { codexbarConfigPath, syncToken } from "./sync.ts";

const SYNC_INTERVAL_MS = 60_000;

/**
 * Feeds CodexBar the Anthropic OAuth access token OpenCode already holds, so its Claude usage
 * view needs no Claude Code login. Resolving the credential lets OpenCode renew it when it is
 * within five minutes of expiry; the refresh token never leaves OpenCode.
 *
 * Runs only while a project location is loaded (see experimental.location_idle_timeout). After
 * a longer idle period CodexBar shows an expired token until OpenCode is used again.
 */
export const CodexbarToken = {
  id: "local.codexbar-token",
  setup(ctx) {
    const sync = async () => {
      const connection = await ctx.integration.connection.active("anthropic");
      if (!connection) return;
      const credential = await ctx.integration.connection.resolve(connection);
      if (credential?.type !== "oauth") return;
      syncToken(codexbarConfigPath(), credential.access, Date.now());
    };
    const tick = () => {
      sync().catch((error) => console.error("codexbar-token sync failed", error));
    };
    tick();
    const timer = setInterval(tick, SYNC_INTERVAL_MS);
    return () => clearInterval(timer);
  },
} satisfies Plugin.Plugin;

export default CodexbarToken;
