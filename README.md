# Hyperneuron AI Platform

Hyperneuron is a private multi-agent research platform built with FastAPI and LangGraph. The end-user workspace is intentionally minimal: sign in, submit a prompt, and read the generated response. Operational capabilities are exposed through separate protected workspaces.

## Platform topology

| Workspace | URL (local) | Purpose |
| --- | --- | --- |
| Generative AI | http://localhost:3000 | User prompt and generated result |
| Orchestrator | http://localhost:3001 | Planning, routing, synthesis and run history |
| Agentic AI | http://localhost:3002 | Specialist agents and model assignments |
| Database | http://localhost:3003 | PostgreSQL and Redis service health |
| Security | http://localhost:3004 | Authentication and audit events |
| Governance | http://localhost:3005 | Baseline policies and governance visibility |
| Backend API | http://localhost:8000 | API health, OpenAPI docs and metrics |
| API docs | http://localhost:8000/docs | Swagger UI |
| Prometheus metrics | http://localhost:8000/metrics | HTTP request counters |

All six browser workspaces use the same authentication service and protected API. Operational consoles require an administrator role.

## Architecture

- **Generative UI:** isolated prompt-first interface; only the user prompt and final answer are shown.
- **Orchestration:** FastAPI invokes the existing LangGraph supervisor and specialist workflow. Specialist execution fans out in parallel and converges through a single synthesis barrier.
- **Agentic AI:** separate workspace for the Chief Orchestrator, Deep Thinking Researcher, Deep Citation Researcher and Qualified Quantified Researcher.
- **Data services:** PostgreSQL stores users, research runs, audit events and governance policies. Redis provides short-lived runtime state and login-attempt throttling.
- **Security:** signed HTTP-only session cookie, local password authentication, optional Google OpenID Connect, role checks, login throttling and audit logging.
- **Governance:** seeded baseline policy records for data retention, model approval, human oversight and access review.

## Quick start with Docker Compose

1. Copy .env.example to .env.
2. Review the local credentials and inference endpoint in .env.
3. Start the stack with the command: docker compose up --build.
4. Open http://localhost:3000.

The local first-run administrator is username admin, password admin. The administrator is forced to change this password on the first sign-in before any workspace API can be used. This default is for local development only. Set a unique ADMIN_PASSWORD, a long random SESSION_SECRET, secure cookies and HTTPS before deploying outside a trusted local machine.

PostgreSQL and Redis are available to application containers on the Compose network. Their ports are not published to the host by default.

## Google SSO setup

1. Create an OAuth 2.0 Web application client in Google Cloud Console.
2. Add the exact authorized redirect URI http://localhost:8000/auth/google/callback for local development.
3. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.
4. Restart the API and UI services.

Google identities are provisioned with the user role. Administrator access remains an explicit local/admin provisioning responsibility; Google sign-in does not automatically grant admin privileges. To allow a specific Google identity to sign in as the seeded administrator, set ADMIN_EMAIL to that verified Google email before the administrator is first created. For production, use HTTPS and set SESSION_COOKIE_SECURE=true.

## Local Python development

Install Python 3.11+ and the packages in requirements.txt. Start PostgreSQL and Redis, configure .env, then run the API:

    uvicorn backend.main:app --reload --port 8000

Run the user UI in another terminal:

    CONSOLE_SECTION=user uvicorn backend.console:app --reload --port 3000

Run each operational console separately by setting CONSOLE_SECTION to orchestrator, agents, database, security or governance, and assigning its matching port from the table above.

For non-Docker local development, set DATABASE_URL to a reachable PostgreSQL instance and REDIS_URL to a reachable Redis instance. If DATABASE_URL is omitted, the application uses a local SQLite file for basic development.

## Configuration

See .env.example for the full environment variable list. The LLM provider remains OpenAI-compatible (Ollama by default). In Docker, host.docker.internal is used to reach an Ollama instance running on the host.

## Operational notes

- Database tables are initialized automatically at API startup for this MVP. Use a versioned migration system such as Alembic before introducing production schema changes.
- Google SSO requires valid OAuth credentials and an exact redirect URI.
- Configure HTTPS termination, trusted proxy settings, backups, secret management, retention schedules and external observability before production.
- The security and governance consoles provide initial administrative visibility; they are not a substitute for a full SIEM, policy engine or compliance certification.
- Research outputs depend on the configured language models and web-search provider availability.

## License

MIT. See LICENSE.
