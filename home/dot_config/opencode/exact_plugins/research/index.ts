import type { Plugin } from "@opencode/plugin";
import { DIRECT_TOOL } from "../lib/direct-tool.ts";
import { runResearch } from "./run.ts";

// Thin tools over the Python `research` CLI. They exist to pass the calling session's ID, which
// scopes the CLI's call budget and source/error ledgers, so parallel researchers stay isolated.

type Input = Record<string, unknown>;
type Schema = Record<string, unknown>;
const record = (input: unknown) => (input && typeof input === "object" ? input : {}) as Input;

// Maps optional tool fields to CLI flags: true becomes a bare flag, arrays repeat the flag.
function flags(input: Input, names: Record<string, string>) {
  return Object.entries(names).flatMap(([field, flag]) => {
    const value = input[field];
    if (value === undefined || value === false) return [];
    if (value === true) return [flag];
    if (Array.isArray(value)) return value.flatMap((item) => [flag, String(item)]);
    return [flag, String(value)];
  });
}

// Field schemas stay minimal because every byte ships in each researcher prompt; the CLI
// validates value ranges and reports violations as usage errors.
const described = (schema: Schema, description?: string) =>
  description ? { ...schema, description } : schema;
const text = (description?: string) => described({ type: "string" }, description);
const integer = (description?: string) => described({ type: "integer" }, description);
const flag = (description?: string) => described({ type: "boolean" }, description);
const texts = (description?: string) =>
  described({ type: "array", items: { type: "string" } }, description);
const choice = (values: string[], description?: string) =>
  described({ type: "string", enum: values }, description);

const critical = flag(
  "Use a reserved slot after the budget warning; only for one named blocking gap. " +
    "Otherwise synthesize; a budget limit is not evidence that a source does not exist.",
);

const repo = text("OWNER/REPO");
const number = integer();
const ref = text("Branch, tag, or SHA");
const date = { type: "string", format: "date" };
// Truncated output explains this bound, so the field carries no description.
const maxChars = integer();
const limit = (fallback: number, unit = "") => integer(`${unit}Default ${fallback}`);
const threadList = {
  search: text(),
  limit: limit(30),
  max_chars: maxChars,
};

/**
 * One tool per `research scout` subcommand. `arguments` names the fields passed positionally, in
 * CLI order; `positional` overrides how they render when the CLI combines them. Every other field
 * becomes the same-named flag (`max_chars` -> `--max-chars`), so field names must match the CLI's
 * long option names.
 */
interface GitHubTool {
  description: string;
  arguments: string[];
  positional?: (input: Input) => unknown[];
  required: string[];
  properties: Record<string, Schema>;
}

const GITHUB_TOOLS: Record<string, GitHubTool> = {
  advisory: {
    description:
      "Security advisory by GHSA or CVE ID: severity, affected version ranges, first patched " +
      "versions, description, and references.",
    arguments: ["id"],
    required: ["id"],
    properties: { id: text(), max_chars: maxChars },
  },
  activity: {
    description: "Recent commits, merged PRs, and closed issues.",
    arguments: ["repo"],
    required: ["repo"],
    properties: { repo, days: limit(7) },
  },
  cat: {
    description:
      "Read a repository file. After a missing path, use research_github_find; do not guess.",
    arguments: ["repo", "path"],
    required: ["repo", "path"],
    properties: {
      repo,
      path: text(),
      limit: integer("Lines; default 240, 0 = all"),
      offset: integer("Lines to skip"),
      ref,
      max_chars: maxChars,
    },
  },
  changelog: {
    description: "Changelog file and releases, optionally narrowed to a version or date range.",
    arguments: ["repo"],
    required: ["repo"],
    properties: { repo, since_tag: text(), since: date, until: date, limit: limit(10) },
  },
  commit: {
    description: "One commit with its linked PRs.",
    arguments: ["repo", "sha"],
    required: ["repo", "sha"],
    properties: {
      repo,
      sha: text(),
      patch: flag("Include file patches"),
      path: text("Path prefix filter"),
      max_chars: maxChars,
    },
  },
  commits: {
    description: "List commits.",
    arguments: ["repo"],
    required: ["repo"],
    properties: {
      repo,
      since: text("ISO 8601"),
      until: text("ISO 8601"),
      path: text(),
      author: text(),
      limit: limit(30),
    },
  },
  diff: {
    description: "Compare two refs.",
    arguments: ["repo", "base", "head"],
    positional: (input) => [input.repo, `${input.base}..${input.head}`],
    required: ["repo", "base", "head"],
    properties: {
      repo,
      base: text(),
      head: text(),
      path: text("Path prefix filter"),
      max_chars: maxChars,
    },
  },
  discussion: {
    description: "List discussions, or view one by number. Search matches titles.",
    arguments: ["repo", "number"],
    required: ["repo"],
    properties: { repo, number, ...threadList },
  },
  find: {
    description: "Find files by glob. Use when paths are unknown, before rg or cat.",
    arguments: ["repo", "glob"],
    required: ["repo", "glob"],
    properties: {
      repo,
      glob: text(),
      limit: integer("Default 100, 0 = all"),
      ref,
      max_chars: maxChars,
    },
  },
  forks: {
    description:
      "Find fork commits absent upstream, such as unmerged fixes. Filter with grep or path, " +
      "then read matches with research_github_commit.",
    arguments: ["repo"],
    required: ["repo"],
    properties: {
      repo,
      grep: text("Regex on commit messages"),
      path: text("File or directory the commits touch"),
      diff: text("Regex on changed lines; requires grep or path"),
      sort: choice(["pushed", "stars"], "Which forks to scan first; default pushed"),
      scan: integer("Forks compared; default 40, max 100"),
      limit: limit(10, "Forks shown; "),
      max_chars: maxChars,
    },
  },
  history: {
    description: "Commit history for one file.",
    arguments: ["repo", "path"],
    required: ["repo", "path"],
    properties: { repo, path: text(), limit: limit(30) },
  },
  issue: {
    description: "List issues, or view one by number.",
    arguments: ["repo", "number"],
    required: ["repo"],
    properties: {
      repo,
      number,
      state: choice(["open", "closed", "all"], "Default open"),
      comments: flag("Include comments when viewing one"),
      ...threadList,
    },
  },
  orient: {
    description: "Repository metadata, structure, and key files. Start here for unknown layouts.",
    arguments: ["repo"],
    required: ["repo"],
    properties: { repo, full: flag("Include key file contents"), ref },
  },
  pr: {
    description: "List pull requests, or view one by number.",
    arguments: ["repo", "number"],
    required: ["repo"],
    properties: {
      repo,
      number,
      state: choice(["open", "closed", "merged", "all"], "Default open"),
      comments: flag("Include comments when viewing one"),
      reviews: flag("Include reviews when viewing one"),
      ...threadList,
    },
  },
  release: {
    description: "List releases, or view one by tag.",
    arguments: ["repo", "tag"],
    required: ["repo"],
    properties: {
      repo,
      tag: text(),
      since: date,
      until: date,
      limit: limit(30),
      max_chars: maxChars,
    },
  },
  rg: {
    description: "Search file contents with ripgrep.",
    arguments: ["repo", "pattern"],
    required: ["repo", "pattern"],
    properties: {
      repo,
      pattern: text("Regex unless fixed_strings"),
      path: texts("Default repository root"),
      glob: texts(),
      type: texts("ripgrep file types"),
      context: integer(),
      after_context: integer(),
      before_context: integer(),
      max_count: integer("Matches per file"),
      ignore_case: flag(),
      fixed_strings: flag(),
      word_regexp: flag(),
      files_with_matches: flag(),
      count: flag("Matching lines per file"),
      ref,
      max_chars: maxChars,
    },
  },
  search: {
    description: "Search GitHub repositories.",
    arguments: ["query"],
    required: ["query"],
    properties: {
      query: text(),
      sort: choice(["stars", "forks", "updated"], "Default stars"),
      language: text(),
      stars: integer("Minimum stars"),
      forks: integer("Top forks listed per result"),
      limit: limit(30),
      max_chars: maxChars,
    },
  },
};

