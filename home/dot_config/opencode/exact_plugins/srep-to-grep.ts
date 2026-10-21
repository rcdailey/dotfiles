import type { Plugin } from "@opencode/plugin";

// Claude models sometimes call a nonexistent `srep` tool with grep's arguments. The
// execute.before hook runs before tool lookup and its `tool` field selects the executor, so
// renaming it there runs the real grep. The after hook tells the model about the misspelling.

const MISSPELLED = "srep";
const TARGET = "grep";
const NOTE = [
  `Note: no tool named "${MISSPELLED}" exists; this call ran "${TARGET}".`,
  `Call "${TARGET}" directly.`,
].join(" ");

/** Routes misspelled `srep` tool calls to grep and adds a correction to the result. */
export const SrepToGrep = {
  id: "local.srep-to-grep",
  async setup(ctx) {
    const redirected = new Set<string>();

    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== MISSPELLED) return;
      event.tool = TARGET;
      redirected.add(event.id);
    });

    await ctx.tool.hook("execute.after", (event) => {
      if (!redirected.delete(event.id) || event.status !== "completed") return;
      const { content, output } = event.result;
      // Empty content makes OpenCode render `output`; keep it visible once a note is added.
      const parts =
        typeof content === "string"
          ? [{ type: "text" as const, text: content }]
          : content?.length
            ? [...content]
            : [{ type: "text" as const, text: JSON.stringify(output) ?? "" }];
      event.result = {
        ...event.result,
        content: [...parts, { type: "text", text: NOTE }],
      };
    });
  },
} satisfies Plugin.Plugin;

export default SrepToGrep;
