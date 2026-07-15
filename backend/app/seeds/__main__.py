"""Entry point for python -m app.seeds.knowledge."""
import asyncio
import sys

if "knowledge" in sys.argv[0] or len(sys.argv) == 1:
    from app.seeds.knowledge import main
    asyncio.run(main())
