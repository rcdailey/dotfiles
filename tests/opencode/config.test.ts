import { expect, test } from "bun:test";
import { mkdir, mkdtemp, readdir, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parse } from "jsonc-parser";
import { createHost } from "./real-host.ts";

const template = join(import.meta.dir, "../../home/dot_config/opencode/opencode.jsonc.tmpl");
const agentSource = join(import.meta.dir, "../../home/dot_config/opencode/exact_agents");

function renderContent(env: "work" | "personal" | "other") {
  const result = Bun.spawnSync([
    "chezmoi",
    "execute-template",
    "--override-data",
    JSON.stringify({ env }),
    "--file",
    template,
  ]);
  if (result.exitCode !== 0) throw new Error(result.stderr.toString());
  return result.stdout.toString();
}

function render(env: "work" | "personal" | "other"): any {
  const errors: unknown[] = [];
  const config = parse(renderContent(env), errors, { allowTrailingComma: true });
  expect(errors).toEqual([]);
  return config;
}

async function renderAgents(env: "work" | "personal" | "other") {
  const directory = await mkdtemp(join(tmpdir(), "opencode-config-test-"));
  const agents = join(directory, "agents");
  await mkdir(agents);
  for (const name of await readdir(agentSource)) {
    if (!name.endsWith(".md") && !name.endsWith(".md.tmpl")) continue;
    const source = join(agentSource, name);
    let content: string;
    if (name.endsWith(".tmpl")) {
      const result = Bun.spawnSync([
        "chezmoi",
        "execute-template",
        "--override-data",
        JSON.stringify({ env }),
        "--file",
        source,
      ]);
      if (result.exitCode !== 0) throw new Error(result.stderr.toString());
      content = result.stdout.toString();
    } else {
      content = await readFile(source, "utf8");
    }
    await writeFile(join(agents, name.replace(/\.tmpl$/, "")), content);
  }
  return directory;
}

test("renders and loads native V2 configuration for every profile", async () => {
  for (const env of ["work", "personal", "other"] as const) {
    const config = render(env);
    expect(config.agent).toBeUndefined();
    expect(config.permission).toBeUndefined();
    expect(config.plugin).toBeUndefined();
    expect(config.provider).toBeUndefined();
    expect(config.update).toBe("disable");
    expect(config.agents.build.model).toContain("#");
    expect(config.permissions).toBeArray();

    const directory = await renderAgents(env);
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
    if (env === "other") {
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

test("keeps profile-specific providers and authentication", () => {
  const work = render("work");
  expect(work.plugins).toContain("opencode-claude-auth-v2@0.4.0-beta.2");
  expect(work.providers.anthropic.settings).toEqual({
    timeout: false,
    chunkTimeout: 60_000,
  });

  const personal = render("personal");
  expect(personal.plugins).not.toContain("opencode-claude-auth-v2@0.4.0-beta.2");
  expect(personal.providers.openai.models["gpt-5.6-sol"].limit).toEqual({
    context: 400_000,
    input: 272_000,
    output: 128_000,
  });

  const other = render("other");
  expect(other.providers).toEqual({});
  expect(other.agents.build.model).toStartWith("openai/");
});

test("resolves configured provider settings and model limits", async () => {
  for (const [env, providerID] of [
    ["work", "anthropic"],
    ["personal", "openai"],
  ] as const) {
    let modelEditor: any;
    const observer = {
      id: `test.provider-observer.${env}`,
      async setup(context: any) {
        await context.model.transform((models: any) => {
          modelEditor = models;
        });
      },
    };
    const config = render(env);
    config.plugins = [];
    const directory = await renderAgents(env);
    await using host = await createHost(JSON.stringify(config), [observer], undefined, directory);
    const session = await host.session.create({
      agent: "build",
      location: { directory: import.meta.dir },
    });
    await host.permission.list({ sessionID: session.id });
    const provider = modelEditor?.provider.get(providerID);
    expect(provider?.provider.id).toBe(providerID);

    if (env === "work") {
      expect(provider.provider.settings.timeout).toBe(false);
      expect(provider.provider.settings.chunkTimeout).toBe(60_000);
      continue;
    }
    expect(modelEditor.get("openai", "gpt-5.6-sol").limit).toEqual({
      context: 400_000,
      input: 272_000,
      output: 128_000,
    });
  }
});

test("the V2 host evaluates representative global permissions", async () => {
  const config = render("personal");
  config.plugins = [];
  const directory = await renderAgents("personal");
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
