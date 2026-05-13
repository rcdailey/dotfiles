import type { Plugin } from "@opencode-ai/plugin";

// Extract command names from the first line of a shell command. Only the first
// line is checked because multi-line content is heredocs or inline scripts
// where tool names appear as data, not invocations. Splits on shell operators
// (|, &&, ||, ;) and resolves each segment's first meaningful token (skipping
// env assignments, sudo, env).
function extractCommands(input: string): string[] {
  const firstLine = input.split("\n")[0];
  const segments = firstLine.split(/\s*(?:\|(?!\|)|\|\||&&|;)\s*/);
  const commands: string[] = [];
  for (const segment of segments) {
    const tokens = segment.trim().split(/\s+/);
    for (const token of tokens) {
      if (!token || token.includes("=") || token === "sudo" || token === "env") continue;
      const name = token.includes("/") ? token.split("/").pop() : token;
      if (name) commands.push(name);
      break;
    }
  }
  return commands;
}

interface RedirectionRule {
  command: string;
  subpattern?: RegExp;
  message: string;
}

const REDIRECTIONS: RedirectionRule[] = [
  {
    command: "grep",
    message: "Use 'rg' instead of 'grep' for better performance and features",
  },
  {
    command: "find",
    subpattern: /-name/,
    message: "Use 'rg --files -g pattern' instead of 'find -name'",
  },
  {
    command: "sops",
    subpattern: /\s--set\b/,
    message:
      "Use 'sops set' instead of 'sops --set'\nCorrect: sops set file.sops.yaml '[\"section\"][\"key\"]' '\"value\"'",
  },
];

// Commands that run in remote/container contexts where we can't control tooling
const REMOTE_EXEC =
  /^\s*(git|ssh|kubectl\s+(exec|run|debug)|docker\s+exec|podman\s+exec|talosctl)\s/;

// Rewrite plannotator's submit_plan to file-only mode. The upstream OpenCode
// plugin still advertises dual-mode (inline text or file path); this strips
// inline-text references so the LLM only sees the file-based workflow.
const SUBMIT_PLAN_DESCRIPTION =
  "Planning tool used to submit a plan to the user for review. Before calling " +
  "this tool you must conduct interactive and exploratory analysis in order to " +
  "submit a quality plan. Ask questions. Explore the codebase for context if " +
  "needed. Only call submit_plan once you have enough details to create a " +
  "quality plan. Work with the user to get those details. Write your plan to " +
  "a .md file using the write tool, then pass the absolute path here.";

const SUBMIT_PLAN_PARAM_DESCRIPTION = "Absolute path to a .md file on disk containing the plan.";

export const ToolGuards: Plugin = async () => {
  return {
    "tool.definition": async (input, output) => {
      if (input.toolID !== "submit_plan") return;
      output.description = SUBMIT_PLAN_DESCRIPTION;
      if (output.parameters?.properties?.plan) {
        output.parameters = {
          ...output.parameters,
          properties: {
            ...output.parameters.properties,
            plan: {
              ...output.parameters.properties.plan,
              description: SUBMIT_PLAN_PARAM_DESCRIPTION,
            },
          },
        };
      }
    },

    // Strip inline-text references from plannotator's injected system prompt
    "experimental.chat.system.transform": async (_input, output) => {
      for (let i = 0; i < output.system.length; i++) {
        const s = output.system[i];
        if (!s.includes("submit_plan")) continue;
        output.system[i] = s
          .replace(
            /- Pass your plan as markdown text[^\n]*\n- Or pass/g,
            "- Write your plan to a .md file, then pass",
          )
          .replace(
            /The tool auto-detects whether you passed text or a file path\. Both open the same review UI\./g,
            "The tool reads the file and opens a review UI.",
          )
          .replace(
            /Pass your plan as markdown text, or pass an absolute file path to a \.md file\./g,
            "Write your plan to a .md file using the write tool, then pass the absolute path.",
          );
      }
    },

    "tool.execute.before": async (input, output) => {
      if (input.tool === "submit_plan") {
        const plan = output.args?.plan as string;
        if (plan && !(plan.startsWith("/") && plan.endsWith(".md"))) {
          throw new Error(
            "submit_plan requires an absolute path to a .md file. " +
              "Write your plan to a file first, then pass the path.",
          );
        }
        return;
      }

      if (input.tool !== "bash") return;

      const command = output.args?.command as string;
      if (!command) return;

      if (REMOTE_EXEC.test(command)) return;

      const cmds = extractCommands(command);

      for (const rule of REDIRECTIONS) {
        if (!cmds.includes(rule.command)) continue;
        if (rule.subpattern && !rule.subpattern.test(command)) continue;
        throw new Error(`TOOL USAGE VIOLATION: ${rule.message}`);
      }
    },
  };
};
