import { mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";

const sourceRoot = join(import.meta.dir, "../../home/dot_config/opencode/exact_plugins");
const outputRoot = join(import.meta.dir, ".tmp");

export async function loadPlugin<T>(name: string): Promise<T> {
  await mkdir(outputRoot, { recursive: true });
  const source = join(sourceRoot, name);
  const target = join(outputRoot, basename(name, ".tmpl"));
  const contents = name.endsWith(".tmpl") ? render(source) : await readFile(source);
  await writeFile(target, contents);
  return import(`${target}?v=${Date.now()}`) as Promise<T>;
}

function render(source: string): Uint8Array {
  const result = Bun.spawnSync(["chezmoi", "execute-template", "--file", source]);
  if (result.exitCode !== 0) throw new Error(result.stderr.toString());
  return result.stdout;
}
