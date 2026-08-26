import os

APP_ENV = os.getenv("APP_ENV", "local")
EVALUATOR_USERNAME = os.getenv("EVALUATOR_USERNAME", "").strip()
EVALUATOR_PASSWORD = os.getenv("EVALUATOR_PASSWORD", "").strip()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "480"))
DEFAULT_APPROACH = os.getenv("DEFAULT_APPROACH", "approach_a")
CPU_COST_PER_SECOND = float(os.getenv("CPU_CONTAINER_APP_COST_PER_SEC", "0.000036"))
MEMORY_GIB_COST_PER_SECOND = float(os.getenv("MEMORY_GIB_COST_PER_SEC", "0"))
CONTAINER_MEMORY_GIB = float(os.getenv("CONTAINER_MEMORY_GIB", "2"))
MAX_CONCURRENT_INFERENCE = max(1, int(os.getenv("MAX_CONCURRENT_INFERENCE", "1")))
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "/tmp/callscope/callscope.db")

def validate_auth_config() -> None:
    if APP_ENV.lower() == "test":
        return
    missing = [name for name, value in (("EVALUATOR_USERNAME", EVALUATOR_USERNAME), ("EVALUATOR_PASSWORD", EVALUATOR_PASSWORD), ("JWT_SECRET_KEY", JWT_SECRET_KEY)) if not value]
    if missing:
        raise RuntimeError(f"Missing required authentication configuration: {', '.join(missing)}")
