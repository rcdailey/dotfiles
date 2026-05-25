import type { Plugin } from "@opencode-ai/plugin";

// RTK OpenCode plugin: rewrites bash commands to use rtk for token savings.
// All rewrite logic lives in `rtk rewrite` (the Rust binary's pattern registry).
// Based on: https://github.com/rtk-ai/rtk/blob/develop/hooks/opencode/rtk.ts

export const RtkRewrite: Plugin = async ({ $ }) => {
  try {
    await $`which rtk`.quiet();
  } catch {
    console.warn("[rtk] rtk binary not found in PATH -- plugin disabled");
    return {};
  }

  return {
    "tool.execute.before": async (input, output) => {
      const tool = String(input?.tool ?? "").toLowerCase();
      if (tool !== "bash" && tool !== "shell") return;

      const args = output?.args;
      if (!args || typeof args !== "object") return;

      const command = (args as Record<string, unknown>).command;
      if (typeof command !== "string" || !command) return;

      // rg -> rtk grep loses rg-native flags (--type, -g), causing errors and loops
      // ruff has its own output format; rtk rewriting breaks it
      if (/(?:^|[;&|]\s*)(rg|ruff)\s/.test(command)) return;

      try {
        const result = await $`rtk rewrite ${command}`.quiet().nothrow();
        const rewritten = String(result.stdout).trim();
        if (rewritten && rewritten !== command) {
          (args as Record<string, unknown>).command = rewritten;
        }
      } catch {
        // rtk rewrite failed -- pass through unchanged
      }
    },
  };
};
