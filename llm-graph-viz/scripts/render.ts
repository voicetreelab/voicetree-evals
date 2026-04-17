// Renderers for formats A, B, C, E, H. Formats F (graph-easy) and G (PNG) are
// thin wrappers over external tools — see `scripts/render-external.md` for how
// to invoke them.
//
// All renderers take a verified Graph (from ./graph.ts) and produce a string.
// Determinism: every renderer sorts children / edges / forests by id for stable
// byte output across runs. Comparisons across formats are only meaningful when
// both sides are deterministic.

import type {Graph, Node, Edge} from './graph.js'
import {children as childrenOf, pathToRoot} from './graph.js'
import {computeArboricity, undirectedEdgeKey} from './arboricity.js'

// ── Format A: Inline ASCII tree with ⇢ title arrows (lossy) ──────────────────
// This is the `tree`-style viewer format. Cross-edges are rendered inline after
// their source line as `⇢ <title>` — but only one title is emitted; duplicate
// titles collide, and unresolved targets are dropped.

export function renderAsciiLossy(g: Graph): string {
    const lines: string[] = []
    const edgesBySrc: Map<string, readonly Edge[]> = groupEdges(g.edges, e => e.src)
    const titleById: Map<string, string> = new Map(g.nodes.map(n => [n.id, n.title]))

    function walk(node: Node, prefix: string, isLast: boolean): void {
        const kids: readonly Node[] = sortNodes(childrenOf(g, node.id))
        const connector: string = isLast ? '└── ' : '├── '
        const marker: string = kids.length > 0 ? '▢' : '·'
        lines.push(`${prefix}${connector}${marker} ${node.title}`)

        const crossEdges: readonly Edge[] = edgesBySrc.get(node.id) ?? []
        for (const e of crossEdges) {
            const childPrefix: string = prefix + (isLast ? '    ' : '│   ')
            const arrowIndent: string = kids.length > 0 ? '    ' : '        '
            const tgtTitle: string | undefined = titleById.get(e.tgt)
            if (tgtTitle === undefined) continue  // lossy: unresolved targets dropped
            lines.push(`${childPrefix}${arrowIndent}⇢ ${tgtTitle}`)
        }
        for (let i = 0; i < kids.length; i++) {
            const nextPrefix: string = prefix + (isLast ? '    ' : '│   ')
            walk(kids[i]!, nextPrefix, i === kids.length - 1)
        }
    }

    const roots: readonly Node[] = sortNodes(childrenOf(g, null))
    for (let i = 0; i < roots.length; i++) walk(roots[i]!, '', i === roots.length - 1)
    return lines.join('\n') + '\n'
}

// ── Format B: Mermaid source ──────────────────────────────────────────────────
// Structurally lossless. All nodes declared up front, edges as `src --> tgt`.
// Note: in practice LLMs struggle with this because the src/tgt declarations
// and edges are arbitrarily far apart; see co-location metric in design.md.

export function renderMermaid(g: Graph): string {
    const lines: string[] = ['graph TD']
    const nodeDecl: (n: Node) => string = n => `  ${n.id}["${escapeMermaid(n.title)}"]`
    for (const n of sortNodes(g.nodes)) lines.push(nodeDecl(n))
    for (const n of sortNodes(g.nodes)) {
        if (n.parent !== null) lines.push(`  ${n.parent} --> ${n.id}`)
    }
    const sortedEdges: readonly Edge[] = [...g.edges].sort((a, b) =>
        a.src < b.src ? -1 : a.src > b.src ? 1 : a.tgt.localeCompare(b.tgt))
    for (const e of sortedEdges) lines.push(`  ${e.src} -.-> ${e.tgt}`)
    return lines.join('\n') + '\n'
}