export const Research = {
  id: "local.research",
  async setup(ctx) {
    await ctx.tool.transform((tools) => {
      tools.add({
        name: "research_search",
        description:
          "Search the web for candidate URLs. Budgeted. Results are discovery only and never " +
          "citable; fetch a URL before citing it. To find a page on a known site, restrict " +
          "`domains` instead of guessing its URL.",
        input: {
          type: "object",
          properties: {
            query: text(),
            max_results: integer("Default 5, max 20"),
            domains: texts("Only return results from these sites, e.g. learn.microsoft.com"),
            exclude_domains: texts(),
            time_range: choice(
              ["day", "week", "month", "year"],
              "Only results published within this period",
            ),
            exact: flag("Quoted phrases in `query` must appear verbatim, e.g. an error string"),
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
              domains: "--domain",
              exclude_domains: "--exclude-domain",
              max_results: "--max-results",
              time_range: "--time-range",
              exact: "--exact",
              critical: "--critical",
            }),
          ];
          return { content: await runResearch(context.sessionID, args, context.signal) };
        },
      });

      tools.add({
        name: "research_fetch",
        description:
          "Fetch a URL as clean markdown. Budgeted; cached pages and pagination are free, and " +
          "a 404 is refunded. Fetch only URLs seen in tool output or supplied by the caller. " +
          "PDFs are converted automatically. GitHub issue, pull request, discussion, release, " +
          "commit, file, raw file, and repository URLs are routed to the matching GitHub " +
          "reader without budget cost. When targeting a named field, option, symbol, or " +
          "phrase, start with `find`; page cached content with `offset`. A `find` no-match is " +
          "failed evidence: " +
          "retry without `find` or with a corrected pattern.",
        input: {
          type: "object",
          properties: {
            url: text(),
            find: text("Show only paragraphs matching this pattern"),
            context: integer("Paragraphs of context around `find` matches"),
            max_chars: integer(
              "Output bound; default 12000, 0 disables truncation. Prefer a narrower `find` " +
                "or `offset` page when one can answer the question.",
            ),
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

      for (const [command, tool] of Object.entries(GITHUB_TOOLS)) {
        const options = Object.keys(tool.properties)
          .filter((field) => !tool.arguments.includes(field))
          .map((field) => [field, `--${field.replaceAll("_", "-")}`]);
        tools.add({
          name: `research_github_${command}`,
          description: tool.description,
          input: {
            type: "object",
            properties: tool.properties,
            required: tool.required,
            additionalProperties: false,
          },
          options: DIRECT_TOOL,
          async execute(input, context) {
            const value = record(input);
            const positional = tool.positional?.(value) ?? tool.arguments.map((f) => value[f]);
            const argv = [
              "scout",
              command,
              ...positional.filter((item) => item !== undefined).map(String),
              ...flags(value, Object.fromEntries(options)),
            ];
            return { content: await runResearch(context.sessionID, argv, context.signal) };
          },
        });
      }

      tools.add({
        name: "research_ledger",
        description:
          "List every citable source URL retrieved and every research tool failure in this " +
          "session. Call once before the final response; cite only listed sources and report " +
          "every listed failure.",
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
