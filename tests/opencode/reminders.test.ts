import { expect, test } from "bun:test";
import { Message as AIMessage, LLM } from "@opencode/ai";
import { AnthropicMessages } from "@opencode/ai/protocols/anthropic-messages";
import { compileRequest } from "@opencode/ai/route/client";
import type { Plugin } from "@opencode/plugin";
import { Effect } from "effect";
import { ChatBrevity } from "../../home/dot_config/opencode/exact_plugins/chat-brevity/index.ts";
import { FileTools } from "../../home/dot_config/opencode/exact_plugins/file-tools/index.ts";
import * as delivery from "../../home/dot_config/opencode/exact_plugins/lib/system-reminder.ts";

type RequestModel = { providerID: string; id: string; variant?: string };
type Message = { role: string; content: Array<Record<string, unknown>>; id?: string };
type WireMessage = {
  role: string;
  content: string | Array<Record<string, unknown>>;
  clear_at?: string;
};
type Body = { messages: WireMessage[]; system: Array<Record<string, unknown>> };

const anthropic: RequestModel = { providerID: "anthropic", id: "claude-opus-5-5" };
const openai = { providerID: "openai", id: "gpt-6-astra" };
const checkpoint = { type: "ephemeral" };
const user = (text = "Fix the tests") => ({
  role: "user",
  content: [{ type: "text", text, cache_control: checkpoint }],
});
const call = (id = "read_1") => ({
  role: "assistant",
  content: [{ type: "tool_use", id, name: "read", input: {} }],
});
const result = (id = "read_1") => ({
  role: "user",
  content: [{ type: "tool_result", tool_use_id: id, content: "file", cache_control: checkpoint }],
});

async function harness(
  options: {
    store?: Map<string, unknown>;
    text?: string;
    parentID?: string;
    primaryOnly?: boolean;
    plugins?: Array<{ id: string; setup: (ctx: Plugin.Context) => Promise<unknown> }>;
    failWrites?: boolean;
  } = {},
) {
  const store = options.store ?? new Map<string, unknown>();
  const hooks = new Map<string, Array<(event: unknown) => Promise<void>>>();
  const plugins = options.plugins ?? [
    {
      id: "test",
      setup: (ctx: Plugin.Context) =>
        delivery.injectReminders(ctx, {
          text: () => options.text ?? "Keep it short",
          primaryOnly: options.primaryOnly,
        }),
    },
  ];
  for (const plugin of plugins) {
    const ctx = {
      session: {
        get: async () => ({ parentID: options.parentID }),
        hook: async (name: string, hook: (event: unknown) => Promise<void>) => {
          hooks.set(name, [...(hooks.get(name) ?? []), hook]);
        },
      },
      storage: {
        get: async (key: string) => structuredClone(store.get(`${plugin.id}/${key}`)),
        set: async (key: string, value: unknown) => {
          if (options.failWrites) throw new Error("Storage unavailable");
          store.set(`${plugin.id}/${key}`, structuredClone(value));
        },
      },
    } as unknown as Plugin.Context;
    await plugin.setup(ctx);
  }
  async function dispatch(name: string, event: unknown) {
    for (const hook of hooks.get(name) ?? []) await hook(event);
  }
  return {
    store,
    dispatch,
    async http(messages: unknown[], model = anthropic, kind = "primary", sessionID = "session") {
      const event = {
        sessionID,
        model,
        kind,
        request: new Request("https://api.anthropic.com/v1/messages", {
          method: "POST",
          headers: { "content-type": "application/json", "anthropic-beta": "existing-beta" },
          body: JSON.stringify({
            model: model.id,
            system: [{ type: "text", text: "Instructions", cache_control: checkpoint }],
            messages,
          }),
        }),
      };
      await dispatch("http.request", event);
      return { body: (await event.request.json()) as Body, headers: event.request.headers };
    },
    async context(messages: Message[], model: RequestModel = openai, sessionID = "session") {
      const event = { sessionID, model, messages: structuredClone(messages) };
      await dispatch("context", event);
      return event.messages;
    },
  };
}

