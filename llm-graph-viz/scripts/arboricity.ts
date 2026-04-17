// Arboricity computation: Nash-Williams lower bound + greedy upper bound + degeneracy.
// For the benchmark's purposes we only need the greedy upper bound (which is what
// the tree-cover renderer actually uses to decide k). The tighter bounds are reported
// for diagnostic purposes — when LB < UB, it's a signal the tree-cover may be
// non-optimal (but still correct).
//
// Reference: Nash-Williams 1964; implementation follows the internal vt-graph version
// at packages/graph-tools/scripts/L3-BF-192-tree-cover-render.ts (f7042f61).

import type {Graph} from './graph.js'

export type ArboricityReport = {
    readonly nodeCount: number
    readonly edgeCount: number  // directed, non-self
    readonly undirectedEdgeCount: number  // after merging bidirectional pairs
    readonly densityUB: number  // E_undirected / max(1, N-1)
    readonly nashWilliamsLB: number  // max over k-cores of ⌈E_S / (|S|-1)⌉
    readonly greedyUB: number  // forests produced by greedy decomposition
    readonly degeneracy: number  // = coreness max
    readonly forestAssignment: ReadonlyMap<string, number>  // edgeKey -> forest index (0..greedyUB-1)
}

class UnionFind {
    private readonly parent: Map<string, string> = new Map()
    private readonly rank: Map<string, number> = new Map()
    find(x: string): string {
        if (!this.parent.has(x)) { this.parent.set(x, x); this.rank.set(x, 0); return x }
        let root: string = x
        while (this.parent.get(root)! !== root) root = this.parent.get(root)!
        let cur: string = x
        while (this.parent.get(cur)! !== cur) {
            const next: string = this.parent.get(cur)!
            this.parent.set(cur, root)
            cur = next
        }
        return root
    }
    union(a: string, b: string): boolean {
        const ra: string = this.find(a)
        const rb: string = this.find(b)
        if (ra === rb) return false
        const rankA: number = this.rank.get(ra)!
        const rankB: number = this.rank.get(rb)!
        if (rankA < rankB) this.parent.set(ra, rb)
        else if (rankA > rankB) this.parent.set(rb, ra)
        else { this.parent.set(rb, ra); this.rank.set(ra, rankA + 1) }
        return true
    }
}

function undirectedKey(a: string, b: string): string {
    return a < b ? `${a}\u0000${b}` : `${b}\u0000${a}`
}

function degeneracyOf(adj: ReadonlyMap<string, Set<string>>): number {
    // Matula & Beck's degeneracy-ordering algorithm. Iteratively removes min-degree vertex.
    const degree: Map<string, number> = new Map()
    for (const [v, nbrs] of adj) degree.set(v, nbrs.size)
    const removed: Set<string> = new Set()
    let maxDeg: number = 0
    while (removed.size < adj.size) {
        let pickV: string | null = null
        let pickDeg: number = Infinity
        for (const [v, d] of degree) {
            if (removed.has(v)) continue
            if (d < pickDeg) { pickDeg = d; pickV = v }
        }
        if (pickV === null) break
        maxDeg = Math.max(maxDeg, pickDeg)
        removed.add(pickV)
        for (const nbr of adj.get(pickV)!) {
            if (removed.has(nbr)) continue
            degree.set(nbr, degree.get(nbr)! - 1)
        }
    }
    return maxDeg
}

