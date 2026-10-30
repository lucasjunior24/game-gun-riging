# Resultados da Fase 5

Experimentos estatisticos: nao sao testes de CI. Os arquivos brutos (`*.jsonl`, `*.npz`)
ficam fora do git; aqui ficam os numeros. Intervalos sao de Wilson 95%.

## 2026-10-29: primeira linha de base (commit base `cfcc5f8` + Fase 5)

### Mesmo agente em todos os assentos

`python -m app.sim.run --games 1000 --players 4,5,8 --agent heuristic --belief`
`python -m app.sim.run --games 600 --players 4,5,8 --agent bayes:medio --belief`

| Jogadores | Agente | Xerife | Fora da lei | Renegado | Turnos (media) | Fogo amigo | Log-loss da crenca |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | heuristic | 37,0% [34,1; 40,0] | 54,1% | 8,9% | 14,2 | 7,7% | 0,190 |
| 4 | bayes:medio | 16,7% [13,9; 19,9] | 63,7% | 19,7% | 11,8 | 3,2% | 0,229 |
| 5 | heuristic | 56,9% [53,8; 59,9] | 39,0% | 4,1% | 16,6 | 12,1% | 0,561 |
| 5 | bayes:medio | 49,8% [45,8; 53,8] | 39,5% | 10,7% | 14,5 | 5,7% | 0,562 |
| 8 | heuristic | 59,2% [56,1; 62,2] | 37,3% | 3,5% | 24,9 | 15,3% | 0,832 |
| 8 | bayes:medio | 49,3% [45,3; 53,3] | 38,7% | 12,0% | 22,4 | 8,3% | 0,776 |

- Nenhuma partida bateu `max_turns`. Todos os times vencem, inclusive o Renegado (o bug antigo dava 0%).
- O Bayes acerta menos tiros em aliados que o heuristico: 3 a 8% contra 8 a 15%.
- Com 4 jogadores e Bayes em todos os assentos, o Xerife so vence 16,7%. Pode ser o bot de
  Xerife fraco ou o equilibrio do jogo com 4 jogadores. Ainda falta investigar.
- Causas de morte (Bayes, 5 jogadores): tiro 72%, indios 23%, Gatling 3%, Dinamite 1%.

### Comparacao pareada heuristic (A) x bayes:medio (B), 5 jogadores, 300 sementes

| Referencia nos outros assentos | A | B | So B / so A | McNemar p |
| --- | --- | --- | --- | --- |
| heuristic | 39,3% | 41,2% | 225 / 196 | 0,17 |
| bayes:medio | 37,1% | 37,3% | 223 / 220 | 0,92 |

**O Bayes nao vence o heuristico de forma significativa.** Pela ordem do plano, o certo e
voltar a Fase 4 antes de investir no ajuste. Por papel (referencia heuristic), o Bayes ganha
como Assistente (+7 pontos) e Renegado (+6), mas perde como Fora da lei (-3). Com referencia
Bayes, perde como Xerife (-9). O jogo do Xerife e do Fora da lei e o primeiro ponto a olhar.

### Ajuste da crenca (log-loss), 5 jogadores, 200 partidas de bayes:medio:n=10

`python -m app.sim.tune belief --games 200 --players 5`

| beta | epsilon | log-loss |
| --- | --- | --- |
| 0,5 | 0,01 | 0,523 (melhor) |
| 1,0 | 0,05 | 0,525 (padrao atual) |
| 2,0 | 0,05 | 0,621 |
| 4,0 | 0,01 | 0,872 |

O padrao ja esta no otimo da grade: a diferenca para o melhor ponto e desprezivel. Os pesos
`w` fazem os jogadores parecerem mais previsiveis do que sao (beta alto piora muito).

### Rede de valor v1

- Dados: `python -m app.sim.dataset --games 300 --players 4,5,6,7,8 --agent bayes:medio:n=10`
  1500 partidas, 138 653 posicoes (uma por jogador vivo no inicio de cada turno), 41% positivas.
- Treino: `python -m app.sim.train_value results/data/gen1.npz --out app/models/value_net_v1.pt`
  com a validacao separada por partida (20% das partidas) e parada antecipada (11 epocas).
- Validacao: BCE 0,569 (prever sempre a media dá 0,677), AUC 0,757, ECE 0,041. A rede e
  bem calibrada ate 0,5 e um pouco otimista acima disso (diz 0,84, o real e 0,77).

Comparacao pareada bayes:medio (A) x bayes:medio com `value=app/models/value_net_v1.pt` (B),
5 jogadores, 300 sementes, referencia bayes:medio:

| A | B | So B / so A | McNemar p |
| --- | --- | --- | --- |
| 37,3% | 39,5% | 268 / 234 | 0,14 |

A diferenca e de +2,3 pontos, **sem significancia**. Ela vem quase toda do Xerife
(47,7% -> 66,7%, em 300 pares); como Assistente e Fora da lei, a rede perde 2 a 4 pontos.
Proximo passo: mais sementes para confirmar o efeito no Xerife e uma segunda geracao de dados
gerada com a rede (expert iteration), mantendo `gen1.npz` no treino.

Nao rodado ainda: `tune eval` (busca da tabela `rel`). Cada tentativa custa uma comparacao
pareada, entao vale rodar depois de resolver a fraqueza do Bayes contra o heuristico.
