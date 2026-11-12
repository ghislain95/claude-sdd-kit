// What the cards need to know about the project: the OpenSpec change names (a commit scoped to one is
// tracked, a cited file under one is found) and the recent commits (a commit card says when it landed).

import type { EngineInterface } from 'claude-code'

import type { CardFacts } from '../types'

const GIT_CANDIDATES = ['git', '/opt/homebrew/bin/git', '/usr/local/bin/git', '/usr/bin/git']

export async function resolveGit($: EngineInterface): Promise<string> {
  for (const candidate of GIT_CANDIDATES) {
    try {
      const result = await $.process.run([candidate, '--version'], { timeoutMs: 3000 })
      if (result.exitCode === 0) return candidate
    } catch {
      // try the next one
    }
  }
  return 'git'
}

async function directories($: EngineInterface, path: string): Promise<string[]> {
  const entries = await $.fs.list(path).catch(() => [])
  return entries.filter(entry => entry.kind === 'dir').map(entry => entry.name)
}

/** Change folders under openspec/changes/, and the archived ones without their date prefix. */
async function changeNames($: EngineInterface, root: string): Promise<string[]> {
  const changes = `${root}/openspec/changes`
  const active = (await directories($, changes)).filter(name => name !== 'archive')
  const archived = (await directories($, `${changes}/archive`)).map(name => name.replace(/^\d{4}-\d{2}-\d{2}-/, ''))
  return [...new Set([...active, ...archived.slice(-20)])]
}

async function recentCommits($: EngineInterface, root: string, git: string): Promise<CardFacts['recentCommits']> {
  try {
    const result = await $.process.run([git, 'log', '-20', '--format=%h%x09%s'], { cwd: root, timeoutMs: 10000 })
    if (result.exitCode !== 0) return []
    return result.stdout
      .split('\n')
      .filter(line => line.includes('\t'))
      .map(line => ({ hash: line.split('\t')[0] ?? '', subject: line.split('\t').slice(1).join('\t') }))
  } catch {
    return []
  }
}

export async function collectFacts($: EngineInterface, root: string, git: string): Promise<CardFacts> {
  const [names, commits] = await Promise.all([changeNames($, root), recentCommits($, root, git)])
  return { changeNames: names, recentCommits: commits }
}
