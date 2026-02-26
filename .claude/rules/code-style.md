# Code Style

## Python (Backend)
- Use type hints on all function signatures
- Use `async def` for all FastAPI route handlers
- Imports order: stdlib → third-party → local, separated by blank lines
- Route handlers stay thin — delegate logic to `services/`
- Never put business logic in `main.py`

## TypeScript / React (Frontend)
- Use `.tsx` for files with JSX, `.ts` for pure logic
- Functional components only, no class components
- Co-locate component styles and tests with the component file
- Custom hooks live in `src/hooks/`, prefixed with `use`
- API calls go through `src/api/`, never directly in components
