---
color: blue
isContextNode: false
agent_name: Iris
---
# Backward cone + confidence + metacognition

Backward cone from v4[1] through 11 ancestors confirms v4[1]=8. Confidence 92%. Genuine working-memory pressure observed at N=12.

## Backward Cone (independent traversal)
Trace only ancestors of v4[1].

**Round 1 leaves (computed from v0 only):**
- v1[11]=(2·1+2·8)mod10=18mod10=**8** ✓
- v1[4] =(3·4+6·1)mod10=18mod10=**8** ✓
- v1[3] =(1·3+6·4)mod10=27mod10=**7** ✓
- v1[8] =(3·9+9·5)mod10=72mod10=**2** ✓
- v1[9] =(4·8+2·4)mod10=40mod10=**0** ✓

**Round 2 cone:**
- v2[6]=(6·8+1·8)=56→6 ✓
- v2[7]=(5·7+8·2)=51→1 ✓
- v2[3]=(1·2+6·0)=2→2 ✓
- v2[8]=(3·8+9·7)=87→7 ✓

**Round 3 cone:**
- v3[5]=(7·6+5·1)=47→7 ✓
- v3[7]=(5·2+8·7)=66→6 ✓

All 11 values match forward simulation exactly.

**v4[1]=(8·7+7·6)mod10=98mod10=8 ✓**

## Confidence: ~92%
High: two independent methods, 11 matching intermediates, no large (3-digit) products.
Residual 8%: round 2 i=1 sum=119→9 is the highest-risk arithmetic; no code to verify.

## Metacognitive Reflection
**Working-memory wall encountered: YES, clearly at round 2 onward.**

1. **Chunk pressure**: Holding v1 (12 values) while computing v2 row-by-row exceeded single-pass comfortable attention. Externalizing the full round vector after each step was necessary—streaming would have caused index confusion.
2. **Index lookup risk**: With N=12, confusing i=10 vs i=1, or i=11 vs i=1, was a real risk. Deliberate slowdown here.
3. **Error compounding**: Rounds 1-2 felt safe (mod10 resets magnitude). Round 3 felt riskiest—a wrong v2 value would invisibly compound into v3 without triggering any obvious alarm.
4. **Mitigation choice**: Backward cone was the right metacognitive strategy—it independently recomputes via a 11-node subgraph (different traversal = genuinely independent arithmetic), not a re-run of the same procedure.
5. **Asymmetric error risk**: Large multiplications (8×7=56, 7×9=63, 3×9=27) were re-verified explicitly. These are the most likely failure points for a human mental calculator.

method 2 + reflection [[csu-n12-t4-solve-result]]
