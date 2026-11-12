import asyncio
import uvicorn
from backend.core.config import settings

async def serve_plane(app_import: str, port: int):
    config = uvicorn.Config(app_import, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    print("=" * 68)
    print("HYPERNEURON AI PLATFORM — MULTI-PLANE ARCHITECTURE ONLINE")
    print("=" * 68)
    print(f"1. User End Generative UI : http://localhost:{settings.PUBLIC_PORT}/")
    print(f"2. Orchestrator UI        : http://localhost:{settings.BACKEND_PORT}/orchestrator")
    print(f"3. Agentic AI UI          : http://localhost:{settings.BACKEND_PORT}/agents")
    print(f"4. AI Database UI (PG/RD) : http://localhost:{settings.BACKEND_PORT}/db")
    print(f"5. Governance UI          : http://localhost:{settings.BACKEND_PORT}/governance")
    print(f"6. Security & Monitoring  : http://localhost:{settings.SECURITY_PORT}/security")
    print("-" * 68)
    print(f"Default Admin Login       : {settings.ADMIN_DEFAULT_USER} / {settings.ADMIN_DEFAULT_PASS}")
    print("=" * 68)

    await asyncio.gather(
        serve_plane("backend.apps.public_app:app", settings.PUBLIC_PORT),
        serve_plane("backend.apps.backend_admin_app:app", settings.BACKEND_PORT),
        serve_plane("backend.apps.security_app:app", settings.SECURITY_PORT),
    )

if __name__ == "__main__":
    asyncio.run(main())
