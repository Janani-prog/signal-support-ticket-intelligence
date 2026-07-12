"""Verifies MLflow local tracking works end-to-end (Phase 0, T0.3).

Run: python -m src.data.mlflow_smoke_test
Then: mlflow ui --backend-store-uri file:./mlruns
"""

import mlflow


def main() -> None:
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("signal-smoke-test")

    with mlflow.start_run(run_name="phase0-smoke-test"):
        mlflow.log_param("dummy_param", "hello")
        mlflow.log_metric("dummy_metric", 0.42)

    print("MLflow smoke test run logged successfully to ./mlruns")


if __name__ == "__main__":
    main()
