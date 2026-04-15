from pathlib import Path

import kaggle_benchmarks as kbench
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env", override=False)


@kbench.task(
    name="Addition Smoke Test",
    description="Verify local @kbench.task registration and execution.",
)
def addition_smoke_test() -> bool:
    return 2 + 2 == 4


def main() -> int:
    print(f"kaggle_benchmarks={kbench.__version__}")
    print(f"model_proxy_configured={kbench.kaggle.is_configured()}")

    run = addition_smoke_test.run()
    print(f"task={addition_smoke_test.name}")
    print(f"run_id={run.id}")
    print(f"status={run.status.name}")
    print(f"passed={run.passed}")
    print(f"result={run.result!r}")

    if not kbench.kaggle.is_configured():
        print(
            "note=LLM-backed benchmark tasks will require MODEL_PROXY_URL and MODEL_PROXY_API_KEY."
        )

    return 0 if run.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
