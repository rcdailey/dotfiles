import type { Plugin } from "@opencode/plugin";
import { readFile } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";

const CONFIG_NAMES = ["opencode.json", "opencode.jsonc"];

// A boolean `formatter` resets every lower-priority formatter entry, silently discarding the
// global md-format and Prettier overrides. OpenCode exposes no config API to plugins, so this
// mirrors config discovery (global directory, then every ancestor's direct and `.opencode` files).
function candidateFiles(directory: string): string[] {
  const configHome =
    process.env.XDG_CONFIG_HOME ?? path.join(homedir(), ".config");
  const files = CONFIG_NAMES.map((name) =>
    path.join(configHome, "opencode", name),
  );
  for (let current = directory; ; current = path.dirname(current)) {
    for (const name of CONFIG_NAMES) {
      files.push(
        path.join(current, name),
        path.join(current, ".opencode", name),
      );
    }
    if (path.dirname(current) === current) return files;
  }
}

/** Removes comments and trailing commas outside strings so JSON.parse accepts JSONC. */
function stripJsonc(text: string): string {
  let output = "";
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"') {
      const start = i;
      while (++i < text.length && text[i] !== '"') if (text[i] === "\\") i++;
      output += text.slice(start, i + 1);
    } else if (ch === "/" && text[i + 1] === "/") {
      while (i < text.length && text[i] !== "\n") i++;
      output += "\n";
    } else if (ch === "/" && text[i + 1] === "*") {
      i = text.indexOf("*/", i + 2);
      if (i === -1) break;
      i++;
    } else {
      output += ch;
    }
  }
  return output.replace(/,(\s*[}\]])/g, "$1");
}

async function setsFormatterTrue(file: string): Promise<boolean> {
  const text = await readFile(file, "utf8").catch(() => undefined);
  if (text === undefined) return false;
  try {
    return JSON.parse(stripJsonc(text))?.formatter === true;
  } catch {
    return false;
  }
}

async function offendingFiles(directory: string): Promise<string[]> {
  const files = [...new Set(candidateFiles(directory))];
  const flags = await Promise.all(files.map(setsFormatterTrue));
  return files.filter((_, index) => flags[index]);
}

/** Tells the agent to stop when any loaded config sets `formatter: true`. */
export const FormatterTrueGuard = {
  id: "local.formatter-true-guard",
  async setup(ctx) {
    await ctx.session.hook("context", async (event) => {
      const files = await offendingFiles(ctx.location.directory);
      if (files.length === 0) return;
      event.system.push({
        type: "text",
        text: [
          "STOP. Before any other work, tell the user that these OpenCode config files set",
          '`"formatter": true`, which discards the global formatter overrides:',
          ...files.map((file) => `- ${file}`),
          "Ask the user to remove the setting, and do not edit files until it is resolved.",
        ].join("\n"),
      });
    });
  },
} satisfies Plugin.Plugin;

export default FormatterTrueGuard;
