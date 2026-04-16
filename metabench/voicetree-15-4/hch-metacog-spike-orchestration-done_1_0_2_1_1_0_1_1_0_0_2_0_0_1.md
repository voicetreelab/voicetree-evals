---
isContextNode: false
---
# so let's think about how we could combine all these ideas to make it easlily actually work with kaggle bencmark

so generally, for a given problem, you want to give a compute budget.

there's also a time budget that's economically relevant.

you also want to encourage decomp becaue that prevents context rot. (agents have a single sesion max context length)

so you have a subtask max tokens, whole problem max tokens. 
and same for max subtask + total time.

so what are some simple benchmarks we could make for this? 
[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_2_0_0_1_0.md]]