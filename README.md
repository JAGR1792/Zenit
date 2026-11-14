# Space Mission Design Game

Interactive experience to design, validate and simulate a space mission.

## Stack
Vue 3 + TypeScript + Vite + Tailwind + Three.js (frontend); Python + FastAPI +
Pydantic + NumPy + SQLite (backend); Docker Compose.

## Run backend
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run frontend
```
cd frontend
npm install
npm run dev
```

## Tests
```
cd backend && pytest
cd frontend && npm test
```