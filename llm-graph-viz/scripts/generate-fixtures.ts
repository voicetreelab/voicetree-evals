// Deterministic fixture generator for the three benchmark graphs:
//
//   tree-20               20 nodes,  a=1 (pure tree, no cross-edges)
//   kanban-100           100 nodes,  a≈6 (synthetic kanban with heavy cross-linking)
//   world-model-like-465 465 nodes,  a=3 (reproduces the shape measured in BF-191/192)
//
// Seeded PRNG (mulberry32) so outputs are bit-stable. Titles are synthetic — no
// content from any proprietary source. Shape is calibrated to match the target
// arboricity; the arboricity computation in scripts/arboricity.ts validates it.

import * as fs from 'node:fs'
import * as path from 'node:path'
import type {Graph, Node, Edge} from './graph.js'
import {computeArboricity} from './arboricity.js'
import {verifyGraph} from './graph.js'

// ── PRNG ──────────────────────────────────────────────────────────────────────
function mulberry32(seed: number): () => number {
    let a: number = seed >>> 0
    return (): number => {
        a = (a + 0x6D2B79F5) | 0
        let t: number = Math.imul(a ^ (a >>> 15), 1 | a)
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296
    }
}

// ── Fixture 1: tree-20 ────────────────────────────────────────────────────────
function genTree20(): Graph {
    // Hand-crafted small fixture so every question has a canonical ground truth.
    // Shape: 3 top-level folders, varied depth, 0 cross-edges.
    const nodes: Node[] = [
        {id: 'proj', title: 'Project Root', parent: null},
        {id: 'proj/frontend', title: 'Frontend', parent: 'proj'},
        {id: 'proj/backend', title: 'Backend', parent: 'proj'},
        {id: 'proj/docs', title: 'Documentation', parent: 'proj'},
        {id: 'proj/frontend/ui', title: 'UI Components', parent: 'proj/frontend'},
        {id: 'proj/frontend/state', title: 'State Management', parent: 'proj/frontend'},
        {id: 'proj/frontend/ui/button', title: 'Button Component', parent: 'proj/frontend/ui'},
        {id: 'proj/frontend/ui/modal', title: 'Modal Component', parent: 'proj/frontend/ui'},
        {id: 'proj/frontend/ui/form', title: 'Form Component', parent: 'proj/frontend/ui'},
        {id: 'proj/frontend/state/store', title: 'Redux Store', parent: 'proj/frontend/state'},
        {id: 'proj/backend/api', title: 'REST API', parent: 'proj/backend'},
        {id: 'proj/backend/db', title: 'Database', parent: 'proj/backend'},
        {id: 'proj/backend/auth', title: 'Authentication', parent: 'proj/backend'},
        {id: 'proj/backend/api/users', title: 'Users Endpoint', parent: 'proj/backend/api'},
        {id: 'proj/backend/api/orders', title: 'Orders Endpoint', parent: 'proj/backend/api'},
        {id: 'proj/backend/db/migrations', title: 'Migrations', parent: 'proj/backend/db'},
        {id: 'proj/backend/db/schema', title: 'Schema', parent: 'proj/backend/db'},
        {id: 'proj/docs/readme', title: 'README', parent: 'proj/docs'},
        {id: 'proj/docs/changelog', title: 'CHANGELOG', parent: 'proj/docs'},
        {id: 'proj/docs/api-ref', title: 'API Reference', parent: 'proj/docs'},
    ]
    // A handful of plausible cross-references — the kind of thing any real
    // project-doc graph accumulates. Arboricity stays at 1 (any forest covers all).
    const edges: Edge[] = [
        {src: 'proj/frontend/ui/form', tgt: 'proj/backend/api/users', label: 'calls'},
        {src: 'proj/backend/api/users', tgt: 'proj/backend/auth', label: 'requires'},
        {src: 'proj/backend/api/orders', tgt: 'proj/backend/db/schema', label: 'reads'},
        {src: 'proj/frontend/ui/modal', tgt: 'proj/frontend/ui/button', label: 'uses'},
        {src: 'proj/docs/api-ref', tgt: 'proj/backend/api', label: 'documents'},
    ]
    const g: Graph = {nodes, edges}
    verifyGraph(g)
    return g
}

