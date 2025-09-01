# Technical Assumptions

## Repository Structure: Monorepo
Single repository containing both frontend and backend Python code, shared documentation, and deployment configurations. This supports tight integration between the collaborative matrix interfaces and real-time backend coordination.

## Service Architecture: Monolith
Python-based monolithic application leveraging frameworks like FastAPI for backend APIs and a Python web framework (Django/Flask) or Python-compiled frontend solution. Given the tight coupling between collaborative features (presence, locking, real-time updates) and complex domain relationships, a monolithic approach simplifies development and deployment for MVP.

## Testing Requirements: Unit + Integration
Comprehensive testing covering both individual component logic (matrix operations, export generation, relationship validation) and integration between collaborative features (WebSocket coordination, data consistency, concurrent editing conflict resolution).

## Additional Technical Assumptions and Requests

**Backend Framework:** FastAPI for high-performance async API handling real-time collaboration requirements

**Frontend Approach:** Python-based frontend solution (Pyodide/PyScript, Streamlit, or Django templates with HTMX) to maintain full-stack Python consistency

**Real-time Communication:** WebSockets for presence indicators, collaborative editing, and live updates

**Database:** PostgreSQL for robust relational data modeling supporting complex object relationships and ACID transactions for collaborative editing

**Session Management:** Redis for managing user presence, collaborative locks, and session state

**Export Generation:** Python libraries for JSON serialization, CSV generation (pandas), Mermaid diagram creation, and HTML template rendering

**Development Environment:** Docker containerization for consistent development and deployment across team members

**Deployment Target:** Container-ready deployment (Docker/Kubernetes) supporting horizontal scaling for collaborative features

**File Storage:** Local filesystem or cloud storage (S3-compatible) for generated export bundles and project snapshots
