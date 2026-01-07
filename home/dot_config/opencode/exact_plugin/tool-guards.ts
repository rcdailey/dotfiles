import type { Plugin } from "@opencode-ai/plugin"

interface RedirectionRule {
  pattern: RegExp
  message: string
}

const REDIRECTIONS: RedirectionRule[] = [
  {
    pattern: /(?<!-)\bgrep\b/,
    message: "Use 'rg' instead of 'grep' for better performance and features",
  },
  {
    pattern: /\bfind\b.*-name/,
    message: "Use 'rg --files -g pattern' instead of 'find -name'",
  },
  {
    pattern: /\|.*(?<!-)\bgrep\b/,
    message:
      "Avoid chaining grep commands - use 'rg' with multiple patterns or combined regex",
  },
  {
    pattern: /\bls\b.*\|.*\b(rg|grep)\b/,
    message:
      "Use 'rg --files -g pattern' instead of 'ls | rg/grep' for file filtering",
  },
  {
    pattern: /\bfind\b.*\|.*\b(rg|grep)\b/,
    message:
      "Use 'rg --files -g pattern' instead of 'find | rg/grep' combinations",
  },
  {
    pattern: /sops\s+--set/,
    message:
      "Use 'sops set' instead of 'sops --set'\nCorrect: sops set file.sops.yaml '[\"section\"][\"key\"]' '\"value\"'",
  },
]

const EXCLUDED_COMMAND_PREFIX =
  /^\s*(git|ssh|kubectl\s+(exec|run|debug)|docker\s+exec|podman\s+exec|talosctl)\s/

const GH_API_MUTATING_PATTERN = /-X\s+(POST|PUT|PATCH|DELETE)\b/i

export const ToolGuards: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return

      const command = output.args?.command as string
      if (!command) return

      // Skip validation for remote execution and container commands
      if (EXCLUDED_COMMAND_PREFIX.test(command)) return

      // Check tool redirections
      for (const rule of REDIRECTIONS) {
        if (rule.pattern.test(command)) {
          throw new Error(`TOOL USAGE VIOLATION: ${rule.message}`)
        }
      }

      // Check gh api readonly
      if (/\bgh\s+api\b/.test(command)) {
        if (GH_API_MUTATING_PATTERN.test(command)) {
          throw new Error(
            "GH API VIOLATION: Mutating operations not allowed. " +
              "gh api with -X POST/PUT/PATCH/DELETE is blocked. " +
              "Only read-only operations (GET or no -X flag) are permitted."
          )
        }
      }
    },
  }
}
