import type { Plugin } from "@opencode-ai/plugin";

export const ShellEnv: Plugin = async () => {
  const agents = new Map<string, string>();

  return {
    "chat.params": async (input) => {
      agents.set(input.sessionID, input.agent);
    },
    "shell.env": async (input, output) => {
      if (input.sessionID && agents.get(input.sessionID) === "researcher") {
        output.env.RESEARCH_SESSION_ID = input.sessionID;
      }
    },
  };
};
