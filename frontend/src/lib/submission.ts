export type RankedCandidate = {
  candidate_id: string
  rank: number
  score: number
  reasoning: string
}

export function parseSubmissionCsv(csv: string): RankedCandidate[] {
  const lines = csv.trim().split("\n")
  if (lines.length < 2) return []

  return lines.slice(1).map((line) => {
    const commaIdx = line.indexOf(",")
    const secondComma = line.indexOf(",", commaIdx + 1)
    const thirdComma = line.indexOf(",", secondComma + 1)

    const candidate_id = line.slice(0, commaIdx)
    const rank = Number(line.slice(commaIdx + 1, secondComma))
    const score = Number(line.slice(secondComma + 1, thirdComma))
    const reasoning = line.slice(thirdComma + 1).replace(/^"|"$/g, "")

    return { candidate_id, rank, score, reasoning }
  })
}

export async function loadSubmission(): Promise<RankedCandidate[]> {
  const res = await fetch("/submission.csv")
  if (!res.ok) throw new Error("Could not load submission.csv")
  const text = await res.text()
  return parseSubmissionCsv(text)
}

export function normalizeScore(score: number, min: number, max: number): number {
  if (max === min) return 50
  return ((score - min) / (max - min)) * 100
}

export function extractSignals(reasoning: string): string[] {
  const signals: string[] = []
  if (reasoning.includes("retrieval")) signals.push("Retrieval")
  if (reasoning.includes("ranking") || reasoning.includes("vector-search"))
    signals.push("Ranking / Vector DB")
  if (reasoning.includes("production ML") || reasoning.includes("deploy models"))
    signals.push("Production ML")
  if (reasoning.includes("hireability") || reasoning.includes("engagement"))
    signals.push("Hireability")
  if (reasoning.includes("Extensive background")) signals.push("Deep Experience")
  return signals
}
