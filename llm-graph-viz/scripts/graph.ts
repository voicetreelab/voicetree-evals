// Shared graph types for the llm-graph-viz benchmark.
// A fixture on disk is a JSON file with this shape.
//
// Every node has a stable `id` (used in all formats for path/edge references).
// `parent` expresses the primary containment hierarchy (folder tree / kanban
// column / project breakdown — whichever is the domain's primary decomposition).
// `edges` are the cross-cutting non-tree edges — wikilinks, dependencies, refs.
//
// Invariants enforced by `verifyGraph`:
// - IDs unique.
// - Every parent reference resolves.
// - Parent relation is acyclic (primary tree is a forest).
// - Every edge src/tgt exists in `nodes`.
// - No self-edges in `edges` (self-loops are never interesting for this benchmark).
//
// Design note: we intentionally do NOT model the primary tree as entries in
// `edges`. Format B (mermaid) and H (JSON-dump) need to know which edges are
// structural-tree vs cross-cutting; conflating them forces every renderer to
// re-derive the distinction.

import * as fs from 'node:fs'

export type Node = {
    readonly id: string
    readonly title: string
    readonly parent: string | null
}

export type Edge = {
    readonly src: string
    readonly tgt: string
    readonly label?: string
}

export type Graph = {
    readonly nodes: readonly Node[]
    readonly edges: readonly Edge[]
}

export function loadGraph(path: string): Graph {
    const raw: string = fs.readFileSync(path, 'utf8')
    const parsed: unknown = JSON.parse(raw)
    verifyGraph(parsed as Graph)
    return parsed as Graph
}

export function verifyGraph(g: Graph): void {
    const ids: Set<string> = new Set()
    for (const n of g.nodes) {
        if (ids.has(n.id)) throw new Error(`Duplicate node id: ${n.id}`)
        ids.add(n.id)
    }
    for (const n of g.nodes) {
        if (n.parent !== null && !ids.has(n.parent)) {
            throw new Error(`Node ${n.id} has missing parent ${n.parent}`)
        }
    }
    // Acyclic parent relation: follow each node up to a root in ≤ N steps.
    const N: number = g.nodes.length
    for (const n of g.nodes) {
        let cur: Node | undefined = n
        for (let i = 0; i < N + 1; i++) {
            if (cur === undefined || cur.parent === null) break
            cur = g.nodes.find(x => x.id === cur!.parent)
        }
        if (cur !== undefined && cur.parent !== null) {
            throw new Error(`Parent cycle detected through ${n.id}`)
        }
    }
    for (const e of g.edges) {
        if (!ids.has(e.src)) throw new Error(`Edge src not found: ${e.src}`)
        if (!ids.has(e.tgt)) throw new Error(`Edge tgt not found: ${e.tgt}`)
        if (e.src === e.tgt) throw new Error(`Self-edge not permitted: ${e.src}`)
    }
}

export function children(g: Graph, parentId: string | null): readonly Node[] {
    return g.nodes.filter(n => n.parent === parentId)
}

export function descendants(g: Graph, rootId: string): readonly Node[] {
    const out: Node[] = []
    const stack: readonly Node[] = children(g, rootId)
    const queue: Node[] = [...stack]
    while (queue.length > 0) {
        const n: Node = queue.shift()!
        out.push(n)
        for (const c of children(g, n.id)) queue.push(c)
    }
    return out
}

export function pathToRoot(g: Graph, id: string): readonly string[] {
    const out: string[] = []
    let cur: string | null = id
    while (cur !== null) {
        out.push(cur)
        const node: Node | undefined = g.nodes.find(n => n.id === cur)
        cur = node?.parent ?? null
    }
    return out
}
