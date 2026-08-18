const promptUrl = new URL("./prompt.md", import.meta.url);

export default function createReviewCommand() {
  return {
    name: "review",
    description: "Code review orchestrator; selects PRs and delegates each to the reviewer agent",
    async execute(args: string[]) {
      const prompt = await Bun.file(promptUrl).text();
      return prompt.replaceAll("$ARGUMENTS", args.join(" "));
    },
  };
}
