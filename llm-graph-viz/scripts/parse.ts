// Reference parser for format C (ASCII + [Cross-Links] footer).
// Parses the footer back into an edge set; the tree part provides node+parent.
// Derived from packages/graph-tools/scripts/L3-BF-191-ascii-parser.ts on
// voicetree-public @ commit f7042f61, simplified for the public schema.
//
// Use this to score a model's emit-side output: prompt a model with format C,
// ask it to produce a modified graph, and then round-trip its response through
// this parser to check how much survived.

import type {Graph, Node, Edge} from './graph.js'

type ParsedFooterEdge = {src: string; tgt: string; label?: string}

export function parseAsciiFooter(ascii: string): {nodes: readonly Node[]; edges: readonly Edge[]} {
    const lines: readonly string[] = ascii.split('\n')

    // Split tree vs footer by locating `[Cross-Links]`.
    const footerStart: number = lines.findIndex(l => l.trim() === '[Cross-Links]')
    const treeLines: readonly string[] = footerStart === -1 ? lines : lines.slice(0, footerStart)
    const footerLines: readonly string[] = footerStart === -1 ? [] : lines.slice(footerStart + 1)

    const nodes: Node[] = parseTreeNodes(treeLines)
    const edges: readonly Edge[] = parseFooter(footerLines)
    return {nodes, edges}
}

// Tree parser. Handles both formats A/C (no @[id] on tree lines) by falling
// back to title-based synthetic IDs when a line has no path ID.
//
// Line shape for A/C:
//   ├── ▢ Folder Name
//   │   └── · Node Title
//   │           ⇢ Other Title         (inline cross-edge; skipped here — footer is authoritative)
//
// Indent step = 4 chars per depth level.
function parseTreeNodes(lines: readonly string[]): Node[] {
    const out: Node[] = []
    const stack: {id: string; depth: number}[] = []
    const TREE_RE: RegExp = /^(?<indent>(?:│\s{3}|\s{4})*)(?:├──\s|└──\s)?(?<rest>.*)$/
    const MARKER_RE: RegExp = /^(?<marker>[▢·▣●])\s(?<body>.+)$/
    const ARROW_RE: RegExp = /^⇢\s/

    for (const raw of lines) {
        const m: RegExpMatchArray | null = raw.match(TREE_RE)
        if (!m) continue
        const indent: string = m.groups!['indent']!
        const rest: string = m.groups!['rest']!
        if (ARROW_RE.test(rest)) continue  // inline edge, handled by footer
        const mm: RegExpMatchArray | null = rest.match(MARKER_RE)
        if (!mm) continue
        const body: string = mm.groups!['body']!.trim()
        const idMatch: RegExpMatchArray | null = body.match(/^(?<title>.+?)\s@\[(?<id>[^\]]+)\]$/)
        const title: string = idMatch ? idMatch.groups!['title']! : body
        const id: string = idMatch ? idMatch.groups!['id']! : synthId(title)
        const depth: number = indent.length / 4

        while (stack.length > 0 && stack[stack.length - 1]!.depth >= depth) stack.pop()
        const parent: string | null = stack.length === 0 ? null : stack[stack.length - 1]!.id
        out.push({id, title, parent})
        stack.push({id, depth})
    }
    return out
}

function parseFooter(lines: readonly string[]): readonly Edge[] {
    const out: Edge[] = []
    const FOOTER_RE: RegExp = /^\s*@\[(?<src>[^\]]+)\]\s⇢\s@\[(?<tgt>[^\]]+)\](?:\s\[(?<label>[^\]]+)\])?\s*$/
    for (const raw of lines) {
        if (raw.trim() === '' || raw.trim().startsWith('Legend')) continue
        if (raw.includes('=') && !raw.includes('⇢')) continue
        const m: RegExpMatchArray | null = raw.match(FOOTER_RE)
        if (!m) continue
        const {src, tgt, label} = m.groups!
        out.push(label ? {src: src!, tgt: tgt!, label} : {src: src!, tgt: tgt!})
    }
    return out
}

