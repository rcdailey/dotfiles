import type { Plugin } from "@opencode-ai/plugin"

// Extract command names from the first line of a shell command. Only the first
// line is checked because multi-line content is heredocs or inline scripts
// where tool names appear as data, not invocations. Splits on shell operators
// (|, &&, ||, ;) and resolves each segment's first meaningful token (skipping
// env assignments, sudo, env).
function extractCommands(input: string): string[] {
  const firstLine = input.split("\n")[0]
  const segments = firstLine.split(/\s*(?:\|(?!\|)|\|\||&&|;)\s*/)
  const commands: string[] = []
  for (const segment of segments) {
    const tokens = segment.trim().split(/\s+/)
    for (const token of tokens) {
      if (!token || token.includes("=") || token === "sudo" || token === "env")
        continue
      commands.push(token.includes("/") ? token.split("/").pop()! : token)
      break
    }
  }
  return commands
}

interface RedirectionRule {
  command: string
  subpattern?: RegExp
  message: string
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
]

// Commands that run in remote/container contexts where we can't control tooling
const REMOTE_EXEC =
  /^\s*(git|ssh|kubectl\s+(exec|run|debug)|docker\s+exec|podman\s+exec|talosctl)\s/

export const ToolGuards: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return

      const command = output.args?.command as string
      if (!command) return

      if (REMOTE_EXEC.test(command)) return

      const cmds = extractCommands(command)

      for (const rule of REDIRECTIONS) {
        if (!cmds.includes(rule.command)) continue
        if (rule.subpattern && !rule.subpattern.test(command)) continue
        throw new Error(`TOOL USAGE VIOLATION: ${rule.message}`)
      }
    },
  }
}