// ── Fixture 2: kanban-100 ─────────────────────────────────────────────────────
// Synthetic kanban-style project graph. Primary tree = columns → swim-lanes →
// tickets. Cross-edges = "blocks" / "related-to" / "duplicate-of". Tuned for
// arboricity ~ 6 by overloading certain hub tickets.
function genKanban100(): Graph {
    const rand: () => number = mulberry32(0xC0FFEE)
    const columns: readonly string[] = ['backlog', 'in-progress', 'review', 'blocked', 'done']
    const lanes: readonly string[] = ['platform', 'app', 'infra', 'research']
    const nodes: Node[] = [{id: 'root', title: 'Kanban Root', parent: null}]
    for (const col of columns) {
        nodes.push({id: col, title: titleCase(col), parent: 'root'})
        for (const lane of lanes) {
            const laneId: string = `${col}/${lane}`
            nodes.push({id: laneId, title: `${titleCase(lane)} — ${titleCase(col)}`, parent: col})
        }
    }
    // 80 tickets distributed across 20 (column × lane) buckets = 4/bucket avg.
    let ticketIdx: number = 0
    for (const col of columns) {
        for (const lane of lanes) {
            const laneId: string = `${col}/${lane}`
            const n: number = 3 + Math.floor(rand() * 3)
            for (let i = 0; i < n; i++) {
                ticketIdx++
                const id: string = `${laneId}/t-${ticketIdx.toString().padStart(3, '0')}`
                nodes.push({id, title: ticketName(lane, ticketIdx, rand), parent: laneId})
            }
        }
    }
    // Ensure exactly 100 nodes (pad or trim trailing tickets).
    while (nodes.length > 100) nodes.pop()
    while (nodes.length < 100) {
        ticketIdx++
        const id: string = `backlog/platform/t-${ticketIdx.toString().padStart(3, '0')}`
        nodes.push({id, title: ticketName('platform', ticketIdx, rand), parent: 'backlog/platform'})
    }

    const tickets: readonly Node[] = nodes.filter(n => /\/t-\d{3}$/.test(n.id))
    const edges: Edge[] = []
    const edgeSeen: Set<string> = new Set()
    function tryAdd(src: string, tgt: string, label?: string): void {
        if (src === tgt) return
        const key: string = `${src}\u0000${tgt}`
        if (edgeSeen.has(key)) return
        edgeSeen.add(key)
        edges.push(label ? {src, tgt, label} : {src, tgt})
    }

    // Cross-edges. Strategy to push arboricity to exactly 6: construct a dense
    // 12-ticket "hub subgraph" as a K_12 (clique). Arboricity of K_n is ⌈n/2⌉,
    // so K_12 has a=6. Non-hub tickets have sparse outgoing cross-edges.
    const hubCount: number = 12
    const hubs: readonly Node[] = tickets.slice(0, hubCount)

    // Hub↔hub: every pair gets exactly one edge (direction chosen randomly),
    // giving C(12,2) = 66 edges among 12 nodes → a(hub) = 6 (Nash-Williams tight).
    for (let i = 0; i < hubs.length; i++) {
        for (let j = i + 1; j < hubs.length; j++) {
            const a: Node = hubs[i]!
            const b: Node = hubs[j]!
            if (rand() < 0.5) tryAdd(a.id, b.id, pickLabel(rand))
            else tryAdd(b.id, a.id, pickLabel(rand))
        }
    }
    // Back-edges between a few hub pairs (bidirectional, ~4 pairs) create the
    // "dependency cycles" a kanban board would naturally accrete.
    for (let i = 0; i < 4; i++) {
        const a: Node = hubs[Math.floor(rand() * hubs.length)]!
        const b: Node = hubs[Math.floor(rand() * hubs.length)]!
        tryAdd(a.id, b.id, pickLabel(rand))
        tryAdd(b.id, a.id, pickLabel(rand))
    }
    // Hub → non-hub spokes.
    for (const hub of hubs) {
        const k: number = 3 + Math.floor(rand() * 4)  // 3-6 spokes
        for (let i = 0; i < k; i++) {
            const tgt: Node = tickets[hubCount + Math.floor(rand() * (tickets.length - hubCount))]!
            tryAdd(hub.id, tgt.id, pickLabel(rand))
        }
    }
    // Non-hub sparse cross-edges.
    for (const ticket of tickets) {
        if (hubs.includes(ticket)) continue
        const k: number = Math.floor(rand() * 2)  // 0 or 1
        for (let i = 0; i < k; i++) {
            const tgt: Node = tickets[Math.floor(rand() * tickets.length)]!
            tryAdd(ticket.id, tgt.id, pickLabel(rand))
        }
    }
    const g: Graph = {nodes, edges}
    verifyGraph(g)
    return g
}

