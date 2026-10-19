import { readFileSync } from "node:fs";
import { join } from "node:path";
import { type ExtensionAPI, getAgentDir } from "@earendil-works/pi-coding-agent";
import { isSubagentChild, trackSubagentChildren } from "./lib/subagent-children.ts";

// Adds ~/.pi/agent/PRIMARY.md to the main session's system prompt as a <primary_instructions>
// section. Subagents inherit global AGENTS.md, so rules for talking to the user live here instead.
// The file is read once at load so the section stays byte-identical and the cached prefix holds;
// edits take effect on /reload. Children skip it, and pi never copies custom sections to them.

export default function primaryInstructions(pi: ExtensionAPI) {
  let text: string;
  try {
    text = readFileSync(join(getAgentDir(), "PRIMARY.md"), "utf8").trim();
  } catch {
    return;
  }

  trackSubagentChildren(pi);
  pi.on("before_agent_start", (event, ctx) => {
    if (isSubagentChild(ctx)) return;
    event.systemPromptOptions.sections.primary_instructions = text;
  });
}
