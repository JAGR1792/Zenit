# Architecture

Monolithic modular architecture. Frontend (Vue 3 + TS + Vite) talks to
FastAPI backend over REST/JSON. Simulation engine is a pure Python package
under `backend/app/simulation` and can run without FastAPI or a browser.

See plan_stack_space_mission.md for full plan.