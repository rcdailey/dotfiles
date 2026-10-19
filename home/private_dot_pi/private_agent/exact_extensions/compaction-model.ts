import {
  compact,
  type ExtensionAPI,
  type ExtensionContext,
  getAgentDir,
  SettingsManager,
} from "@earendil-works/pi-coding-agent";

// Summarizes compactions with the model in settings.json `compactionModel`
// ({ "model": "provider/modelId", "thinkingLevel": "low" }) instead of the session model. It
// reuses pi's native compact(), so only the model changes. On a missing key, unknown model, auth
// failure, or error, it returns nothing and pi compacts with the session model.

type ThinkingLevel = Parameters<typeof compact>[6];

interface Config {
  model: string;
  thinkingLevel?: ThinkingLevel;
}

const warn = (message: string) => console.warn(`[compaction-model] ${message}`);

function loadConfig(ctx: ExtensionContext): Config | undefined {
  const trusted = ctx.isProjectTrusted();
  const settings = SettingsManager.create(ctx.cwd, getAgentDir(), { projectTrusted: trusted });
  const project = trusted ? settings.getProjectSettings() : {};
  const raw =
    (project as Record<string, unknown>).compactionModel ??
    (settings.getGlobalSettings() as Record<string, unknown>).compactionModel;
  if (typeof raw !== "object" || raw === null) return;
  const { model, thinkingLevel } = raw as Record<string, unknown>;
  if (typeof model !== "string") return;
  return { model, thinkingLevel: thinkingLevel as ThinkingLevel };
}

export default function compactionModel(pi: ExtensionAPI) {
  pi.on("session_before_compact", async (event, ctx) => {
    const config = loadConfig(ctx);
    if (!config) return;

    const slash = config.model.indexOf("/");
    const model =
      slash > 0
        ? ctx.modelRegistry.find(config.model.slice(0, slash), config.model.slice(slash + 1))
        : undefined;
    if (!model) return warn(`Unknown model ${config.model}; using the session model.`);

    const auth = await ctx.modelRegistry.getApiKeyAndHeaders(model);
    if (!auth.ok)
      return warn(`No auth for ${config.model}: ${auth.error}; using the session model.`);

    // pi marks hook-provided compactions `fromHook` and then ignores their file lists when
    // preparing the next compaction. Restore them so read and modified files carry forward.
    const previous = event.branchEntries.findLast((entry) => entry.type === "compaction");
    const details = (previous as { details?: { readFiles?: unknown; modifiedFiles?: unknown } })
      ?.details;
    for (const [paths, target] of [
      [details?.readFiles, event.preparation.fileOps.read],
      [details?.modifiedFiles, event.preparation.fileOps.edited],
    ] as const) {
      if (Array.isArray(paths)) for (const path of paths) target.add(path);
    }

    try {
      const compaction = await compact(
        event.preparation,
        model,
        auth.apiKey,
        auth.headers,
        event.customInstructions,
        event.signal,
        config.thinkingLevel,
        undefined,
        auth.env,
      );
      return { compaction };
    } catch (error) {
      if (!event.signal.aborted)
        warn(`${config.model} failed (${error}); using the session model.`);
    }
  });
}