test("native reminders follow the existing checkpoint without changing user content", async () => {
  const host = await harness();
  const { body, headers } = await host.http([user()]);
  expect(body.messages).toEqual([
    user(),
    { role: "system", clear_at: "next_user_message", content: "Keep it short" },
  ]);
  expect(body.system[0].cache_control).toEqual(checkpoint);
  expect(headers.get("anthropic-beta")).toContain("existing-beta");
  expect(headers.get("anthropic-beta")).toContain("mid-conversation-system-clear-at-2026-08-21");
});

test("native reminders follow existing system updates and their checkpoints", async () => {
  const host = await harness();
  const update = {
    role: "system",
    content: [{ type: "text", text: "New constraint", cache_control: checkpoint }],
  };
  const original = [user(), update];
  const first = await host.http(original);
  expect(first.body.messages.slice(0, original.length)).toEqual(original);
  expect(first.body.messages.at(-1)?.clear_at).toBe("next_user_message");
  const next = await host.http([...original, call(), result()]);
  expect(next.body.messages.slice(0, first.body.messages.length)).toEqual(first.body.messages);
});

test("native retries and restarts preserve original reminder text", async () => {
  const first = await harness();
  const initial = await first.http([user()], { ...anthropic, variant: "high" });
  const restarted = await harness({ store: first.store, text: "New guidance" });
  const retry = await restarted.http([user()], { ...anthropic, variant: "medium" });
  expect(retry.body).toEqual(initial.body);
  const plainUser = { role: "user", content: [{ type: "text", text: "Fix the tests" }] };
  const next = await restarted.http([plainUser, call(), result()]);
  expect(next.body.messages).toEqual([
    plainUser,
    initial.body.messages[1],
    call(),
    result(),
    { role: "system", clear_at: "next_user_message", content: "New guidance" },
  ]);
});

test("native reminders never split parallel tool results or unfinished tool calls", async () => {
  const host = await harness();
  const parallel = {
    role: "assistant",
    content: [...call().content, ...call("read_2").content],
  };
  const partial = await host.http([user(), parallel, result()]);
  expect(partial.body.messages).toEqual([user(), parallel, result()]);
  const complete = await host.http([user(), parallel, result(), result("read_2")]);
  expect(complete.body.messages.slice(0, 4)).toEqual([
    user(),
    parallel,
    result(),
    result("read_2"),
  ]);
  expect(complete.body.messages.at(-1).clear_at).toBe("next_user_message");
});

test("native delivery requires Anthropic Opus 4.8+ or Fable 5+", async () => {
  for (const id of [
    "claude-opus-4-8",
    "claude-opus-4-8-20260926",
    "claude-opus-5",
    "claude-opus-6",
    "claude-fable-5",
    "claude-fable-5-1",
    "claude-fable-6-20260926",
  ]) {
    const host = await harness();
    const model = { providerID: "anthropic", id };
    expect((await host.http([user()], model)).body.messages.at(-1).clear_at).toBe(
      "next_user_message",
    );
    expect(await host.context([user()], model)).toEqual([user()]);
  }
  for (const model of [
    openai,
    { providerID: "other", id: anthropic.id },
    ...["claude-opus-4-7", "claude-fable-4", "claude-sonnet-5", "claude-mythos-5", "unknown"].map(
      (id) => ({ providerID: "anthropic", id }),
    ),
  ]) {
    const host = await harness();
    expect((await host.http([user()], model)).body.messages).toEqual([user()]);
    expect((await host.context([user()], model))[0].content.at(-1).text).toBe("Keep it short");
  }
});

test("auxiliary requests and non-user tails get no new reminders", async () => {
  const host = await harness();
  for (const kind of ["title", "compaction", "generate"]) {
    expect((await host.http([user()], anthropic, kind)).body.messages).toEqual([user()]);
  }
  expect((await host.http([])).body.messages).toEqual([]);
  expect((await host.http([user(), call()])).body.messages).toEqual([user(), call()]);
  expect(host.store.size).toBe(0);
});

test("compaction, provider switches, undo, and sessions stay isolated", async () => {
  const host = await harness();
  const first = await host.http([user()]);
  await host.context([user()], openai);
  const compacted = [user("Summary of earlier work"), call(), result()];
  const after = await host.http(compacted);
  expect(after.body.messages.slice(0, 3)).toEqual(compacted);
  expect(after.body.messages.at(-1).clear_at).toBe("next_user_message");
  const restarted = await harness({ store: host.store, text: "Changed later" });
  expect((await restarted.http([user()])).body).toEqual(first.body);
  const separate = await restarted.http([user()], anthropic, "primary", "other-session");
  expect(separate.body.messages.at(-1).content).toBe("Changed later");
});

