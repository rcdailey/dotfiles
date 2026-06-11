import type { Plugin } from "@opencode-ai/plugin";

export const Notify: Plugin = async ({ $ }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.idle") {
        await $`notify-send "OpenCode" "Session idle"`;
      } else if (event.type === "permission.asked") {
        await $`notify-send -u critical "OpenCode" "Permission requested"`;
      }
    },
  };
};
