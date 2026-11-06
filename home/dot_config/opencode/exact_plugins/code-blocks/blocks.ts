/** A fenced Markdown code block; `fenced` rebuilds it without container prefixes. */
export type CodeBlock = { lang: string; code: string; fenced: string };

type Open = { fence: string; info: string; quotes: number; indent: number; lines: string[] };

const OPENING = /^((?:[-*+]|\d{1,9}[.)])[ \t]+)?( *)(`{3,}|~{3,})(.*)$/;

/** Removes up to `depth` blockquote markers; undefined when the line has fewer. */
function stripQuotes(line: string, depth: number) {
  let rest = line;
  for (let level = 0; level < depth; level++) {
    const marker = /^ {0,3}> ?/.exec(rest);
    if (!marker) return undefined;
    rest = rest.slice(marker[0].length);
  }
  return rest;
}

function countQuotes(line: string) {
  let depth = 0;
  let rest = line;
  for (let marker = /^ {0,3}> ?/.exec(rest); marker; marker = /^ {0,3}> ?/.exec(rest)) {
    depth++;
    rest = rest.slice(marker[0].length);
  }
  return { depth, rest };
}

function dedent(line: string, indent: number) {
  const spaces = /^ */.exec(line)?.[0].length ?? 0;
  return line.slice(Math.min(spaces, indent));
}

function finish(open: Open): CodeBlock {
  const code = open.lines.join("\n");
  const lang = open.info.trim().split(/\s+/, 1)[0] ?? "";
  const body = open.lines.length > 0 ? `${code}\n` : "";
  return { lang, code, fenced: `${open.fence}${open.info.trim()}\n${body}${open.fence}` };
}

/**
 * Finds fenced code blocks in document order, including blocks inside list items and
 * blockquotes. An unclosed final fence is still streaming and is excluded; a fence whose
 * blockquote ends first closes there, as CommonMark renders it.
 */
export function findCodeBlocks(markdown: string): CodeBlock[] {
  const blocks: CodeBlock[] = [];
  let open: Open | undefined;
  for (const line of markdown.split(/\r?\n/)) {
    if (open) {
      const inner = stripQuotes(line, open.quotes);
      if (inner === undefined) {
        blocks.push(finish(open));
        open = undefined;
      } else {
        const content = dedent(inner, open.indent);
        const char = open.fence[0];
        const closing = new RegExp(`^ {0,3}\\${char}{${open.fence.length},}[ \\t]*$`);
        if (closing.test(content)) {
          blocks.push(finish(open));
          open = undefined;
        } else {
          open.lines.push(content);
        }
        continue;
      }
    }
    const { depth, rest } = countQuotes(line);
    const leading = /^ */.exec(rest)?.[0].length ?? 0;
    const match = OPENING.exec(rest.slice(leading));
    if (!match) continue;
    const [, marker = "", padding = "", fence = "", info = ""] = match;
    if (fence.startsWith("`") && info.includes("`")) continue;
    const indent = leading + marker.length + padding.length;
    open = { fence, info, quotes: depth, indent, lines: [] };
  }
  return blocks;
}
