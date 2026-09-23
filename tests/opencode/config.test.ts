import { expect, test } from "bun:test";
import { mkdir, mkdtemp, readdir, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parse } from "jsonc-parser";
import { createHost } from "./real-host.ts";

const template = join(import.meta.dir, "../../home/dot_config/opencode/opencode.jsonc.tmpl");
const agentSource = join(import.meta.dir, "../../home/dot_config/opencode/exact_agents");

const providers = ["anthropic", "openai"] as const;
type ProviderID = (typeof providers)[number];

function renderTemplate(file: string, opencodeProvider: ProviderID) {
  const result = Bun.spawnSync([
    "chezmoi",
    "execute-template",
    "--override-data",
    JSON.stringify({ opencodeProvider }),
    "--file",
    file,
  ]);
  if (result.exitCode !== 0) throw new Error(result.stderr.toString());
  return result.stdout.toString();
}

function render(provider: ProviderID): any {
  const errors: unknown[] = [];
  const config = parse(renderTemplate(template, provider), errors, { allowTrailingComma: true });
  expect(errors).toEqual([]);
  return config;
}

async function renderAgents(provider: ProviderID) {
  const directory = await mkdtemp(join(tmpdir(), "opencode-config-test-"));
  const agents = join(directory, "agents");
  await mkdir(agents);
  for (const name of await readdir(agentSource)) {
    if (!name.endsWith(".md") && !name.endsWith(".md.tmpl")) continue;
    const source = join(agentSource, name);
    const content = name.endsWith(".tmpl")
      ? renderTemplate(source, provider)
      : await readFile(source, "utf8");
    await writeFile(join(agents, name.replace(/\.tmpl$/, "")), content);
  }
  return directory;
}

test("renders and loads native V2 configuration for every provider", async () => {
  for (const provider of providers) {
    const config = render(provider);
    expect(config.agent).toBeUndefined();
    expect(config.permission).toBeUndefined();
    expect(config.plugin).toBeUndefined();
    expect(config.provider).toBeUndefined();
    expect(config.update).toBe("disable");
    expect(config.agents.build.model).toContain("#");
    expect(config.permissions).toBeArray();

    const directory = await renderAgents(provider);
    const hostConfig = { ...config, plugins: [] };
    await using host = await createHost(JSON.stringify(hostConfig), [], undefined, directory);
    const loaded = await host.config.get();
    expect(
      loaded.some((entry) => entry.type === "document" && entry.info.default_agent === "build"),
    ).toBe(true);
    const plugins = await host.plugin.list({ location: { directory: import.meta.dir } });
    expect(plugins.data.filter((plugin) => plugin.state.status === "failed")).toEqual([]);
    const session = await host.session.create({
      agent: "build",
      location: { directory: import.meta.dir },
    });
    await host.session.shell({ sessionID: session.id, command: "true" });
    await host.session.wait({ sessionID: session.id });
    const agents = await host.agent.list({ location: { directory: import.meta.dir } });
    expect(agents.data.map((agent) => agent.id)).toContain("build");
    if (provider === "anthropic") {
      const evaluate = (agent: string, action: string, resource: string) =>
        host.permission.create({
          sessionID: session.id,
          action,
          resources: [resource],
          agent,
        });
      expect((await evaluate("plan", "edit", "file.txt")).effect).toBe("deny");
      expect((await evaluate("plan", "subagent", "explore")).effect).toBe("allow");
      expect((await evaluate("plan", "subagent", "acceptance")).effect).toBe("deny");
      expect((await evaluate("acceptance", "subagent", "explore")).effect).toBe("deny");
      expect((await evaluate("researcher", "skill", "research-cli")).effect).toBe("allow");
      expect((await evaluate("researcher", "shell", "research query")).effect).toBe("allow");
      expect((await evaluate("researcher", "shell", "ls")).effect).toBe("deny");
    }
  }
});

test("renders provider blocks and authentication only for the selected provider", () => {
  const anthropic = render("anthropic");
  expect(anthropic.agents.build.model).toStartWith("anthropic/");
  expect(anthropic.plugins).toContain("github:rcdailey/opencode-claude-auth#integration");
  expect(Object.keys(anthropic.providers)).toEqual(["anthropic"]);

  const openai = render("openai");
  expect(openai.agents.build.model).toStartWith("openai/");
  expect(openai.plugins).not.toContain("github:rcdailey/opencode-claude-auth#integration");
  expect(openai.providers).toEqual({});
});

test("the V2 host evaluates representative global permissions", async () => {
  const config = render("anthropic");
  config.plugins = [];
  const directory = await renderAgents("anthropic");
  await using host = await createHost(JSON.stringify(config), [], undefined, directory);
  const session = await host.session.create({
    agent: "build",
    location: { directory: import.meta.dir },
  });
  await host.session.shell({ sessionID: session.id, command: "true" });
  await host.session.wait({ sessionID: session.id });
  const agents = await host.agent.list({
    location: { directory: import.meta.dir },
  });
  expect(agents.data.map((agent) => agent.id)).toContain("build");

  const allowed = await host.permission.create({
    sessionID: session.id,
    action: "read",
    resources: ["README.md"],
    agent: "build",
  });
  expect(allowed.effect).toBe("allow");
  expect(
    (
      await host.permission.create({
        sessionID: session.id,
        action: "read",
        resources: ["report.pdf"],
        agent: "build",
      })
    ).effect,
  ).toBe("deny");
  expect(
    (
      await host.permission.create({
        sessionID: session.id,
        action: "skill",
        resources: ["research-cli"],
        agent: "build",
      })
    ).effect,
  ).toBe("deny");
  expect(
    (
      await host.permission.create({
        sessionID: session.id,
        action: "shell",
        resources: ["gh api user --method GET"],
        agent: "build",
      })
    ).effect,
  ).toBe("allow");

  const denied = await host.permission.create({
    sessionID: session.id,
    action: "shell",
    resources: ["git commit -m test"],
    agent: "build",
  });
  expect(denied.effect).toBe("deny");

  const expectAsk = async (resource: string) => {
    const result = await host.permission.create({
      sessionID: session.id,
      action: "shell",
      resources: [resource],
      agent: "build",
    });
    expect(result.effect).toBe("ask");
    const requests = await host.permission.list({ sessionID: session.id });
    expect(requests).toHaveLength(1);
    await host.permission.reply({
      sessionID: session.id,
      requestID: requests[0].id,
      decision: "once",
    });
  };
  await expectAsk("git push");
  await expectAsk("gh pr create --title test");
});
