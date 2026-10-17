import { expect, test } from "bun:test";
import { randomUUID } from "node:crypto";
import { ResearchError, runResearch, shellWords } from "./run.ts";

test("argument strings split into the words a shell would pass", () => {
  expect(shellWords(`dotnet/sdk "NoCache|no-cache" --path 'src/Cli' -C 2`)).toEqual([
    "dotnet/sdk",
    "NoCache|no-cache",
    "--path",
    "src/Cli",
    "-C",
    "2",
  ]);
  expect(shellWords(String.raw`a\ b "say \"hi\"" '' `)).toEqual(["a b", 'say "hi"', ""]);
  expect(shellWords("   ")).toEqual([]);
});

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
