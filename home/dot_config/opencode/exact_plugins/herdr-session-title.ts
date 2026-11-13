import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { Plugin } from "@opencode/plugin";

const run = promisify(execFile);
const HERDR = process.env.HERDR_BIN_PATH || "herdr";
const SOURCE = "opencode-session-title";
/** Linear (`ENG-142`) or GitHub (`#412`) key leading the title; see opencode-session-title.md. */
const ISSUE_PREFIX = /^([A-Z][A-Z0-9]*-\d+|#\d+)\s+(.+)$/;
/** OpenCode's placeholder for a session not yet titled, current or historical form. */
const FALLBACK_TITLE = /^(New|Child) session - \d{4}-\d{2}-\d{2}T[\d:.]+Z$/;

type HerdrPane = { pane_id: string; agent_session?: { agent: string; value: string } };

/**
 * Reports each OpenCode session title to the herdr pane running it as `$issue` and `$title`
 * sidebar tokens (see `ui.sidebar.agents.rows_by_agent` in herdr's config.toml). The OpenCode
 * service is shared across panes, so the pane is found through herdr's OpenCode integration, which
 * records each pane's session ID. Titles are reported when a session is renamed or prompted, and
 * for every open pane when the plugin loads, so restored panes show their title without a prompt.
 */
export const HerdrSessionTitle = {
  id: "local.herdr-session-title",
  async setup(ctx) {
    const opencodePanes = async () => {
      const { stdout } = await run(HERDR, ["pane", "list"], { timeout: 10_000 });
      const panes: HerdrPane[] = JSON.parse(stdout).result.panes;
      return panes.filter((pane) => pane.agent_session?.agent === "opencode");
    };

    const report = async (paneID: string, title: string | undefined) => {
      const args = ["pane", "report-metadata", paneID, "--source", SOURCE];
      if (!title || FALLBACK_TITLE.test(title)) {
        args.push("--clear-token", "issue", "--clear-token", "title");
      } else {
        const [, issue, subject] = title.match(ISSUE_PREFIX) ?? [];
        args.push(...(issue ? ["--token", `issue=${issue}`] : ["--clear-token", "issue"]));
        args.push("--token", `title=${subject ?? title}`);
      }
      await run(HERDR, args, { timeout: 10_000 });
    };

    const publish = async (sessionID: string, title?: string) => {
      const panes = (await opencodePanes()).filter(
        (pane) => pane.agent_session?.value === sessionID,
      );
      if (panes.length === 0) return;
      const resolved = title ?? (await ctx.session.get({ sessionID })).title;
      for (const pane of panes) await report(pane.pane_id, resolved);
    };

    // Outside herdr every call fails; the sidebar is optional, so failures are ignored
    let queue = Promise.resolve();
    const enqueue = (task: () => Promise<void>) => {
      queue = queue.then(task).catch(() => {});
    };

    enqueue(async () => {
      for (const pane of await opencodePanes()) {
        const sessionID = pane.agent_session!.value;
        // Sessions of other locations are unavailable here; their own plugin instance reports them
        const session = await ctx.session.get({ sessionID }).catch(() => undefined);
        if (session) await report(pane.pane_id, session.title);
      }
    });
    await ctx.session.hook("prompt", ({ sessionID }) => {
      enqueue(() => publish(sessionID));
    });
    const controller = new AbortController();
    void (async () => {
      const events = ctx.event.subscribe({
        types: ["session.renamed"],
        signal: controller.signal,
      });
      for await (const event of events) {
        const { sessionID, title } = event.data;
        enqueue(() => publish(sessionID, title));
      }
    })();
    return () => controller.abort();
  },
} satisfies Plugin.Plugin;

export default HerdrSessionTitle;