test("primary and child scopes compose with stable historical placement", async () => {
  for (const parentID of [undefined, "parent"]) {
    const host = await harness({ parentID, plugins: [ChatBrevity, FileTools] });
    const first = await host.http([user()]);
    const notes = first.body.messages.filter((message) => message.role === "system");
    expect(notes).toHaveLength(parentID ? 1 : 2);
    expect(notes.some((note) => String(note.content).includes("Read, search, and edit"))).toBe(
      true,
    );
    expect(notes.some((note) => String(note.content).includes("Follow Chat Style"))).toBe(
      !parentID,
    );
    const next = await host.http([user(), call(), result()]);
    expect(next.body.messages.slice(0, first.body.messages.length)).toEqual(first.body.messages);
    expect(next.body.messages.filter((message) => message.role === "system")).toHaveLength(
      notes.length * 2,
    );
  }
});

test("fallback uses each plugin's scope and the actual request model", async () => {
  for (const parentID of [undefined, "parent"]) {
    const host = await harness({ parentID, plugins: [ChatBrevity, FileTools] });
    const messages = await host.context([user()]);
    expect(JSON.stringify(messages)).not.toContain("Read, search, and edit");
    expect(JSON.stringify(messages).includes("first-pass comprehension")).toBe(!parentID);
    const sonnet = await host.context([user()], { providerID: "anthropic", id: "claude-sonnet-5" });
    expect(JSON.stringify(sonnet)).toContain("Read, search, and edit");
    expect(JSON.stringify(sonnet).includes("under 120 words")).toBe(!parentID);
  }
});

test("failed writes leave requests unchanged and allow recovery", async () => {
  const store = new Map<string, unknown>();
  const host = await harness({ store, failWrites: true });
  const request = new Request("https://api.anthropic.com/v1/messages", {
    method: "POST",
    body: JSON.stringify({ model: anthropic.id, messages: [user()] }),
  });
  const event = { sessionID: "session", model: anthropic, kind: "primary", request };
  await expect(host.dispatch("http.request", event)).rejects.toThrow("Storage unavailable");
  expect(event.request).toBe(request);
  expect(await request.json()).toEqual({ model: anthropic.id, messages: [user()] });
  expect(store.size).toBe(0);
  const retry = await harness({ store });
  expect((await retry.http([user()])).body.messages.at(-1).clear_at).toBe("next_user_message");
});

test("fallback preserves history and adds nothing to tool results", async () => {
  const host = await harness();
  const prompt = { id: "user_1", role: "user", content: [{ type: "text", text: "Fix tests" }] };
  const initial = await host.context([prompt]);
  expect(initial[0].content.at(-1)).toEqual({ type: "text", text: "Keep it short" });
  const tool = {
    role: "tool",
    content: [{ type: "tool-result", id: "read_1", result: { type: "text", value: "file" } }],
  };
  const next = await host.context([prompt, { role: "assistant", content: [] }, tool]);
  expect(next[0]).toEqual(initial[0]);
  expect(next.at(-1)).toEqual(tool);
});

