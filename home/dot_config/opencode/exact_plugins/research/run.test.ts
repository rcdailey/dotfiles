import { expect, test } from "bun:test";
import { randomUUID } from "node:crypto";
import { ResearchError, runResearch } from "./run.ts";

// Runs the real CLI with an invocation that fails before any network access.
test("failures are recorded only in the calling session's ledger", async () => {
  const session = `test-${randomUUID()}`;
  const other = `test-${randomUUID()}`;

  const failure = runResearch(session, ["scout", "orient", "not-a-repo"]);

  await expect(failure).rejects.toBeInstanceOf(ResearchError);
  await expect(failure).rejects.toThrow("OWNER/REPO");
  expect(await runResearch(session, ["errors"])).toContain(
    "Input: research scout orient not-a-repo",
  );
  expect(await runResearch(other, ["errors"])).toBe("No tool failures recorded.");
}, 60_000);

// Only agents following the goal protocol are refused retrieval before recording goals.
test("goal-protocol callers must record goals before retrieval", async () => {
  const session = `test-${randomUUID()}`;
  const retrieval = ["scout", "orient", "not-a-repo"];

  await expect(runResearch(session, retrieval, undefined, true)).rejects.toThrow("research_plan");
  await runResearch(session, ["plan", "--", "goal one"], undefined, true);
  await expect(runResearch(session, retrieval, undefined, true)).rejects.toThrow("OWNER/REPO");
}, 60_000);
