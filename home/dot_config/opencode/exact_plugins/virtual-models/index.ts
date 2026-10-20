import { homedir } from "node:os";
import path from "node:path";
import type { Plugin } from "@opencode/plugin";

// Sets agent models from ~/.config/opencode/virtual-models.jsonc: the selected provider's map of
// agent ID to "provider/model#variant". Applies once at startup; open sessions keep their model.
//
// User plugins load before the built-in config plugin that reads agent Markdown files, so those
// agents do not exist yet when this runs. Updating them creates them early and the config plugin
// fills in the rest. For the same reason, an `agents.<id>.model` in opencode.jsonc overrides this
// plugin, and mapping gaps cannot be detected here; pre-commit checks them instead.

type VirtualModels = { provider: string; providers: Record<string, Record<string, string>> };

const CONFIG_PATH = path.join(
  process.env.XDG_CONFIG_HOME || path.join(homedir(), ".config"),
  "opencode",
  "virtual-models.jsonc",
);

const parseRef = (ref: string) => {
  const [model, variant] = ref.split("#");
  const slash = model.indexOf("/");
  return {
    providerID: model.slice(0, slash),
    id: model.slice(slash + 1),
    ...(variant ? { variant } : {}),
  };
};

export const VirtualModels = {
  id: "local.virtual-models",
  async setup(ctx) {
    const config = Bun.JSONC.parse(await Bun.file(CONFIG_PATH).text()) as VirtualModels;
    const models = config.providers[config.provider];
    if (!models) throw new Error(`virtual-models.jsonc has no mapping for "${config.provider}"`);

    await ctx.agent.transform((agents) => {
      for (const [agentID, ref] of Object.entries(models)) {
        agents.update(agentID, (agent) => {
          // Model.Ref IDs are type-only brands; plugins have no runtime constructor for them.
          agent.model = parseRef(ref) as unknown as typeof agent.model;
        });
      }
    });
  },
} satisfies Plugin.Plugin;

export default VirtualModels;
