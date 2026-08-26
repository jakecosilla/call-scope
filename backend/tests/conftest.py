import os
os.environ.setdefault("APP_ENV","test")
os.environ.setdefault("EVALUATOR_USERNAME","evaluator@example.test")
os.environ.setdefault("EVALUATOR_PASSWORD","test-only-password")
os.environ.setdefault("JWT_SECRET_KEY","test-only-secret-that-is-long-enough-for-hs256")
os.environ.setdefault("SQLITE_DB_PATH","/tmp/callscope-tests/callscope.db")
