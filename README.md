
### Mobile game BANG: DICE GAME
API → recebe estado do jogo
Agente → decide ação
Simulador → permite treino / testes locais

bang-ai/
│
├── app/
│   ├── main.py             # FastAPI entrypoint
│   ├── schemas.py          # Models (Pydantic)
│   ├── agent.py            # Lógica do agente
│   ├── env.py              # Simulador simplificado
│   ├── policy.py           # Heurística / decisão
│   └── utils.py
│
├── train/
│   └── self_play.py        # Simulação de partidas
│
├── requirements.txt
└── README.md


to run
uvicorn ai.ai_main:app --reload


