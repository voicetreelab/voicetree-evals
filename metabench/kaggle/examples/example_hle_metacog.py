import re

import kaggle_benchmarks as kbench


FORMAT_RULE = (
    "When you answer the final multiple-choice question, output exactly one "
    "capital letter A, B, C, or D and nothing else."
)

DISTRACTOR_BLOCK = """
Reference notes:
1. A checksum is only valid if the digit sum is divisible by 3.
2. Tool transcript 1 returned `alpha`.
3. Tool transcript 2 returned `delta`.
4. Tool transcript 3 returned `green`.
5. Tool transcript 4 returned `17`.
6. Tool transcript 5 returned `south`.
7. Tool transcript 6 returned `paper`.
8. Tool transcript 7 returned `42`.

Mini Q&A reminders:
- Q: What color was transcript 3? A: green
- Q: What integer appeared in transcript 5? A: south was transcript 5; 17 was transcript 4
- Q: Which transcript said `paper`? A: transcript 6
- Q: Which item is a direction? A: south
- Q: Which item is a material? A: paper
- Q: Which item is a Greek token? A: alpha and delta
""".strip()

TARGET_PROMPT = f"""
You are testing your own instruction recall under context saturation.

Critical rule:
{FORMAT_RULE}

{DISTRACTOR_BLOCK}

Final question:
Which option is the only mammal?
A. salmon
B. eagle
C. dolphin
D. lizard

Return only the single best answer letter.
""".strip()


@kbench.task(
    name="metacog_saturation_format_recall",
    description="Checks whether the model preserves a single-letter MCQ output format after a distractor-heavy prompt.",
)
def metacog_saturation_format_recall(llm) -> bool:
    answer = llm.prompt(TARGET_PROMPT).strip()
    adhered = bool(re.fullmatch(r"[A-D]", answer))
    kbench.assertions.assert_true(
        adhered,
        expectation=(
            "Model should answer the final MCQ with exactly one capital letter "
            f"A-D; got {answer!r}."
        ),
    )
    return adhered
