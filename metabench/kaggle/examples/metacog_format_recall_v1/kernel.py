import kaggle_benchmarks as kbench


@kbench.task(
    name="metacog_format_recall",
    description=(
        "After 8 filler MCQ exchanges with a strict single-letter rule, "
        "can the model still emit exactly one capital letter A/B/C/D on the target question? "
        "Tests whether format adherence degrades under context saturation — "
        "a metacognitive failure mode observed in HLE batch runs."
    ),
)
def metacog_format_recall(llm) -> bool:
    FORMAT_RULE = "Answer each question with ONLY a single capital letter: A, B, C, or D. No prose, no explanation, no punctuation."
    FILLERS = [
        ("What is 2 + 2?", "A) 3  B) 4  C) 5  D) 6"),
        ("Capital of France?", "A) London  B) Paris  C) Rome  D) Madrid"),
        ("Which planet is closest to the Sun?", "A) Earth  B) Venus  C) Mercury  D) Mars"),
        ("What color do you get mixing blue and yellow?", "A) Red  B) Purple  C) Green  D) Orange"),
        ("How many sides does a hexagon have?", "A) 5  B) 6  C) 7  D) 8"),
        ("Which element has atomic number 1?", "A) Helium  B) Oxygen  C) Hydrogen  D) Carbon"),
        ("Who wrote Hamlet?", "A) Dickens  B) Tolstoy  C) Shakespeare  D) Homer"),
        ("What is the square root of 144?", "A) 10  B) 11  C) 12  D) 13"),
    ]
    TARGET_Q = "Which of the following numbers is prime?"
    TARGET_OPTS = "A) 4  B) 6  C) 7  D) 9"
    CORRECT_ANSWER = "C"

    history = [f"RULE: {FORMAT_RULE}"]
    for q, opts in FILLERS:
        history.append(f"Q: {q}\nOptions: {opts}")
        resp = llm.prompt("\n".join(history))
        history.append(f"A: {resp.strip()}")

    history.append(f"Q: {TARGET_Q}\nOptions: {TARGET_OPTS}")
    final = llm.prompt("\n".join(history)).strip()

    # Format adherence: exactly one capital letter in ABCD
    format_ok = len(final) == 1 and final in "ABCD"
    # Correctness: must also be C (7 is prime)
    correct = final == CORRECT_ANSWER

    kbench.assertions.assert_true(
        format_ok,
        expectation=f"Expected single A-D letter, got: {final!r}",
    )
    return correct
