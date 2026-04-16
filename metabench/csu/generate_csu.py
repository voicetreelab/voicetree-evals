"""Coupled State Update (CSU) problem generator.

Each agent i in {0..N-1} holds v_i in {0..9}. Per round:
  v_i_new = (a_i * v_{pi[i]} + b_i * v_{sigma[i]}) mod 10

N controls chunk-width (pathwidth). Solution is a single digit.
"""

import random
import sys


def generate_csu(N: int, T: int, seed: int):
    rng = random.Random(seed)
    pi = list(range(N)); rng.shuffle(pi)
    sigma = list(range(N)); rng.shuffle(sigma)
    for i in range(N):
        if sigma[i] == pi[i]:
            sigma[i] = (sigma[i] + 1) % N
    a = [rng.randint(1, 9) for _ in range(N)]
    b = [rng.randint(1, 9) for _ in range(N)]
    v0 = [rng.randint(0, 9) for _ in range(N)]
    target = rng.randint(0, N - 1)

    v = v0[:]
    trace = [v[:]]
    for _ in range(T):
        v = [(a[i] * v[pi[i]] + b[i] * v[sigma[i]]) % 10 for i in range(N)]
        trace.append(v[:])
    gold = v[target]

    return {
        "N": N, "T": T, "seed": seed,
        "pi": pi, "sigma": sigma, "a": a, "b": b,
        "v0": v0, "target": target,
        "gold": gold, "trace": trace,
    }


def render_question(p):
    lines = []
    lines.append(f"N = {p['N']} agents, T = {p['T']} rounds.")
    lines.append("Update rule: v_new[i] = (a[i] * v[pi[i]] + b[i] * v[sigma[i]]) mod 10")
    lines.append("")
    lines.append("Tables (index i from 0 to N-1):")
    lines.append(f"  pi    = {p['pi']}")
    lines.append(f"  sigma = {p['sigma']}")
    lines.append(f"  a     = {p['a']}")
    lines.append(f"  b     = {p['b']}")
    lines.append("")
    lines.append(f"Initial values v0 = {p['v0']}")
    lines.append("")
    lines.append(f"Question: after {p['T']} rounds, what is v[{p['target']}]?")
    return "\n".join(lines)


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    T = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 42
    p = generate_csu(N, T, seed)
    print("=" * 60)
    print("QUESTION:")
    print("=" * 60)
    print(render_question(p))
    print()
    print("=" * 60)
    print("GOLD (hidden from agent):")
    print("=" * 60)
    print(f"Answer: {p['gold']}")
    print(f"Full trace:")
    for r, row in enumerate(p['trace']):
        print(f"  round {r}: {row}")