function escapeMermaid(s: string): string {
    return s.replace(/"/g, '&quot;').replace(/[\[\]]/g, c => c === '[' ? '(' : ')')
}

// ── Format C: ASCII tree + [Cross-Links] footer ───────────────────────────────
// The shipped vt-graph format (commit f7042f61). Keeps the tree exactly as A,
// but appends a deterministic `[Cross-Links]` footer keyed by path IDs. Lossless
// on the rendered subgraph.

export function renderAsciiFooter(g: Graph): string {
    const tree: string = renderAsciiLossy(g)
    const footerLines: string[] = ['', '[Cross-Links]']
    const sortedEdges: readonly Edge[] = [...g.edges].sort((a, b) =>
        a.src.localeCompare(b.src) || a.tgt.localeCompare(b.tgt))
    for (const e of sortedEdges) {
        const label: string = e.label ? ` [${e.label}]` : ''
        footerLines.push(`  @[${e.src}] ⇢ @[${e.tgt}]${label}`)
    }
    footerLines.push('')
    footerLines.push('Legend:')
    footerLines.push('  @[id]   = stable node identifier (use in edge references)')
    footerLines.push('  ⇢       = directed edge src → tgt')
    footerLines.push('')
    return tree + footerLines.join('\n')
}

// ── Format E: Arboricity-bounded tree-cover ───────────────────────────────────
// Spine = parent hierarchy as a tree. Cross-cutting edges decomposed into k
// forests (k = arboricity upper bound). Each forest rendered as ● source, with
// ⇢ target children. Every edge's source-title and target-title are on adjacent
// lines — the co-location property.

export function renderTreeCover(g: Graph): string {
    const r = computeArboricity(g)
    const out: string[] = [
        '═══ arboricity report ═══',
        `nodes N         : ${r.nodeCount}`,
        `edges E         : ${r.edgeCount}`,
        `undirected      : ${r.undirectedEdgeCount}`,
        `density UB      : ${r.densityUB}`,
        `Nash-Williams LB: ${r.nashWilliamsLB}`,
        `greedy forests  : ${r.greedyUB}`,
        `degeneracy      : ${r.degeneracy}`,
        '',
        '═══ SPINE (containment hierarchy, no cross-edges) ═══',
    ]

    function walk(node: Node, prefix: string, isLast: boolean): void {
        const kids: readonly Node[] = sortNodes(childrenOf(g, node.id))
        const connector: string = isLast ? '└── ' : '├── '
        const marker: string = kids.length > 0 ? '▢' : '·'
        out.push(`${prefix}${connector}${marker} ${node.title} @[${node.id}]`)
        for (let i = 0; i < kids.length; i++) {
            walk(kids[i]!, prefix + (isLast ? '    ' : '│   '), i === kids.length - 1)
        }
    }
    const roots: readonly Node[] = sortNodes(childrenOf(g, null))
    for (let i = 0; i < roots.length; i++) walk(roots[i]!, '', i === roots.length - 1)

    // Group cross-edges by forest index.
    const titleById: Map<string, string> = new Map(g.nodes.map(n => [n.id, n.title]))
    const byForest: Map<number, Edge[]> = new Map()
    for (const e of g.edges) {
        const key: string = undirectedEdgeKey(e.src, e.tgt)
        const forestIdx: number = r.forestAssignment.get(key) ?? 0
        const arr: Edge[] = byForest.get(forestIdx) ?? []
        arr.push(e)
        byForest.set(forestIdx, arr)
    }

    const forestKeys: readonly number[] = [...byForest.keys()].sort((a, b) => a - b)
    for (const idx of forestKeys) {
        const edges: readonly Edge[] = byForest.get(idx)!
        out.push('')
        out.push(`═══ COVER FOREST ${idx + 1} (|E|=${edges.length}) ═══`)
        const bySrc: Map<string, Edge[]> = new Map()
        for (const e of edges) {
            const a: Edge[] = bySrc.get(e.src) ?? []
            a.push(e); bySrc.set(e.src, a)
        }
        const srcKeys: readonly string[] = [...bySrc.keys()].sort((a, b) => {
            const ta: string = titleById.get(a) ?? a
            const tb: string = titleById.get(b) ?? b
            return ta.localeCompare(tb)
        })
        for (const src of srcKeys) {
            const srcTitle: string = titleById.get(src) ?? src
            out.push(`● ${srcTitle} @[${src}]`)
            const outEdges: readonly Edge[] = [...bySrc.get(src)!].sort((a, b) =>
                (titleById.get(a.tgt) ?? a.tgt).localeCompare(titleById.get(b.tgt) ?? b.tgt))
            for (let i = 0; i < outEdges.length; i++) {
                const e: Edge = outEdges[i]!
                const last: boolean = i === outEdges.length - 1
                const connector: string = last ? '└── ' : '├── '
                const tgtTitle: string = titleById.get(e.tgt) ?? e.tgt
                const label: string = e.label ? ` [${e.label}]` : ''
                out.push(`${connector}⇢ ${tgtTitle} @[${e.tgt}]${label}`)
            }
        }
    }

    return out.join('\n') + '\n'
}

// ── Format H: Raw JSON state dump ─────────────────────────────────────────────
// Precision ceiling. For fidelity comparisons only — you're not going to prompt
// a model with this when you have a cheaper option that works.

export function renderJson(g: Graph): string {
    return JSON.stringify(g, null, 2) + '\n'
}

// ── Utilities ────────────────────────────────────────────────────────────────
function sortNodes(nodes: readonly Node[]): readonly Node[] {
    return [...nodes].sort((a, b) => a.id.localeCompare(b.id))
}

function groupEdges<T>(edges: readonly Edge[], key: (e: Edge) => string): Map<string, readonly Edge[]> {
    const out: Map<string, Edge[]> = new Map()
    const sorted: readonly Edge[] = [...edges].sort((a, b) =>
        a.tgt.localeCompare(b.tgt))
    for (const e of sorted) {
        const k: string = key(e)
        const arr: Edge[] = out.get(k) ?? []
        arr.push(e); out.set(k, arr)
    }
    return out
}

// ── CLI entry point ──────────────────────────────────────────────────────────

if (import.meta.url === `file://${process.argv[1]}`) {
    const [, , format, fixturePath] = process.argv
    if (!format || !fixturePath) {
        console.error('usage: render.ts <A|B|C|E|H> <fixture.json>')
        process.exit(1)
    }
    const {loadGraph} = await import('./graph.js')
    const g: Graph = loadGraph(fixturePath)
    const renderers: Record<string, (g: Graph) => string> = {
        A: renderAsciiLossy,
        B: renderMermaid,
        C: renderAsciiFooter,
        E: renderTreeCover,
        H: renderJson,
    }
    const fn: ((g: Graph) => string) | undefined = renderers[format.toUpperCase()]
    if (!fn) { console.error(`Unknown format: ${format}`); process.exit(1) }
    process.stdout.write(fn(g))
}
