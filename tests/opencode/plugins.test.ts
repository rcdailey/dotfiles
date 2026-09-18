import { expect, test } from "bun:test";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadPlugin } from "./load-plugin";
import { createHost } from "./real-host.ts";

const { SessionRename } = await loadPlugin<any>("session-rename.ts");
const { ChatBrevity } = await loadPlugin<any>("chat-brevity.ts.tmpl");

test("loads local behavior plugins in the V2 host", async () => {
  const loaded: string[] = [];
  const observe = (plugin: any) => ({
    ...plugin,
    setup(context: unknown) {
      loaded.push(plugin.id);
      return plugin.setup(context);
    },
  });
  await using host = await createHost("{}", [observe(SessionRename), observe(ChatBrevity)]);
  const session = await host.sessions.create({ location: { directory: import.meta.dir } });
  await host.permission.list({ sessionID: session.id });
  expect(loaded).toEqual(["local.session-rename", "local.chat-brevity"]);
});

test("session rename updates only the invoking session", async () => {
  let definition: any;
  const updates: unknown[] = [];
  await SessionRename.setup({
    session: {
      update(input: unknown) {
        updates.push(input);
      },
    },
    tool: {
      transform(callback: (editor: any) => void) {
        callback({
          add(value: unknown) {
            definition = value;
          },
        });
      },
    },
  } as never);

  const result = await definition.execute({ title: "Focused title" }, { sessionID: "ses_current" });

  expect(updates).toEqual([{ sessionID: "ses_current", title: "Focused title" }]);
  expect(result.content).toBe("Session renamed to: Focused title");
  expect(definition.input.properties.title.maxLength).toBe(100);
});

test("chat brevity injects guidance only into primary context", async () => {
  let contextHook: ((event: any) => Promise<void>) | undefined;
  await ChatBrevity.setup({
    session: {
      get({ sessionID }: { sessionID: string }) {
        return Promise.resolve({
          id: sessionID,
          parentID: sessionID === "ses_child" ? "ses_parent" : undefined,
        });
      },
      hook(name: string, callback: (event: any) => Promise<void>) {
        if (name === "context") contextHook = callback;
      },
    },
  } as never);
  if (!contextHook) throw new Error("plugin did not register context hook");

  const stored = {
    sessionID: "ses_primary",
    messages: [{ role: "user", content: [{ type: "text", text: "Question" }] }],
  };
  const primary = structuredClone(stored);
  await contextHook(primary);
  expect(primary.messages[0].content).toHaveLength(2);
  expect(primary.messages[0].content[1].text).toContain("<system-reminder>");
  expect(stored.messages[0].content).toHaveLength(1);

  const continuation = {
    sessionID: "ses_primary",
    messages: [
      {
        role: "tool",
        content: [
          {
            type: "tool-result",
            id: "tool_1",
            name: "read",
            result: { type: "content", value: [{ type: "text", text: "result" }] },
          },
        ],
      },
    ],
  };
  await contextHook(continuation);
  const result = continuation.messages[0].content[0].result;
  expect(result.value[1].text).toContain("<system-reminder>");
  expect(result.value[1].text).not.toContain("When ending a turn");
  await contextHook(continuation);
  expect(result.value).toHaveLength(2);

  const child = {
    sessionID: "ses_child",
    messages: [{ role: "user", content: [{ type: "text", text: "Question" }] }],
  };
  await contextHook(child);
  expect(child.messages[0].content).toHaveLength(1);
});

test("chat brevity retries a failed session lookup", async () => {
  let contextHook: ((event: any) => Promise<void>) | undefined;
  let attempts = 0;
  await ChatBrevity.setup({
    session: {
      get() {
        attempts++;
        return attempts === 1 ? Promise.reject(new Error("temporary")) : Promise.resolve({});
      },
      hook(_name: string, callback: (event: any) => Promise<void>) {
        contextHook = callback;
      },
    },
  } as never);
  if (!contextHook) throw new Error("plugin did not register context hook");
  const event = {
    sessionID: "ses_primary",
    messages: [{ role: "user", content: [{ type: "text", text: "Question" }] }],
  };
  await contextHook(event);
  expect(event.messages[0].content).toHaveLength(1);
  await contextHook(event);
  expect(event.messages[0].content).toHaveLength(2);
});

test("chat guidance stays out of stored history across a host restart", async () => {
  const directory = await mkdtemp(join(tmpdir(), "opencode-chat-history-test-"));
  const database = join(directory, "sessions.db");
  let contextHook: ((event: any) => Promise<void>) | undefined;
  const observed = {
    ...ChatBrevity,
    setup(context: any) {
      return ChatBrevity.setup({
        ...context,
        session: {
          ...context.session,
          hook(name: string, callback: (event: any) => Promise<void>) {
            if (name === "context") contextHook = callback;
            return context.session.hook(name, callback);
          },
        },
      });
    },
  };
  const now = Date.now();
  const sessionID = "ses_history_test";
  const message = {
    id: "msg_history_test",
    type: "user" as const,
    text: "Question",
    time: { created: now },
  };

  {
    await using host = await createHost("{}", [observed], database, directory);
    await host.session.import({
      info: {
        id: sessionID,
        projectID: "project",
        cost: 0,
        tokens: { input: 0, output: 0, reasoning: 0, cache: { read: 0, write: 0 } },
        time: { created: now, updated: now },
        title: "History test",
        location: { directory },
      },
      messages: [message],
    });
    await host.permission.list({ sessionID });
    if (!contextHook) throw new Error("plugin did not register context hook");

    const outgoing = {
      sessionID,
      messages: [{ role: "user", content: [{ type: "text", text: message.text }] }],
    };
    await contextHook(outgoing);
    expect(outgoing.messages[0].content).toHaveLength(2);
    expect((await host.message.list({ sessionID })).data).toEqual([message]);
  }

  await using restarted = await createHost("{}", [ChatBrevity], database, directory);
  expect((await restarted.message.list({ sessionID })).data).toEqual([message]);
});
