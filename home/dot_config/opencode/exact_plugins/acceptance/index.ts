import type { Plugin } from "@opencode/plugin";
import { begin, diff, finish, type Scope } from "./state.ts";

// Snapshot state is keyed by the calling session, so a resumed acceptance task continues its own
// iteration history and parallel audits stay isolated. Tools resolve the repository from the
// plugin instance directory, which is also the shell tool's default working directory.

const NO_INPUT = { type: "object", properties: {}, additionalProperties: false } as const;

const stringField = (input: unknown, key: string) => {
  const value = input && typeof input === "object" ? Reflect.get(input, key) : undefined;
  return typeof value === "string" && value ? value : undefined;
};

const pathsField = (input: unknown) => {
  const value = input && typeof input === "object" ? Reflect.get(input, "paths") : undefined;
  if (!Array.isArray(value) || !value.every((path) => typeof path === "string")) {
    throw new Error("paths must be an array of strings");
  }
  return value as string[];
};

export const Acceptance = {
  id: "local.acceptance",
  async setup(ctx) {
    const scope = (sessionID: string): Scope => ({ sessionID, directory: ctx.location.directory });

    await ctx.tool.transform((tools) => {
      tools.add({
        name: "acceptance_begin",
        description:
          "Capture the repository's current nonignored files as the pending acceptance " +
          "iteration and list changed paths since the last audited tree. Independent of the " +
          "Git index and commits. Resuming this session continues its iteration history.",
        input: {
          type: "object",
          properties: {
            base: {
              type: "string",
              description:
                "Initial comparison revision; only for a nondefault Base. Defaults to HEAD, " +
                "or the empty tree before the first commit.",
            },
          },
          additionalProperties: false,
        },
        async execute(input, context) {
          return { content: await begin(scope(context.sessionID), stringField(input, "base")) };
        },
      });

      tools.add({
        name: "acceptance_diff",
        description:
          "Show the pending iteration's patch for specific repository paths, compared with " +
          "the last audited tree. Requires acceptance_begin first.",
        input: {
          type: "object",
          properties: {
            paths: {
              type: "array",
              items: { type: "string" },
              minItems: 1,
              description: "Repository-relative paths or Git pathspecs",
            },
          },
          required: ["paths"],
          additionalProperties: false,
        },
        async execute(input, context) {
          return { content: await diff(scope(context.sessionID), pathsField(input)) };
        },
      });

      tools.add({
        name: "acceptance_finish",
        description:
          "Record the pending tree as audited. Reports `stable` when the repository still " +
          "matches it, or `retry` with changes made since acceptance_begin.",
        input: NO_INPUT,
        async execute(_input, context) {
          return { content: await finish(scope(context.sessionID)) };
        },
      });
    });
  },
} satisfies Plugin.Plugin;

export default Acceptance;
