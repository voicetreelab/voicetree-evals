---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Chunking Recommendation

Recommended a queue of small question-level chunks rather than splitting the work into two fixed halves. The baseline stays single-source-of-truth; each person works only on isolated chunk updates.

Recommendation:
- Do not split the full baseline submission file in half.
- Do not split by individual forecast rows.
- Split by grouped target questions, because one question shares evidence across its first-month rows.

Best working model for two people:
1. One person runs Step 4 once to create the baseline, grouped target manifest, and updates template structure.
2. Break the grouped target manifest into small question-level chunks.
3. Each person claims the next available chunk, produces an updates file for that chunk, and moves on to the next one.
4. Merge all chunk updates back onto the one baseline submission at the end.

Suggested chunk size:
- Start with 10 grouped questions per chunk.
- That is small enough to rebalance if one chunk is harder, but large enough that the setup overhead stays low.

Why not fixed halves:
- Difficulty will not be perfectly even.
- One person may finish faster.
- Small chunks let you rebalance and checkpoint more safely.

Why not split by rows:
- The full workflow is question-level.
- Splitting rows from the same question across people duplicates reasoning and creates inconsistency.

Rule of thumb:
- baseline file stays centralized
- work is distributed as small grouped-question chunks
- outputs are isolated chunk updates files
- final merge happens once at the end

[[1775712512821qMj]]
