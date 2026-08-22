import type { Plugin } from "@opencode-ai/plugin";

export const ShellEnv: Plugin = async () => {
  return {
    "shell.env": async (input, output) => {
      if (input.sessionID) {
        output.env.OPENCODE_SESSION_ID = input.sessionID;
      }
    },
  };
};
