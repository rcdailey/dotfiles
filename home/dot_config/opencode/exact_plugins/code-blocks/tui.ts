import { Plugin } from "@opencode/plugin/tui";
import {
  BoxRenderable,
  basenameToFiletype,
  CodeRenderable,
  createClipboard,
  createHostClipboard,
  createRendererClipboardAdapter,
  extensionToFiletype,
  infoStringToFiletype,
  type MarkdownCodeBlockRenderer,
  RenderableEvents,
  TextRenderable,
} from "@opentui/core";
import { findCodeBlocks } from "./blocks.ts";

// Built-in plugins draw these as diagrams and formulas; registering one throws in whichever
// plugin loads second.
const RESERVED = new Set(["mermaid", "latex", "math"]);
// Tags that no OpenTUI filetype maps, so they normalize to themselves.
const EXTRA_TAGS = ["txt", "text", "plaintext", "console", "shell", "output", "log", "diff"];
const COPIED_MS = 1500;
// Same heavy bar the TUI uses for message borders (packages/tui/src/ui/border.ts SplitBorder).
const LEFT_BAR = {
  topLeft: "",
  bottomLeft: "",
  vertical: "┃",
  topRight: "",
  bottomRight: "",
  horizontal: " ",
  bottomT: "",
  topT: "",
  cross: "",
  leftT: "",
  rightT: "",
};

type Clipboard = ReturnType<typeof createClipboard>;
type Context = Plugin.Context;

// OpenTUI exposes no catch-all renderer, so every known filetype and alias registers by name.
function languages() {
  const tags = [
    ...extensionToFiletype.keys(),
    ...extensionToFiletype.values(),
    ...basenameToFiletype.values(),
    ...EXTRA_TAGS,
  ];
  const names = tags.map((tag) => infoStringToFiletype(tag)).filter((name) => name !== undefined);
  return [...new Set(names)].filter((name) => !RESERVED.has(name));
}