test("real compilation preserves checkpoints and results across plugins", async () => {
  const host = await harness({ plugins: [ChatBrevity, FileTools] });
  const prompt = AIMessage.user("Fix the tests");
  const assistant = AIMessage.assistant([
    { type: "tool-call", id: "read_1", name: "read", input: {} },
    { type: "tool-call", id: "read_2", name: "read", input: {} },
  ]);
  const results = ["read_1", "read_2"].map((id) =>
    AIMessage.tool({
      id,
      name: "read",
      result: "file",
      resultType: "text",
    }),
  );
  const model = AnthropicMessages.route.model({ id: anthropic.id });
  let firstNotes: WireMessage[] | undefined;
  for (const messages of [[prompt], [prompt, assistant, ...results]]) {
    const compiled = await Effect.runPromise(
      compileRequest(
        LLM.request({
          model,
          system: [
            { type: "text", text: "Base instructions" },
            { type: "text", text: "Project rules" },
          ],
          tools: [{ name: "read", description: "Read a file", inputSchema: { type: "object" } }],
          messages,
        }),
      ),
    );
    const original = JSON.parse(JSON.stringify(compiled.body)) as Body;
    const event = {
      sessionID: "session",
      model: anthropic,
      kind: "primary",
      request: new Request("https://api.anthropic.com/v1/messages", {
        method: "POST",
        body: JSON.stringify(original),
      }),
    };
    await host.dispatch("http.request", event);
    const sent = (await event.request.json()) as Body;
    expect(sent.messages.filter((message) => message.role !== "system")).toEqual(original.messages);
    expect(sent.system).toEqual(original.system);
    const markers = (body: Body) => [...JSON.stringify(body).matchAll(/"cache_control":/g)].length;
    expect(markers(original)).toBe(4);
    expect(markers(sent)).toBe(markers(original));
    const notes = sent.messages.filter((message) => message.role === "system");
    if (firstNotes) expect(notes.slice(0, firstNotes.length)).toEqual(firstNotes);
    else firstNotes = notes;
  }
});

test("duplicate and concurrent HTTP interception is idempotent", async () => {
  const host = await harness({ plugins: [ChatBrevity, FileTools] });
  const [first, concurrent] = await Promise.all([host.http([user()]), host.http([user()])]);
  expect(concurrent.body).toEqual(first.body);
  const event = {
    sessionID: "session",
    model: anthropic,
    kind: "primary",
    request: new Request("https://api.anthropic.com/v1/messages", {
      method: "POST",
      body: JSON.stringify({ ...first.body, model: anthropic.id }),
      headers: first.headers,
    }),
  };
  await host.dispatch("http.request", event);
  expect(await event.request.json()).toEqual({ ...first.body, model: anthropic.id });
});

test("native reminders preserve images and failed tool results", async () => {
  const host = await harness();
  const image = {
    role: "user",
    content: [{ type: "image", source: { type: "url", url: "image" } }],
  };
  const failure = {
    role: "user",
    content: [{ type: "tool_result", tool_use_id: "read_1", is_error: true, content: "Denied" }],
  };
  const first = await host.http([image]);
  const next = await host.http([image, call(), failure]);
  expect(next.body.messages).toEqual([
    image,
    first.body.messages[1],
    call(),
    failure,
    first.body.messages[1],
  ]);
});

test("fallback text survives restart and changes only at new boundaries", async () => {
  const host = await harness();
  const initial = await host.context([user()]);
  const restarted = await harness({ store: host.store, text: "New wording" });
  const tool = { role: "tool", content: [{ type: "tool-result", id: "read_1", result: "file" }] };
  const during = await restarted.context([user(), { role: "assistant", content: [] }, tool]);
  expect(during[0]).toEqual(initial[0]);
  expect(during.at(-1)).toEqual(tool);
  const next = await restarted.context([
    user(),
    { role: "assistant", content: [] },
    user("Thanks"),
  ]);
  expect(next[0]).toEqual(initial[0]);
  expect(next.at(-1)?.content.at(-1)).toEqual({ type: "text", text: "New wording" });
});

test("fallback preserves trailing system updates", async () => {
  const host = await harness();
  const update = { role: "system", content: [{ type: "text", text: "Effort changed" }] };
  const messages = await host.context([user(), update]);
  expect(messages[0].content.at(-1)).toEqual({ type: "text", text: "Keep it short" });
  expect(messages[1]).toEqual(update);
});

test("corrupt history and malformed payloads leave requests unchanged", async () => {
  const host = await harness();
  await host.http([user()]);
  for (const key of host.store.keys()) host.store.set(key, { version: 999, entries: {} });
  await expect(host.http([user()])).rejects.toThrow("Invalid reminder history");
  for (const payload of [
    null,
    { model: "unsupported" },
    { model: anthropic.id, messages: [null] },
  ]) {
    const request = new Request("https://api.anthropic.com/v1/messages", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const event = { sessionID: "new-session", model: anthropic, kind: "primary", request };
    await expect(host.dispatch("http.request", event)).rejects.toThrow();
    expect(event.request).toBe(request);
    expect(await request.json()).toEqual(payload);
  }
});
