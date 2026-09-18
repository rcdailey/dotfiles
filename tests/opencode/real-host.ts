import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { Plugin } from "@opencode/plugin";
import { OpenCode } from "@opencode/sdk";

export async function createHost(
  content: string,
  plugins: Plugin.Plugin[] = [],
  databasePath?: string,
  configDirectory?: string,
) {
  const directory = configDirectory ?? (await mkdtemp(join(tmpdir(), "opencode-host-test-")));
  return OpenCode.create({
    config: { content, directory, project: false },
    database: databasePath ? { path: databasePath } : undefined,
    fs: { filewatcher: false },
    instances: plugins.length
      ? {
          key: () => "test",
          configure: () => ({ plugins }),
        }
      : undefined,
    models: { fetch: false, snapshot: true },
  });
}
