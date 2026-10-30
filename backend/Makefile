deploy-local:
	docker build -t go-notify-local .
	docker-compose -f compose/compose-local/docker-compose.yaml up -d
		
deploy-develop:
	docker build -t go_notify_develop .
	docker-compose -f compose/compose-develop/docker-compose.yaml up -d


deploy-teste:
	docker build -t go-notify-local .
	docker-compose -f docker-compose.yml up -d

test:
	python -m pytest tests

cov-total:
	python -m pytest --cov=app tests

# coverage:
# 	py.test app/application_manager.py --cov-report xml:cov.xml --cov .
	
coverage:
	py.test app/__init__.py --cov-report xml:cov.xml --cov=app tests


deploy-nginx:
	docker-compose -f compose/compose-local/nginx.yaml up
# ---------- Fase 5: simulador e treino (experimentos, nao sao testes de CI) ----------
GAMES ?= 1000
PLAYERS ?= 5
AGENT ?= bayes:medio
OUT ?= results/sim.jsonl

sim:
	python -m app.sim.run --games $(GAMES) --players $(PLAYERS) --agent $(AGENT) --belief --out $(OUT)

report:
	python -m app.sim.report $(OUT)

compare:
	python -m app.sim.compare --a $(A) --b $(B) --games $(GAMES) --players $(PLAYERS)

tune-belief:
	python -m app.sim.tune belief --games $(GAMES) --players $(PLAYERS)

tune-eval:
	python -m app.sim.tune eval --games $(GAMES) --players $(PLAYERS)

dataset:
	python -m app.sim.dataset --games $(GAMES) --players 4,5,6,7,8 --out $(DATA)

train-value:
	python -m app.sim.train_value $(DATA)
