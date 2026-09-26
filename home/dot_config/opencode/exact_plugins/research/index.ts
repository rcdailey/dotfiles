import type { Plugin } from "@opencode/plugin";
import { DIRECT_TOOL } from "../lib/direct-tool.ts";
import { runResearch } from "./run.ts";

// Thin tools over the Python `research` CLI. They exist to pass the calling session's ID, which
// scopes the CLI's call budget and source/error ledgers, so parallel researchers stay isolated.

const SCOUT_USAGE = [
  "activity REPO [--days N=7]  Recent commits, merged PRs, and closed issues",
  "cat REPO PATH [-L/--limit N=240] [--offset N=0] [--ref REF] [--max-chars N]  Read a file",
  "changelog REPO [--since-tag TAG] [--since DATE] [--until DATE] [--limit N=10]",
  "commit REPO SHA [--patch] [--path PATH] [--max-chars N]  Commit summary and linked PRs",
  "commits REPO [--since X] [--until X] [--path PATH] [--author X] [-L/--limit N=30]",
  "diff REPO BASE..HEAD [--path PATH] [--max-chars N]  Compare two refs",
  "discussion REPO [NUMBER] [-S/--search X] [-L/--limit N=30] [--max-chars N]  List or view",
  "find REPO GLOB [-L/--limit N=100] [--ref REF] [--max-chars N]  Find files by glob",
  "forks REPO [--grep X] [--path PATH] [--diff X] [--sort pushed|stars] [--scan N=40] " +
    "[-L/--limit N=10] [--max-chars N]  Forks with their own commits",
  "history REPO PATH [-L/--limit N=30]  Commit history for a file",
  "issue REPO [NUMBER] [-S/--search X] [-s/--state open|closed|all] [-L/--limit N=30] " +
    "[--comments] [--max-chars N]  List or view",
  "orient REPO [--full] [--ref REF]  Metadata, structure summary, key files",
  "pr REPO [NUMBER] [-S/--search X] [-s/--state open|closed|merged|all] [-L/--limit N=30] " +
    "[--comments] [--reviews] [--max-chars N]  List or view",
  "release REPO [TAG] [-L/--limit N=30] [--since DATE] [--until DATE] [--max-chars N]",
  "rg REPO PATTERN [--path PATH] [-g/--glob X] [--type X] [-C/--context N] [-i] [-F] " +
    "[--ref REF] [--max-chars N]  Search file contents",
  "search QUERY [-L/--limit N=30] [--sort stars|forks|updated] [--language X] [--stars N] " +
    "[--forks N] [--max-chars N]  Search GitHub repositories",
];
const SCOUT_COMMANDS = SCOUT_USAGE.map((line) => line.split(" ")[0] as string);

type Input = Record<string, unknown>;
const record = (input: unknown) => (input && typeof input === "object" ? input : {}) as Input;

// Maps optional tool fields to CLI flags; booleans become bare flags when true.
function flags(input: Input, names: Record<string, string>) {
  return Object.entries(names).flatMap(([field, flag]) => {
    const value = input[field];
    if (value === undefined || value === false) return [];
    if (value === true) return [flag];
    return [flag, String(value)];
  });
}

const critical = {
  type: "boolean",
  description: "Use a reserved slot after the budget warning; only for one named blocking gap",
} as const;
const integer = (description: string, minimum = 0) =>
  ({ type: "integer", minimum, description }) as const;

export const Research = {
  id: "local.research",
  async setup(ctx) {
    await ctx.tool.transform((tools) => {
      tools.add({
        name: "research_search",
        description:
          "Search the web. Budgeted. Returns a sourced answer by default, or a ranked result " +
          "list with `results`. Search results are discovery only; fetch a source before " +
          "citing it.",
        input: {
          type: "object",
          properties: {
            query: { type: "string", minLength: 1 },
            max_results: { type: "integer", minimum: 1, maximum: 10, description: "Default 5" },
            results: { type: "boolean", description: "Return result URLs and snippets" },
            critical,
          },
          required: ["query"],
          additionalProperties: false,
        },
        options: DIRECT_TOOL,
        async execute(input, context) {
          const value = record(input);
          const args = [
            "web",
            "search",
            String(value.query),
            ...flags(value, {
              max_results: "--max-results",
              results: "--results",
              critical: "--critical",
            }),
          ];
          return { content: await runResearch(context.sessionID, args, context.signal) };
        },
      });

      tools.add({
        name: "research_fetch",
        description:
          "Fetch any URL as clean markdown. Budgeted; cached pages and pagination are free. " +
          "PDFs are converted automatically. GitHub issue, pull request, discussion, release, " +
          "commit, file, and repository URLs are routed to the matching GitHub reader.",
        input: {
          type: "object",
          properties: {
            url: { type: "string", minLength: 1 },
            find: { type: "string", description: "Show only paragraphs matching this pattern" },
            context: integer("Paragraphs of context around `find` matches"),
            max_chars: integer("Output bound; default 12000, 0 disables truncation"),
            offset: integer("Character offset into the content, applied before `find`"),
            critical,
          },
          required: ["url"],
          additionalProperties: false,
        },
        options: DIRECT_TOOL,
        async execute(input, context) {
          const value = record(input);
          const args = [
            "web",
            "fetch",
            String(value.url),
            ...flags(value, {
              find: "--find",
              context: "--context",
              max_chars: "--max-chars",
              offset: "--offset",
              critical: "--critical",
            }),
          ];
          return { content: await runResearch(context.sessionID, args, context.signal) };
        },
      });

      tools.add({
        name: "research_github",
        description: [
          "Explore GitHub repositories. Not budgeted. REPO is OWNER/REPO. Pass `command` and " +
            "its CLI arguments in `args`, for example command `rg`, args " +
            '["owner/repo", "pattern", "--path", "src"].',
          "Commands:",
          ...SCOUT_USAGE,
        ].join("\n"),
        input: {
          type: "object",
          properties: {
            command: { type: "string", enum: SCOUT_COMMANDS },
            args: { type: "array", items: { type: "string" } },
          },
          required: ["command", "args"],
          additionalProperties: false,
        },
        options: DIRECT_TOOL,
        async execute(input, context) {
          const value = record(input);
          const args = Array.isArray(value.args) ? value.args.map(String) : [];
          const argv = ["scout", String(value.command), ...args];
          return { content: await runResearch(context.sessionID, argv, context.signal) };
        },
      });

      tools.add({
        name: "research_ledger",
        description:
          "List every source URL retrieved and every research tool failure in this session. " +
          "Call before responding; cite only listed sources and report every failure.",
        input: { type: "object", properties: {}, additionalProperties: false },
        options: DIRECT_TOOL,
        async execute(_input, context) {
          const sources = await runResearch(context.sessionID, ["sources"], context.signal);
          const errors = await runResearch(context.sessionID, ["errors"], context.signal);
          return { content: `## Sources\n\n${sources}\n\n## Errors\n\n${errors}` };
        },
      });
    });
  },
} satisfies Plugin.Plugin;

export default Research;
