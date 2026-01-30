import type { Plugin } from "@opencode-ai/plugin"
import { readFileSync, existsSync } from "fs"
import { parse as parseJsonc } from "jsonc-parser"
import { minimatch } from "minimatch"
import { basename, join } from "path"
import { homedir } from "os"

type SkillConfig = Record<string, string[]>

interface ResolvedRule {
  pattern: string
  skill: string
}

const CONFIG_FILENAME = "skill-enforcer.jsonc"
const EDIT_TOOLS = ["edit", "write", "patch", "multiedit"]

function loadConfig(configPath: string): SkillConfig {
  if (!existsSync(configPath)) return {}
  try {
    const content = readFileSync(configPath, "utf-8")
    return parseJsonc(content) ?? {}
  } catch {
    return {}
  }
}

function mergeConfigs(global: SkillConfig, project: SkillConfig): SkillConfig {
  const merged: SkillConfig = {}

  for (const [skill, patterns] of Object.entries(global)) {
    merged[skill] = [...patterns]
  }

  for (const [skill, patterns] of Object.entries(project)) {
    merged[skill] = patterns
  }

  return merged
}

function buildRules(config: SkillConfig): ResolvedRule[] {
  const rules: ResolvedRule[] = []
  for (const [skill, patterns] of Object.entries(config)) {
    for (const pattern of patterns) {
      rules.push({ pattern, skill })
    }
  }
  return rules
}

function findRequiredSkill(filePath: string, rules: ResolvedRule[]): string | null {
  const fileName = basename(filePath)

  for (const { pattern, skill } of rules) {
    if (minimatch(fileName, pattern) || minimatch(filePath, pattern)) {
      return skill
    }
  }

  return null
}

function formatRejection(skill: string): string {
  return [
    `SKILL REQUIRED: Load the "${skill}" skill before editing this file.`,
    "You MUST follow the skill's guidance when retrying your edit.",
  ].join("\n")
}

export const SkillEnforcer: Plugin = async ({ directory }) => {
  const globalConfigPath = join(homedir(), ".config", "opencode", CONFIG_FILENAME)
  const projectConfigPath = join(directory, ".opencode", CONFIG_FILENAME)

  const globalConfig = loadConfig(globalConfigPath)
  const projectConfig = loadConfig(projectConfigPath)
  const config = mergeConfigs(globalConfig, projectConfig)
  const rules = buildRules(config)

  console.log(`[skill-enforcer] initialized with ${rules.length} rules`)
  if (rules.length === 0) {
    return {}
  }

  const loadedSkills = new Set<string>()

  return {
    event: async ({ event }) => {
      if (event.type === "session.created") {
        console.log("[skill-enforcer] session.created - clearing loaded skills")
        loadedSkills.clear()
      }
    },

    "tool.execute.before": async (input, output) => {
      // Track skill loading
      if (input.tool === "skill" && typeof output.args?.name === "string") {
        console.log(`[skill-enforcer] skill loaded: ${output.args.name}`)
        loadedSkills.add(output.args.name)
        return
      }

      // Enforce skill requirements for edit tools
      if (!EDIT_TOOLS.includes(input.tool)) return

      const filePath = (output.args?.filePath ?? output.args?.path) as string | undefined
      if (!filePath) return

      const requiredSkill = findRequiredSkill(filePath, rules)
      if (!requiredSkill) return

      console.log(`[skill-enforcer] checking ${filePath}, need: ${requiredSkill}, have: [${[...loadedSkills].join(", ")}]`)
      if (!loadedSkills.has(requiredSkill)) {
        throw new Error(formatRejection(requiredSkill))
      }
    },
  }
}
