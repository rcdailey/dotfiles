import type { Plugin } from "@opencode/plugin";
import { DIRECT_TOOL } from "../lib/direct-tool.ts";
import {
  begin,
  CASE_STATUSES,
  diff,
  finish,
  type LedgerEntry,
  type RepositoryInput,
  type Scope,
  VERDICTS,
  workspace,
} from "./state.ts";

// Snapshot state is keyed by the calling session, so a resumed acceptance task continues its own
// iteration history and parallel audits stay isolated. Tools resolve the primary repository from
// the plugin instance directory, which is also the shell tool's default working directory.

const NO_INPUT = { type: "object", properties: {}, additionalProperties: false } as const;

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const repositoriesField = (input: unknown): RepositoryInput[] => {
  const value = isRecord(input) ? input.repositories : undefined;
  if (value === undefined) return [];
  const valid =
    Array.isArray(value) &&
    value.every(
      (item) =>
        isRecord(item) &&
        typeof item.path === "string" &&
        item.path !== "" &&
        (item.base === undefined || typeof item.base === "string"),
    );
  if (!valid) throw new Error("repositories must be an array of { path, base? }");
  return value as RepositoryInput[];
};

const verdictField = (input: unknown) => {
  const value = isRecord(input) ? input.verdict : undefined;
  if (!VERDICTS.includes(value as (typeof VERDICTS)[number])) {
    throw new Error(`verdict must be one of: ${VERDICTS.join(", ")}`);
  }
  return value as (typeof VERDICTS)[number];
};

const ledgerField = (input: unknown): LedgerEntry[] => {
  const value = isRecord(input) ? input.ledger : undefined;
  const valid =
    Array.isArray(value) &&
    value.every(
      (entry) =>
        isRecord(entry) &&
        typeof entry.case === "string" &&
        CASE_STATUSES.includes(entry.status as (typeof CASE_STATUSES)[number]) &&
        typeof entry.evidence === "string" &&
        Array.isArray(entry.paths) &&
        entry.paths.every((path) => typeof path === "string"),
    );
  if (!valid) throw new Error("ledger must be an array of { case, status, evidence, paths }");
  return value as LedgerEntry[];
};

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
          "Capture the current nonignored files of the primary repository and every named " +
          "repository as the pending acceptance iteration, and list each one's changed paths " +
          "since its last audited tree. Independent of the Git index and commits. Resuming " +
          "this session continues its iteration history, remembers named repositories, and " +
          "returns the stored ledger with entries whose paths changed marked stale.",
        input: {
          type: "object",
          properties: {
            base: {
              type: "string",
              description:
                "Primary repository's initial comparison revision; only for a nondefault " +
                "Base. Defaults to HEAD, or the empty tree before the first commit.",
            },
            repositories: {
              type: "array",
              description:
                "Additional repositories this goal changed. Each is then addressed by its " +
                "directory name, as `name:path` in other tools. Omit on resume to reuse them.",
              items: {
                type: "object",
                properties: {
                  path: { type: "string", description: "Repository directory path" },
                  base: { type: "string", description: "Nondefault initial revision" },
                },
                required: ["path"],
                additionalProperties: false,
              },
            },
          },
          additionalProperties: false,
        },
        options: DIRECT_TOOL,
        async execute(input, context) {
          const base = stringField(input, "base");
          return { content: await begin(scope(context.sessionID), base, repositoriesField(input)) };
        },
      });

      tools.add({
        name: "acceptance_diff",
        description:
          "Show the pending iteration's patch for specific paths, compared with the last " +
          "audited tree. Prefix paths in additional repositories with `name:`. Requires " +
          "acceptance_begin first.",
        input: {
          type: "object",
          properties: {
            paths: {
              type: "array",
              items: { type: "string" },
              minItems: 1,
              description:
                "Repository-relative paths or Git pathspecs, `name:`-prefixed " +
                "for additional repositories",
            },
          },
          required: ["paths"],
          additionalProperties: false,
        },
        options: DIRECT_TOOL,
        async execute(input, context) {
          return { content: await diff(scope(context.sessionID), pathsField(input)) };
        },
      });

      tools.add({
        name: "acceptance_workspace",
        description:
          "Recreate a ready-to-run sandbox beside each repository: a standalone Git checkout " +
          "whose HEAD commits the previous audited tree and whose index and files hold the " +
          "pending tree, plus ignored files listed in the repository's .worktreeinclude, after " +
          "the repository's .config/wt.toml pre-start hook runs. Reports each sandbox path, " +
          "copied files, and the hook outcome. Each call discards prior edits. Requires " +
          "acceptance_begin first.",
        input: NO_INPUT,
        options: DIRECT_TOOL,
        async execute(_input, context) {
          return { content: await workspace(scope(context.sessionID)) };
        },
      });

      tools.add({
        name: "acceptance_finish",
        description:
          "Store the verdict and ledger, record every pending tree as audited, and remove the " +
          "sandboxes. Reports `stable` when every repository still matches its audited tree, " +
          "or `retry` with changes made since acceptance_begin.",
        input: {
          type: "object",
          properties: {
            verdict: { type: "string", enum: [...VERDICTS] },
            ledger: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  case: { type: "string" },
                  status: { type: "string", enum: [...CASE_STATUSES] },
                  evidence: { type: "string" },
                  paths: {
                    type: "array",
                    items: { type: "string" },
                    description: "Paths the evidence depends on; `name:`-prefixed when additional",
                  },
                },
                required: ["case", "status", "evidence", "paths"],
                additionalProperties: false,
              },
            },
          },
          required: ["verdict", "ledger"],
          additionalProperties: false,
        },
        options: DIRECT_TOOL,
        async execute(input, context) {
          const sessionScope = scope(context.sessionID);
          return { content: await finish(sessionScope, verdictField(input), ledgerField(input)) };
        },
      });
    });
  },
} satisfies Plugin.Plugin;

export default Acceptance;