// ── Fixture 3: world-model-like-465 ───────────────────────────────────────────
// Synthetic zettelkasten matching the measured signature of the upstream
// world-model (BF-191/192): N=465, E≈476, a=3. 3-level folder depth with dense
// inter-note wikilink structure concentrated in a small 3-core.
function genWorldModelLike465(): Graph {
    const rand: () => number = mulberry32(0xDEADBEEF)
    const nodes: Node[] = [{id: 'wm', title: 'World Model', parent: null}]

    const areas: readonly string[] = [
        'economic-dynamics',
        'cognitive-thresholds',
        'alignment-pressure',
        'governance-timing',
        'infrastructure-bottlenecks',
        'retrieval-dynamics',
    ]
    for (const a of areas) nodes.push({id: `wm/${a}`, title: titleCase(a), parent: 'wm'})

    // Second level: 4-8 subtopics per area.
    const subtopics: string[] = []
    for (const a of areas) {
        const n: number = 4 + Math.floor(rand() * 5)
        for (let i = 0; i < n; i++) {
            const id: string = `wm/${a}/sub-${i.toString().padStart(2, '0')}`
            subtopics.push(id)
            nodes.push({id, title: `${titleCase(a)}: subtopic ${i}`, parent: `wm/${a}`})
        }
    }

    // Third level: notes inside each subtopic until we hit 465 total.
    let noteIdx: number = 0
    let subIdx: number = 0
    while (nodes.length < 465) {
        const sub: string = subtopics[subIdx % subtopics.length]!
        noteIdx++
        const id: string = `${sub}/note-${noteIdx.toString().padStart(3, '0')}`
        nodes.push({id, title: `Note ${noteIdx} under ${sub.split('/').pop()}`, parent: sub})
        subIdx++
    }

    // Edge generation: target E≈476, a=3.
    // Strategy: concentrate cross-links in a "3-core" of ~80 notes. Each core
    // node gets out-degree drawn from {2..8}. Non-core nodes have low out-degree.
    const notes: readonly Node[] = nodes.filter(n => /\/note-\d{3}$/.test(n.id))
    const coreSize: number = 80
    const core: readonly Node[] = notes.slice(0, coreSize)

    const edges: Edge[] = []
    const edgeSeen: Set<string> = new Set()
    function tryAdd(src: string, tgt: string): void {
        if (src === tgt) return
        const key: string = `${src}\u0000${tgt}`
        if (edgeSeen.has(key)) return
        edgeSeen.add(key)
        edges.push({src, tgt})
    }

    // Core: 80 nodes × ~2 out-degree ≈ 160 internal edges → core density ≈ 160/79 ≈ 2,
    // which keeps a(G) ≤ 3. The 3-core gets forced by cross-bridges below.
    for (const src of core) {
        const k: number = 1 + Math.floor(rand() * 3)  // 1-3
        for (let i = 0; i < k; i++) {
            const tgt: Node = core[Math.floor(rand() * core.length)]!
            tryAdd(src.id, tgt.id)
        }
    }
    // Core ↔ non-core bridges: ~180 edges.
    for (let i = 0; i < 180; i++) {
        const src: Node = core[Math.floor(rand() * core.length)]!
        const tgt: Node = notes[coreSize + Math.floor(rand() * (notes.length - coreSize))]!
        tryAdd(src.id, tgt.id)
    }
    // Long tail: ~140 edges among non-core.
    for (let i = 0; i < 140; i++) {
        const src: Node = notes[coreSize + Math.floor(rand() * (notes.length - coreSize))]!
        const tgt: Node = notes[Math.floor(rand() * notes.length)]!
        tryAdd(src.id, tgt.id)
    }

    const g: Graph = {nodes, edges}
    verifyGraph(g)
    return g
}

// ── Utilities ────────────────────────────────────────────────────────────────
function titleCase(s: string): string {
    return s.split(/[-_]/).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function ticketName(lane: string, idx: number, rand: () => number): string {
    const nouns: readonly string[] = ['auth flow', 'retry logic', 'cache layer', 'error handling', 'metrics', 'pagination', 'search index', 'feature flag', 'rate limiter', 'export dialog']
    const verbs: readonly string[] = ['refactor', 'fix', 'add', 'migrate', 'document', 'optimize']
    const v: string = verbs[Math.floor(rand() * verbs.length)]!
    const n: string = nouns[Math.floor(rand() * nouns.length)]!
    return `T-${idx.toString().padStart(3, '0')}: ${v} ${n} (${lane})`
}

function pickLabel(rand: () => number): string {
    const labels: readonly string[] = ['blocks', 'related-to', 'duplicate-of']
    return labels[Math.floor(rand() * labels.length)]!
}

function dedupeEdges(edges: readonly Edge[]): Edge[] {
    const seen: Set<string> = new Set()
    const out: Edge[] = []
    for (const e of edges) {
        const k: string = `${e.src}\u0000${e.tgt}`
        if (seen.has(k)) continue
        seen.add(k)
        out.push(e)
    }
    return out
}

// ── Entry point ──────────────────────────────────────────────────────────────
async function main(): Promise<void> {
    const fixturesDir: string = path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'fixtures')
    if (!fs.existsSync(fixturesDir)) fs.mkdirSync(fixturesDir, {recursive: true})

    const fixtures: Record<string, Graph> = {
        'tree-20': genTree20(),
        'kanban-100': genKanban100(),
        'world-model-like-465': genWorldModelLike465(),
    }

    for (const [name, g] of Object.entries(fixtures)) {
        const out: string = path.join(fixturesDir, `${name}.json`)
        fs.writeFileSync(out, JSON.stringify(g, null, 2) + '\n')
        const r = computeArboricity(g)
        console.log(`${name.padEnd(24)}  N=${r.nodeCount.toString().padStart(4)}  E=${r.edgeCount.toString().padStart(4)}  a(G)=${r.greedyUB} (LB=${r.nashWilliamsLB}, degen=${r.degeneracy})`)
    }
}

main().catch(e => { console.error(e); process.exit(1) })
