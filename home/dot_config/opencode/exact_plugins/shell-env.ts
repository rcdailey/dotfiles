import type { Plugin } from "@opencode-ai/plugin";

export const ShellEnv: Plugin = async () => {
  const agents = new Map<string, string>();
  const budgetedAgents = new Set(["acceptance", "researcher", "reviewer", "upgrade-analyst"]);

  return {
    "chat.params": async (input) => {
      agents.set(input.sessionID, input.agent);
    },
    "shell.env": async (input, output) => {
      if (input.sessionID && budgetedAgents.has(agents.get(input.sessionID) ?? "")) {
        output.env.RESEARCH_SESSION_ID = input.sessionID;
      }
    },
  };
};