// Fenced blocks stream through Markdown token updates; the panel replaces the default renderable
// only once the closing fence exists, so streaming never replaces a block on every chunk.
function isClosed(raw: string) {
  const fence = /^ {0,3}(`{3,}|~{3,})/.exec(raw)?.[1];
  if (!fence) return false;
  return new RegExp(`\\n {0,3}${fence[0]}{${fence.length},}[ \\t]*\\n*$`).test(raw);
}

async function writeClipboard(clipboard: Clipboard, text: string) {
  // OpenTUI rejects NUL before any destination; host clipboard text cannot contain it.
  const result = await clipboard.writeText(text.replaceAll("\0", ""), {
    destination: "all-available",
    selection: "clipboard",
  });
  if (result.host.status === "written" || result.terminal.status === "attempted") return;
  if (result.host.status === "failed") throw result.host.error;
  throw new Error(`clipboard write failed (host: ${result.host.status})`);
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function toMillis(value: unknown) {
  if (typeof value === "number") return value;
  if (value instanceof Date) return value.getTime();
  if (value && typeof value === "object" && "epochMillis" in value) {
    return Number(value.epochMillis);
  }
  return undefined;
}

function age(created: number | undefined) {
  if (created === undefined) return "";
  const minutes = Math.floor((Date.now() - created) / 60_000);
  if (minutes < 1) return "now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return hours < 24 ? `${hours}h ago` : `${Math.floor(hours / 24)}d ago`;
}

function preview(code: string) {
  return (
    code
      .split("\n")
      .find((line) => line.trim() !== "")
      ?.trim() ?? "(empty)"
  );
}

function createRenderer(context: Context, copy: (text: string) => Promise<void>) {
  const render: MarkdownCodeBlockRenderer = (token, defaults) => {
    const body = defaults.defaultRender();
    if (!body || !isClosed(token.raw)) return body ?? undefined;
    const theme = context.theme;
    const shade = theme.background.raised.base;
    if (body instanceof CodeRenderable) body.bg = shade;
    // Markdown gives the default block its inter-block margins; move them onto the panel.
    const { marginTop, marginBottom } = body;
    body.marginTop = 0;
    body.marginBottom = 0;
    // Padding mirrors the edit tool's panel so both read as the same kind of surface.
    const panel = new BoxRenderable(context.renderer, {
      width: "100%",
      flexDirection: "column",
      flexShrink: 0,
      backgroundColor: shade,
      border: ["left"],
      customBorderChars: LEFT_BAR,
      borderColor: theme.border.base,
      marginTop: marginTop ?? undefined,
      marginBottom: marginBottom ?? undefined,
      paddingTop: 1,
      paddingBottom: 1,
      paddingLeft: 2,
      paddingRight: 2,
    });
    const header = new BoxRenderable(context.renderer, {
      width: "100%",
      flexDirection: "row",
      flexShrink: 0,
      marginBottom: 1,
      backgroundColor: shade,
    });
    const language = new TextRenderable(context.renderer, {
      content: token.lang?.trim().split(/\s+/, 1)[0] ?? "",
      fg: theme.text.muted,
      bg: shade,
      flexGrow: 1,
      selectable: false,
    });
    let reset: ReturnType<typeof setTimeout> | undefined;
    let hovered = false;
    let copied = false;
    // Chip states: idle on the next raised shade, brighter on hover, success color after copying.
    const paint = () => {
      if (button.isDestroyed) return;
      button.content = copied ? " copied " : " copy ";
      button.bg = hovered ? theme.background.raised.max : theme.background.raised.high;
      button.fg = copied
        ? theme.text.feedback.success.base
        : hovered
          ? theme.text.base
          : theme.text.muted;
    };
    const button = new TextRenderable(context.renderer, {
      selectable: false,
      onMouseOver() {
        hovered = true;
        paint();
      },
      onMouseOut() {
        hovered = false;
        paint();
      },
      onMouseUp(event) {
        event.stopPropagation();
        void copy(token.text).then(
          () => {
            copied = true;
            paint();
            clearTimeout(reset);
            reset = setTimeout(() => {
              copied = false;
              paint();
            }, COPIED_MS);
          },
          () => undefined,
        );
      },
    });
    paint();
    panel.once(RenderableEvents.DESTROYED, () => clearTimeout(reset));
    header.add(language);
    header.add(button);
    panel.add(header);
    panel.add(body);
    return panel;
  };
  return render;
}

async function pickBlock(context: Context, copy: (text: string) => Promise<void>) {
  const route = context.ui.router.current();
  if (route.type !== "session") {
    context.ui.toast.show({ message: "Open a session to copy code blocks", variant: "info" });
    return;
  }
  const blocks = context.data.session.message
    .list(route.sessionID)
    .flatMap((message) => {
      if (message.type !== "assistant") return [];
      const created = toMillis(message.time.created);
      return message.content
        .flatMap((part) => (part.type === "text" ? findCodeBlocks(part.text) : []))
        .map((block) => ({ ...block, created }));
    })
    .reverse();
  if (blocks.length === 0) {
    context.ui.toast.show({ message: "No code blocks in this session", variant: "info" });
    return;
  }
  const choose = (text: string) => {
    context.ui.dialog.clear();
    void copy(text);
  };
  const index = await context.ui.dialog.select({
    title: "Copy code block",
    placeholder: "filter",
    current: 0,
    options: blocks.map((block, value) => ({
      title: preview(block.code),
      description: [block.lang || "plain", age(block.created)].filter(Boolean).join(" - "),
      value,
    })),
    actions: [
      {
        bind: "ctrl+o",
        title: "copy with fences",
        onTrigger: (value) => choose(blocks[value]?.fenced ?? ""),
      },
    ],
  });
  if (index === undefined) return;
  const block = blocks[index];
  if (block) void copy(block.code);
}

export default Plugin.define({
  id: "code-blocks",
  setup(context) {
    const clipboard = createClipboard({
      host: createHostClipboard(),
      terminal: createRendererClipboardAdapter(context.renderer),
    });
    const copy = (text: string) =>
      writeClipboard(clipboard, text).then(
        () => context.ui.toast.show({ message: "Copied code block", variant: "success" }),
        (error) => {
          context.ui.toast.show({ message: errorMessage(error), variant: "error" });
          throw error;
        },
      );
    const render = createRenderer(context, copy);
    // A language another plugin already owns stays with that plugin.
    const unregister = languages().flatMap((name) => {
      try {
        return [context.markdown.registerCodeBlockRenderer(name, render)];
      } catch {
        return [];
      }
    });
    context.keymap.layer(() => ({
      mode: "global",
      commands: [
        {
          id: "code-blocks.copy",
          title: "Copy code block",
          group: "Session",
          bind: "alt+x",
          palette: true,
          slash: { name: "copy-code" },
          run: () => pickBlock(context, (text) => copy(text).catch(() => undefined)),
        },
      ],
    }));
    return () => {
      for (const dispose of unregister) dispose();
      void clipboard.dispose();
    };
  },
});
