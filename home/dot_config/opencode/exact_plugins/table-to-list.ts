import type { Plugin } from "@opencode-ai/plugin"

const DEFAULT_MAX_WIDTH = 80

export const TableToList: Plugin = async () => {
  return {
    "experimental.text.complete": async (
      _input: { sessionID: string; messageID: string; partID: string },
      output: { text: string }
    ) => {
      try {
        output.text = transformWideTables(output.text, DEFAULT_MAX_WIDTH)
      } catch (error) {
        output.text =
          output.text +
          "\n\n<!-- table-to-list transform failed: " +
          (error as Error).message +
          " -->"
      }
    },
  }
}

interface TableRow {
  cells: string[]
  isSeparator: boolean
}

function transformWideTables(text: string, maxWidth: number): string {
  const lines = text.split("\n")
  const result: string[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    if (isTableRow(line)) {
      const tableLines: string[] = [line]
      i++

      while (i < lines.length && isTableRow(lines[i])) {
        tableLines.push(lines[i])
        i++
      }

      const parsed = parseTable(tableLines)
      if (parsed && parsed.dataRows.length > 0) {
        const tableWidth = getMaxLineWidth(tableLines)

        if (tableWidth > maxWidth) {
          result.push(...convertToList(parsed.headers, parsed.dataRows))
        } else {
          result.push(...tableLines)
        }
      } else {
        result.push(...tableLines)
      }
    } else {
      result.push(line)
      i++
    }
  }

  return result.join("\n")
}

function isTableRow(line: string): boolean {
  const trimmed = line.trim()
  return (
    trimmed.startsWith("|") &&
    trimmed.endsWith("|") &&
    trimmed.split("|").length > 2
  )
}

function isSeparatorRow(line: string): boolean {
  const trimmed = line.trim()
  if (!trimmed.startsWith("|") || !trimmed.endsWith("|")) return false

  const cells = trimmed.split("|").slice(1, -1)
  return cells.length > 0 && cells.every((cell) => /^\s*:?-+:?\s*$/.test(cell))
}

function parseTable(
  lines: string[]
): { headers: string[]; dataRows: string[][] } | null {
  if (lines.length < 2) return null

  const rows: TableRow[] = lines.map((line) => ({
    cells: line
      .split("|")
      .slice(1, -1)
      .map((cell) => cell.trim()),
    isSeparator: isSeparatorRow(line),
  }))

  const separatorIndex = rows.findIndex((row) => row.isSeparator)
  if (separatorIndex === -1 || separatorIndex === 0) return null

  const headers = rows[separatorIndex - 1].cells
  const dataRows = rows
    .slice(separatorIndex + 1)
    .filter((row) => !row.isSeparator)
    .map((row) => row.cells)

  if (dataRows.length === 0) return null

  const colCount = headers.length
  const normalizedRows = dataRows.map((row) => {
    if (row.length < colCount) {
      return [...row, ...Array(colCount - row.length).fill("")]
    }
    return row.slice(0, colCount)
  })

  return { headers, dataRows: normalizedRows }
}

function getMaxLineWidth(lines: string[]): number {
  return Math.max(...lines.map((line) => line.length))
}

function convertToList(headers: string[], dataRows: string[][]): string[] {
  const result: string[] = []

  for (let rowIndex = 0; rowIndex < dataRows.length; rowIndex++) {
    const row = dataRows[rowIndex]

    const { identifier, colIndex: identifierCol } = findRowIdentifier(
      headers,
      row,
      rowIndex
    )

    result.push(`**${identifier}**`)

    for (let col = 0; col < headers.length; col++) {
      if (col === identifierCol) continue

      const header = headers[col]
      const value = row[col] || ""

      if (value.trim()) {
        result.push(`- ${header}: ${value}`)
      }
    }

    if (rowIndex < dataRows.length - 1) {
      result.push("")
    }
  }

  return result
}

function findRowIdentifier(
  headers: string[],
  row: string[],
  rowIndex: number
): { identifier: string; colIndex: number | null } {
  const identifierPatterns = [
    /^(name|title|id|key|scenario|option|command|flag|severity)$/i,
    /^#$/,
  ]

  for (const pattern of identifierPatterns) {
    const idx = headers.findIndex((h) => pattern.test(h.trim()))
    if (idx !== -1 && row[idx]?.trim()) {
      return { identifier: row[idx].trim(), colIndex: idx }
    }
  }

  // Fall back to first non-empty cell
  for (let i = 0; i < row.length; i++) {
    if (row[i]?.trim()) {
      return { identifier: row[i].trim(), colIndex: i }
    }
  }

  // Last resort: row number
  return { identifier: `Row ${rowIndex + 1}`, colIndex: null }
}
