# VulnForge - convenience targets.
# On Windows without `make`, run the underlying commands directly (shown in each target).

.PHONY: install dev-api dev-web challenge-check

install:           ## Install the api Python deps
	pip install -r api/requirements.txt

dev-api:           ## Run the api origin (FastAPI) on :8081
	python -m uvicorn api.main:app --port 8081 --reload

dev-web:           ## Run the web origin (Next.js) on :8082
	cd web && npm run dev

challenge-check:   ## Prove the CHALLENGE face (VF_LAB=0) leaks no answer-key signal
	python tools/challenge_check.py
