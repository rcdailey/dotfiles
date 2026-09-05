import { expect, test } from "bun:test";
import { GhApiGuard } from "../../home/dot_config/opencode/exact_plugins/gh-api-guard";
import { ToolGuards } from "../../home/dot_config/opencode/exact_plugins/tool-guards";

const api = await GhApiGuard({} as never);
const tools = await ToolGuards({} as never);

for (const command of [
  "gh api --method GET user",
  "gh api user --method GET",
  "gh api --method=GET user",
  "gh api -XGET user",
  'rg "gh api.*deployments" .',
]) {
  test(`allows an unambiguous read: ${command}`, async () => {
    const output = { status: "ask" as "ask" | "allow" | "deny" };
    await api["permission.ask"]?.({ pattern: command, metadata: { command } } as never, output);
    expect(output.status).toBe("allow");
  });
}

for (const command of [
  "gh api --method DELETE repos/example/repo",
  "gh api --method GET --method DELETE repos/example/repo",
  "gh api --method GET -XDELETE repos/example/repo",
  "gh api --method GET -iX DELETE repos/example/repo",
  "gh api repos/example/repo -f --method=GET",
  'printf "%s" "$(gh api --method DELETE repos/example/repo)"',
  'printf "%s" "`gh api --method DELETE repos/example/repo`"',
  'bash -c "gh api --method DELETE repos/example/repo"',
  "python -c \"import os; os.system('gh api --method DELETE repos/example/repo')\"",
  'gh api --method GET graphql -f query="mutation { placeholder }"',
  "gh api --method GET user && git push",
  "gh api --method GET user > result.json",
  "gh api --method GET user & gh api --method DELETE repos/example/repo",
  'gh api --method GET "unterminated',
  "gh api --method $METHOD user",
  "gh api --method GET user # gh api --method DELETE repos/example/repo",
]) {
  test(`retains approval for ambiguous or mutating input: ${command}`, async () => {
    const output = { status: "ask" as "ask" | "allow" | "deny" };
    await api["permission.ask"]?.({ pattern: command, metadata: { command } } as never, output);
    expect(output.status).toBe("ask");
  });
}

test("does not relax an unrelated permission request or a denial", async () => {
  const command = "gh api --method GET user";
  const output = { status: "ask" as "ask" | "allow" | "deny" };
  await api["permission.ask"]?.({ pattern: "git push", metadata: { command } } as never, output);
  expect(output.status).toBe("ask");
  output.status = "deny";
  await api["permission.ask"]?.({ pattern: command, metadata: { command } } as never, output);
  expect(output.status).toBe("deny");
});

test("requires a method on an ordinary API invocation", async () => {
  await expect(
    api["tool.execute.before"]?.({ tool: "bash" } as never, { args: { command: "gh api user" } }),
  ).rejects.toThrow("explicit --method");
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
    await expect(
      tools["tool.execute.before"]?.({ tool: "bash" } as never, { args: { command } }),
    ).rejects.toThrow("TOOL USAGE VIOLATION");
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
    await tools["tool.execute.before"]?.({ tool: "bash" } as never, { args: { command } });
  });
}