function nashWilliamsFromKCore(adj: ReadonlyMap<string, Set<string>>, k: number): number {
    // Repeatedly strip vertices of degree < k. Whatever remains has min-degree ≥ k;
    // its density is a lower bound on arboricity.
    const deg: Map<string, number> = new Map()
    for (const [v, n] of adj) deg.set(v, n.size)
    const alive: Set<string> = new Set(adj.keys())
    let changed: boolean = true
    while (changed) {
        changed = false
        for (const v of Array.from(alive)) {
            if (deg.get(v)! < k) {
                alive.delete(v)
                changed = true
                for (const nbr of adj.get(v)!) {
                    if (alive.has(nbr)) deg.set(nbr, deg.get(nbr)! - 1)
                }
            }
        }
    }
    if (alive.size < 2) return 0
    let edgeCount: number = 0
    for (const v of alive) for (const nbr of adj.get(v)!) if (alive.has(nbr) && v < nbr) edgeCount++
    return Math.ceil(edgeCount / (alive.size - 1))
}

export function computeArboricity(g: Graph): ArboricityReport {
    const N: number = g.nodes.length

    // Undirected adjacency for Nash-Williams and degeneracy.
    const undirected: Map<string, Set<string>> = new Map()
    for (const n of g.nodes) undirected.set(n.id, new Set())
    const undirectedEdgeSet: Set<string> = new Set()
    for (const e of g.edges) {
        if (e.src === e.tgt) continue
        undirected.get(e.src)!.add(e.tgt)
        undirected.get(e.tgt)!.add(e.src)
        undirectedEdgeSet.add(undirectedKey(e.src, e.tgt))
    }

    const degen: number = degeneracyOf(undirected)
    let nashLB: number = 0
    for (let k = 1; k <= Math.max(1, degen); k++) {
        nashLB = Math.max(nashLB, nashWilliamsFromKCore(undirected, k))
    }

    // Greedy forest decomposition on undirected edge classes. Each class carries
    // all its directed copies (so bidirectional pairs travel together).
    const classes: Map<string, {u: string; v: string; edges: readonly {src: string; tgt: string}[]}> = new Map()
    for (const e of g.edges) {
        if (e.src === e.tgt) continue
        const key: string = undirectedKey(e.src, e.tgt)
        const entry = classes.get(key) ?? {u: e.src < e.tgt ? e.src : e.tgt, v: e.src < e.tgt ? e.tgt : e.src, edges: []}
        classes.set(key, {u: entry.u, v: entry.v, edges: [...entry.edges, {src: e.src, tgt: e.tgt}]})
    }

    const forests: UnionFind[] = []
    const assignment: Map<string, number> = new Map()
    for (const [key, cls] of classes) {
        let placed: boolean = false
        for (let i = 0; i < forests.length; i++) {
            if (forests[i]!.union(cls.u, cls.v)) {
                assignment.set(key, i)
                placed = true
                break
            }
        }
        if (!placed) {
            const uf: UnionFind = new UnionFind()
            uf.union(cls.u, cls.v)
            forests.push(uf)
            assignment.set(key, forests.length - 1)
        }
    }

    return {
        nodeCount: N,
        edgeCount: g.edges.length,
        undirectedEdgeCount: undirectedEdgeSet.size,
        densityUB: Math.ceil(undirectedEdgeSet.size / Math.max(1, N - 1)),
        nashWilliamsLB: nashLB,
        greedyUB: forests.length,
        degeneracy: degen,
        forestAssignment: assignment,
    }
}

// Convenience: return just the forest assignment map keyed by undirectedKey.
export function undirectedEdgeKey(a: string, b: string): string {
    return undirectedKey(a, b)
}

if (import.meta.url === `file://${process.argv[1]}`) {
    const path: string | undefined = process.argv[2]
    if (!path) { console.error('usage: arboricity.ts <fixture.json>'); process.exit(1) }
    const {loadGraph} = await import('./graph.js')
    const g: Graph = loadGraph(path)
    const r: ArboricityReport = computeArboricity(g)
    console.log(JSON.stringify({
        nodes: r.nodeCount,
        edges: r.edgeCount,
        undirectedEdges: r.undirectedEdgeCount,
        density_ub: r.densityUB,
        nash_williams_lb: r.nashWilliamsLB,
        greedy_ub: r.greedyUB,
        degeneracy: r.degeneracy,
    }, null, 2))
}
