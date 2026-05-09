import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Testing imports...")
    import main
    print("main: OK")
    import app.strategy.strategy_runner
    print("app.strategy.strategy_runner: OK")
    import app.routes.strategy_routes
    print("app.routes.strategy_routes: OK")
    import db.models
    print("db.models: OK")
    import app.strategy.data_engine
    print("app.strategy.data_engine: OK")
    import app.strategy.indicators
    print("app.strategy.indicators: OK")
    import app.strategy.signal_engine
    print("app.strategy.signal_engine: OK")
    import app.strategy.entry_engine
    print("app.strategy.entry_engine: OK")
    import app.strategy.exit_engine
    print("app.strategy.exit_engine: OK")
    print("All critical imports: OK")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
