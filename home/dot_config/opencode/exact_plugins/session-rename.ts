import { type Plugin, tool } from "@opencode-ai/plugin";

export const SessionRename: Plugin = async ({ client }) => {
  return {
    tool: {
      session_rename: tool({
        description:
          "Rename the current session. Sets the session title that appears " +
          "in the session list. Use this to give the session a meaningful, " +
          "searchable name based on what was accomplished or reviewed.",
        args: {
          title: tool.schema.string().max(100).describe("New session title (max 100 chars)"),
        },
        async execute(args, context) {
          await client.session.update({
            path: { id: context.sessionID },
            body: { title: args.title },
          });
          return `Session renamed to: ${args.title}`;
        },
      }),
    },
  };
};
