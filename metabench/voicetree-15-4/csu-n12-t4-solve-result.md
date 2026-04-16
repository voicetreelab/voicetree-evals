---
color: green
isContextNode: false
agent_name: Iris
---
# CSU N=12 T=4 solve: v[1] = 8 (two methods agree)

Solved CSU working-memory benchmark (N=12, T=4, no code). Both full forward simulation and backward cone agree: v[1] after 4 rounds = 8. Confidence ~92%.

## Setup
v_new[i] = (a[i]·v[π[i]] + b[i]·v[σ[i]]) mod 10
π=[7,5,2,8,9,6,11,3,4,0,1,10] σ=[5,7,3,9,10,7,4,8,3,1,11,0]
a=[4,8,5,1,3,7,6,5,3,4,6,2]  b=[2,7,2,6,6,5,1,8,9,2,7,2]
v0=[8,4,9,5,9,3,1,0,3,4,1,3]

## Final Answer
**v[1] after 4 rounds = 8**

Derived by two independent methods (see child nodes): full 48-operation forward simulation and 11-node backward cone expansion. All 11 intermediate values in the cone matched the forward simulation exactly.

### NOTES

- Two-method cross-check was essential: N=12 forward simulation requires externalizing full 12-vector after each round; a single-pass mental trace is unreliable at this N

[[task_1776313468042bcr]]
