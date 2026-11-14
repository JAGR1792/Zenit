# Zenit

Simulador narrativo de misiones espaciales (juego serio educativo). Estado actual: MVP fase 0 (hello world).

## Referencias
- `docs/implementation-plan.md` — plan técnico completo.
- `docs/game-design.md` — documento de diseño del juego.
- `artboard.html` — dirección de arte (paleta y boceto).
- `vercel.json` — infraestructura multi-service.

## Stack
- Backend: FastAPI (Python)
- Frontend: Vue 3 + Vite

## Run backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run frontend
```bash
cd frontend
npm install
npm run dev
```
