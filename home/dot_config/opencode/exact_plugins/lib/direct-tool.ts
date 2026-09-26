/**
 * Tool options that list a plugin tool directly instead of in Code Mode. Plugin tools default to
 * Code Mode, where agents reach them only through `execute`, whose `fetch` has no permission
 * check. Direct tools let an agent allow them by name while `execute` stays denied.
 */
export const DIRECT_TOOL = { codemode: false } as const;
