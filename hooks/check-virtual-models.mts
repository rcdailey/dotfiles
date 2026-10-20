#!/usr/bin/env bun
// Fails when an enabled OpenCode agent lacks a model mapping under any provider in
// virtual-models.jsonc, or when providers map different agents. The virtual-models plugin cannot
// detect gaps at runtime because agent files load after it runs.

import { readdirSync } from "node:fs";
import path from "node:path";

const OPENCODE = path.join(import.meta.dir, "..", "home", "dot_config", "opencode");

// Built-in agents this setup keeps enabled; custom agents come from agent files.
const BUILT_IN_AGENTS = ["build", "explore", "title", "compaction"];

const render = (file: string) => {
  const result = Bun.spawnSync(["chezmoi", "execute-template", "--file", path.join(OPENCODE, file)]);
  if (result.exitCode !== 0) throw new Error(`chezmoi failed to render ${file}: ${result.stderr}`);
  return Bun.JSONC.parse(result.stdout.toString());
};

type Agents = Record<string, { disabled?: boolean }>;
type VirtualModels = { providers: Record<string, Record<string, string>> };

const disabled = Object.entries((render("opencode.jsonc.tmpl") as { agents?: Agents }).agents ?? {})
  .filter(([, agent]) => agent.disabled)
  .map(([id]) => id);

const agentFiles = readdirSync(path.join(OPENCODE, "exact_agents"))
  .filter((name) => /\.md(\.tmpl)?$/.test(name))
  .map((name) => name.replace(/\.md(\.tmpl)?$/, ""));

const required = [...new Set([...BUILT_IN_AGENTS, ...agentFiles])]
  .filter((id) => !disabled.includes(id))
  .sort();

const { providers } = render("virtual-models.jsonc.tmpl") as VirtualModels;

const errors = Object.entries(providers).flatMap(([provider, models]) => [
  ...required
    .filter((id) => !(id in models))
    .map((id) => `${provider}: missing mapping for agent "${id}"`),
  ...Object.keys(models)
    .filter((id) => !required.includes(id))
    .map((id) => `${provider}: mapping for unknown or disabled agent "${id}"`),
]);

if (errors.length > 0) {
  console.error(`virtual-models.jsonc.tmpl:\n${errors.map((error) => `  ${error}`).join("\n")}`);
  process.exit(1);
}