function synthId(title: string): string {
    return `title:${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`
}

// ── Fidelity scorer ───────────────────────────────────────────────────────────
// Given a reconstructed graph and the ground-truth graph, compute node and edge
// fidelity. This is the measurement used in results/bf-191-bf-192.md.

export type Fidelity = {
    readonly nodeCount: {truth: number; reconstructed: number; matched: number}
    readonly edgeCount: {truth: number; reconstructed: number; matched: number}
    readonly nodeFidelity: number   // matched / truth
    readonly edgeFidelity: number   // matched / truth (recall)
    readonly edgePrecision: number  // matched / reconstructed
}

// Node fidelity matching strategy:
// Format C does not inline @[id] on tree lines (only on footer edges). So
// reconstructed node IDs are either synthesized from titles (our parser) or
// derived from (parent_title_chain, title) tuples. We therefore match nodes by
// their (parent-title-chain || title) signature. This matches the internal
// BF-191 parser's `(folder-path :: title)` keying on commit f7042f61.
export function scoreFidelity(truth: Graph, reconstructed: {nodes: readonly Node[]; edges: readonly Edge[]}): Fidelity {
    function chainOf(nodes: readonly Node[], id: string): string {
        const byId: Map<string, Node> = new Map(nodes.map(n => [n.id, n]))
        const out: string[] = []
        let cur: string | null = id
        while (cur !== null) {
            const n: Node | undefined = byId.get(cur)
            if (!n) break
            out.unshift(n.title)
            cur = n.parent
        }
        return out.join(' :: ')
    }
    const truthKey: (n: Node) => string = n => chainOf(truth.nodes, n.id)
    const reconKey: (n: Node) => string = n => chainOf(reconstructed.nodes, n.id)
    const truthKeys: Set<string> = new Set(truth.nodes.map(truthKey))
    const reconKeys: Set<string> = new Set(reconstructed.nodes.map(reconKey))
    const matchedNodes: number = [...truthKeys].filter(k => reconKeys.has(k)).length

    const truthEdgeKeys: Set<string> = new Set(truth.edges.map(e => `${e.src}\u0000${e.tgt}`))
    const reconstructedEdgeKeys: Set<string> = new Set(reconstructed.edges.map(e => `${e.src}\u0000${e.tgt}`))
    const matchedEdges: number = [...truthEdgeKeys].filter(k => reconstructedEdgeKeys.has(k)).length

    return {
        nodeCount: {truth: truthKeys.size, reconstructed: reconKeys.size, matched: matchedNodes},
        edgeCount: {truth: truthEdgeKeys.size, reconstructed: reconstructedEdgeKeys.size, matched: matchedEdges},
        nodeFidelity: truthKeys.size === 0 ? 1 : matchedNodes / truthKeys.size,
        edgeFidelity: truthEdgeKeys.size === 0 ? 1 : matchedEdges / truthEdgeKeys.size,
        edgePrecision: reconstructedEdgeKeys.size === 0 ? 1 : matchedEdges / reconstructedEdgeKeys.size,
    }
}

if (import.meta.url === `file://${process.argv[1]}`) {
    const [, , mode, arg1, arg2] = process.argv
    if (mode === 'parse' && arg1) {
        const fs = await import('node:fs')
        const ascii: string = fs.readFileSync(arg1, 'utf8')
        const {nodes, edges} = parseAsciiFooter(ascii)
        process.stdout.write(JSON.stringify({nodes, edges}, null, 2) + '\n')
    } else if (mode === 'score' && arg1 && arg2) {
        const fs = await import('node:fs')
        const {loadGraph} = await import('./graph.js')
        const truth: Graph = loadGraph(arg1)
        const ascii: string = fs.readFileSync(arg2, 'utf8')
        const fid: Fidelity = scoreFidelity(truth, parseAsciiFooter(ascii))
        process.stdout.write(JSON.stringify(fid, null, 2) + '\n')
    } else {
        console.error('usage: parse.ts (parse <ascii.txt>) | (score <truth.json> <ascii.txt>)')
        process.exit(1)
    }
}
