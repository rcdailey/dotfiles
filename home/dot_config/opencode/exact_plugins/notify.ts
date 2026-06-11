import type { Plugin } from "@opencode-ai/plugin";

export const Notify: Plugin = async ({ client, $ }) => {
  // Only dispatched (headless) sessions notify; the dispatch zsh function sets this.
  if (!process.env["OPENCODE_DISPATCH"]) return {};

  return {
    event: async ({ event }) => {
      if (event.type !== "session.idle") return;

      const session = await client.session.get({
        path: { id: event.properties.sessionID },
      });
      if (session.data?.parentID) return; // subagent sessions stay silent

      await $`notify-send "OpenCode" "Dispatched session idle"`;
    },
  };
};
