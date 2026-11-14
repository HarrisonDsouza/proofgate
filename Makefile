-include .env
export

.PHONY: test-restart ci secret-scan install smoke setup seed reset dev detector test lint rules bypass test-conflict explain eval eval-heldout baseline calibrate-detector calibrate-prd codes deploy

install:      ; pip install -r requirements-dev.txt
smoke:        ; python -m pg.db --smoke
setup:        ; python -m pg.db --setup
seed:         ; python -m seed.generate --reset --seed 20261114
reset: seed
dev:          ; uvicorn pg.main:app --port 8080 --reload
detector:     ; RUN_BACKGROUND=0 python -m pg.detector          # separate process for the live kill/restart
test:         ; pytest -q
lint:         ; ruff check pg eval seed tests data
rules:        ; curl -s "localhost:8080/rules?tenant=payer-acme" | python -m json.tool
bypass:       ; python -m eval.bypass
test-conflict:; DEMO_DEBUG_HOOKS=true python -m eval.test_conflict
test-restart: ; python -m eval.test_detector_restart
explain:      ; curl -s -H "X-Tenant-Id: payer-acme" localhost:8080/api/explain/window | python -m json.tool
codes:        ; python -m data.pipeline.codes
calibrate-detector: ; python -m eval.calibrate_detector --tenant payer-live
calibrate-prd:      ; python -m eval.calibrate_detector --prd-model
eval:         ; python -m eval.simulate --seed 1
eval-heldout: ; python -m eval.simulate --seed 20261114
baseline:     ; python -m eval.simulate --seed 20261114 --baseline
deploy:       ; gcloud run deploy proofgate --source . --region us-central1 --allow-unauthenticated --min-instances 1

# Same checks as .github/workflows/ci.yml, runnable locally (use before every PR while GitHub Actions is unavailable)
secret-scan:  ; ! git grep -nE "(sk-ant-|sk-[A-Za-z0-9]{20,}|mongodb\+srv://[^<\"]+:[^<\"]+@)" -- . ':!*.md' ':!.env.example' ':!.github/workflows/ci.yml' ':!Makefile' && echo "secret-scan: PASS"
ci: lint test secret-scan
