import type { Plugin } from "@opencode/plugin";

export const SessionRename = {
  id: "local.session-rename",
  async setup(ctx) {
    await ctx.tool.transform((tools) => {
      tools.add({
        name: "session_rename",
        description:
          "Rename the current session. Sets the session title that appears " +
          "in the session list. Use this to give the session a meaningful, " +
          "searchable name based on what was accomplished or reviewed.",
        input: {
          type: "object",
          properties: {
            title: {
              type: "string",
              maxLength: 100,
              description: "New session title (max 100 chars)",
            },
          },
          required: ["title"],
          additionalProperties: false,
        },
        async execute(input, context) {
          if (!input || typeof input !== "object") throw new Error("title is required");
          const title = Reflect.get(input, "title");
          if (typeof title !== "string") throw new Error("title is required");
          await ctx.session.update({
            sessionID: context.sessionID,
            title,
          });
          return { content: `Session renamed to: ${title}` };
        },
      });
    });
  },
} satisfies Plugin.Plugin;

export default SessionRename;
