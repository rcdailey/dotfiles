import { expect, test } from "bun:test";
import type { Plugin } from "@opencode/plugin";
import { loadPlugin } from "./load-plugin";
import { createHost } from "./real-host.ts";

const { GhApiGuard } = await loadPlugin<{ GhApiGuard: Plugin.Plugin }>("gh-api-guard.ts");
const { ToolGuards } = await loadPlugin<{ ToolGuards: Plugin.Plugin }>("tool-guards.ts");
const { RipgrepRecursiveFlag } = await loadPlugin<{
  RipgrepRecursiveFlag: Plugin.Plugin;
}>("ripgrep-recursive-flag.ts");

type BeforeHook = (event: { tool: string; input: { command: string } }) => Promise<void> | void;

async function beforeHook(plugin: Plugin.Plugin): Promise<BeforeHook> {
  let hook: BeforeHook | undefined;
  await plugin.setup({
    tool: {
      hook(name: string, callback: BeforeHook) {
        if (name === "execute.before") hook = callback;
      },
    },
  } as never);
  if (!hook) throw new Error("plugin did not register execute.before");
  return hook;
}

const api = await beforeHook(GhApiGuard);
const tools = await beforeHook(ToolGuards);
const ripgrep = await beforeHook(RipgrepRecursiveFlag);

test("loads guard plugins in the V2 host", async () => {
  const loaded: string[] = [];
  const observe = (plugin: Plugin.Plugin): Plugin.Plugin => ({
    ...plugin,
    setup(context: unknown) {
      loaded.push(plugin.id);
      return plugin.setup(context);
    },
  });
  for (const plugin of [GhApiGuard, RipgrepRecursiveFlag, ToolGuards]) {
    await using host = await createHost("{}", [observe(plugin)]);
    const session = await host.sessions.create({ location: { directory: import.meta.dir } });
    await host.permission.list({ sessionID: session.id });
  }
  expect(loaded).toEqual([
    "local.gh-api-guard",
    "local.ripgrep-recursive-flag",
    "local.tool-guards",
  ]);
});

for (const [command, expected] of [
  ['rg -r "needle" path', 'rg "needle" path'],
  ['rg -rl "needle" path', 'rg -l "needle" path'],
  ['rg -nr "needle" path', 'rg -n "needle" path'],
  ['true && rg "-rn" "needle" path', 'true && rg -n "needle" path'],
] as const) {
  test(`removes ripgrep's mistaken recursive flag: ${command}`, async () => {
    const event = { tool: "shell", input: { command } };
    await ripgrep(event);
    expect(event.input.command).toBe(expected);
  });
}

for (const command of [
  'rg "needle" path',
  'rg --replace replacement "needle" path',
  "rg -- -r path",
  'printf "%s" "rg -r needle path"',
  "git rg -r needle path",
]) {
  test(`preserves intentional replacement and shell data: ${command}`, async () => {
    const event = { tool: "shell", input: { command } };
    await ripgrep(event);
    expect(event.input.command).toBe(command);
  });
}

const execute = async (hook: BeforeHook, command: string) =>
  hook({ tool: "shell", input: { command } });

for (const command of [
  "gh api --method GET user",
  "gh api --method POST repos/example/repo/issues",
]) {
  test(`accepts an explicit API method: ${command}`, async () => {
    await execute(api, command);
  });
}

test("requires a method on an ordinary API invocation", async () => {
  await expect(execute(api, "gh api user")).rejects.toThrow("explicit --method");
});

test("a rejected command cannot reach its shell side effect", async () => {
  let executed = false;
  const run = async (command: string) => {
    await execute(tools, command);
    executed = true;
  };

  await expect(run("grep needle file")).rejects.toThrow("TOOL USAGE VIOLATION");
  expect(executed).toBe(false);
});

for (const command of [
  "grep needle file",
  "git status && grep needle file",
  "true\ngrep needle file",
  "ssh host true; grep needle file",
  "command grep needle file",
  "command -p grep needle file",
  "(grep needle file)",
  "{ grep needle file; }",
  "git status && (grep needle file)",
  "grep needle file(N)",
  "grep needle file; printf foo(bar)",
  "printf foo(bar); grep needle file",
  "sudo -n grep needle file",
  "sudo -u root grep needle file",
  "env -i grep needle file",
  "env -u HOME grep needle file",
  "sudo -n env -i grep needle file",
  'find . -name "*.ts"',
  "sops --set value file",
  "sops --set=value file",
]) {
  test(`redirects an ordinary local invocation: ${command}`, async () => {
    await expect(execute(tools, command)).rejects.toThrow("TOOL USAGE VIOLATION");
  });
}

for (const command of [
  'printf "%s" "x | grep y"',
  'printf "%s" "x && find . -name y"',
  "git grep needle",
  "ssh host grep needle file",
  "kubectl exec pod -- grep needle file",
  "sudo -n ssh host grep needle file",
  "env -i ssh host grep needle file",
  "command -v grep",
  "sudo -u grep true",
  "sudo --user=grep true",
  "env -u grep true",
  'printf "%s" "(grep needle file)"',
  'printf "%s" "{ grep needle file; }"',
  "printf foo(grep)",
  "rg needle file",
  "find . -type f",
  "sops set file key value",
  "printf '%s' --set && sops file",
  "true # grep needle file",
  "python - <<'PY'\nprint('grep needle')\nPY",
]) {
  test(`leaves data, remote calls, and supported alternatives alone: ${command}`, async () => {
    await execute(tools, command);
  });
}
