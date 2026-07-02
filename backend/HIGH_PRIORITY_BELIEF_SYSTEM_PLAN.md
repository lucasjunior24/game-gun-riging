# Plano de implementacao: sistema de crenca por identidade

Este documento descreve como eu implementaria a feature de Prioridade alta do `TODO`:

> Implementar sistema de crenca sobre identidade dos jogadores + decisao de tiro baseada nessa crenca.

O objetivo e fazer o bot parar de escolher alvo apenas por features simples, como posicao ou score neural generico, e passar a considerar a identidade provavel de cada jogador dentro da partida.

## Resultado esperado

Ao final da feature, cada jogador deve ter uma distribuicao de probabilidade por identidade:

- `XERIFE`
- `FORA_DA_LEI`
- `RENEGADO`
- `ASSISTENTE`

Essa distribuicao deve influenciar a decisao de tiro considerando:

- identidade provavel do alvo;
- papel do jogador atual;
- vida do alvo;
- flechas do alvo;
- distancia;
- quantidade de tiros disponiveis.

O termo usado para o papel de aliado do Xerife deve ser sempre `Assistente`.

## Decisao de arquitetura

Eu implementaria primeiro no fluxo principal do backend, dentro de `app/`, porque hoje a decisao real do endpoint acontece em:

```text
app/views/dice.py -> ShotPolicyService
```

O pacote `ai/` tem ideias experimentais de crenca e politica, mas ele nao esta conectado ao endpoint `/dices/execution`. Por isso, eu usaria `ai/` como referencia conceitual, mas faria a feature nascer no modulo que ja esta em producao no fluxo da API.

## Passo 1: ajustar o modelo de dados do jogador

Arquivo principal:

```text
app/dtos/players.py
```

Hoje `PlayerDTO` tem:

```python
papel_probability: float = Field(default=0.0)
```

Esse campo representa apenas um numero solto. Para a nova feature, ele precisa virar uma distribuicao por identidade.

Eu substituiria ou evoluiria esse campo para algo como:

```python
papel_probability: dict[IdentityDTO, float]
```

Na pratica, por compatibilidade com JSON/Pydantic, pode ser melhor usar chaves string com os valores do enum:

```python
papel_probability: dict[str, float] = Field(default_factory=dict)
```

As chaves esperadas seriam:

```text
Xerife
Fora da lei
Renegado
Assistente
```

Esses valores devem vir do enum `IdentityDTO`, definido em:

```text
app/dtos/character.py
```

## Passo 2: criar um servico de crenca

Eu criaria um novo arquivo:

```text
app/services/belief_service.py
```

Responsabilidade desse servico:

- inicializar probabilidades quando o jogador ainda nao tiver `papel_probability`;
- normalizar probabilidades para a soma fechar em `1.0`;
- obter a identidade mais provavel de um jogador;
- expor helpers simples para o `ShotPolicyService`.

Funcoes principais:

```python
class BeliefService:
    def initialize_player_belief(player: PlayerDTO) -> dict[str, float]
    def normalize(probabilities: dict[str, float]) -> dict[str, float]
    def get_identity_probability(player: PlayerDTO, identity: IdentityDTO) -> float
    def get_most_likely_identity(player: PlayerDTO) -> IdentityDTO
```

Neste primeiro passo, sem historico de acoes, a crenca pode ser inicializada de forma neutra:

```text
Xerife: 0.25
Fora da lei: 0.25
Renegado: 0.25
Assistente: 0.25
```

Depois, quando a feature de historico de acoes for implementada, esse mesmo servico pode atualizar as suspeitas com base em eventos.

## Passo 3: definir matriz de prioridade por papel atual

O bot precisa avaliar se uma identidade e boa ou ruim para atacar dependendo do papel dele.

Eu criaria uma tabela de pesos no proprio `BeliefService` ou em um modulo pequeno de politica, por exemplo:

```text
app/services/shot_priority_service.py
```

Regras iniciais sugeridas:

| Papel atual | Alvo Xerife | Alvo Fora da lei | Alvo Renegado | Alvo Assistente |
| --- | ---: | ---: | ---: | ---: |
| Xerife | baixo | alto | medio | muito baixo |
| Assistente | muito baixo | alto | medio | baixo |
| Fora da lei | alto | baixo | medio | alto |
| Renegado | medio/alto | medio | baixo | medio |

Em numeros, isso poderia virar:

| Papel atual | Xerife | Fora da lei | Renegado | Assistente |
| --- | ---: | ---: | ---: | ---: |
| Xerife | -1.0 | 1.0 | 0.4 | -0.8 |
| Assistente | -1.0 | 1.0 | 0.5 | -0.7 |
| Fora da lei | 1.0 | -0.8 | 0.3 | 0.8 |
| Renegado | 0.6 | 0.4 | -0.6 | 0.3 |

Esses pesos nao precisam ser perfeitos no inicio. Eles servem como heuristica clara e ajustavel.

## Passo 4: calcular score de alvo baseado em crenca

Eu adicionaria ao `ShotPolicyService` um caminho de score heuristico por identidade.

Para cada candidato em `players_options`, calcular:

```text
identity_score =
    prob(Xerife) * peso_contra_Xerife
  + prob(Fora da lei) * peso_contra_Fora_da_lei
  + prob(Renegado) * peso_contra_Renegado
  + prob(Assistente) * peso_contra_Assistente
```

Depois somar ajustes de estado:

```text
life_score      = maior se o alvo estiver com pouca vida
arrow_score     = maior se o alvo tiver muitas flechas
distance_score  = leve preferencia por distancia 1
self_penalty    = penalidade forte se o alvo for o proprio jogador
alive_penalty   = penalidade forte se o alvo nao estiver vivo
```

Score final sugerido:

```text
target_score =
    identity_score * 0.55
  + life_score * 0.20
  + arrow_score * 0.10
  + distance_score * 0.10
  + available_shots_score * 0.05
  - self_penalty
  - dead_penalty
```

Com isso, a identidade provavel vira o principal fator da decisao, mas nao o unico.

## Passo 5: integrar com `ShotPolicyService`

Arquivo:

```text
app/services/policy_service.py
```

Eu faria a integracao em tres partes.

Primeiro, instanciar o servico de crenca no construtor:

```python
self.belief_service = BeliefService()
```

Segundo, criar um metodo novo:

```python
def _score_candidate_by_belief(
    self,
    execution: ExecuteDicesDTO,
    distance: ExecuteDistanceDTO,
    distance_label: str,
    candidate: PlayerDTO,
) -> float:
```

Terceiro, atualizar `_predict_target()` para considerar esse score.

Existem duas opcoes:

1. Usar somente a heuristica de crenca para escolher alvo.
2. Combinar score neural atual com score de crenca.

Eu escolheria a opcao 2 para preservar o modelo existente:

```text
final_score = neural_score * 0.35 + belief_score * 0.65
```

Se o modelo `.pt` nao estiver carregado, o sistema usaria somente `belief_score`, em vez do fallback atual por maior `position`.

## Passo 6: atualizar vetor de features do modelo

Hoje o vetor de features tem 12 posicoes e nao inclui as probabilidades por identidade.

Eu adicionaria quatro novas features:

```text
prob_Xerife
prob_Fora_da_lei
prob_Renegado
prob_Assistente
```

Tambem adicionaria features one-hot para o papel atual:

```text
current_is_Xerife
current_is_Fora_da_lei
current_is_Renegado
current_is_Assistente
```

O vetor passaria de 12 para 19 ou 20 features, dependendo se mantivermos a feature antiga `current_identity == "xerife"`.

Como isso muda `input_size`, sera necessario retreinar e salvar novamente:

```text
app/models/shot_policy_model.pt
```

## Passo 7: atualizar treinamento sintetico

Arquivo:

```text
app/training.py
```

O treinamento sintetico precisa gerar `papel_probability` para cada jogador.

Exemplo de distribuicao:

```text
Player suspeito de Fora da lei:
Xerife: 0.05
Fora da lei: 0.70
Renegado: 0.15
Assistente: 0.10
```

Tambem precisa mudar a escolha do alvo sintetico. Em vez de escolher apenas por:

```python
(p.is_alive, p.bullet, p.arrow)
```

O target ideal deve ser escolhido pelo mesmo score de prioridade baseado em identidade. Assim, o modelo neural aprende a imitar a politica nova.

## Passo 8: corrigir `apply_prediction`

Antes ou junto dessa feature, eu corrigiria o bug atual:

```python
distance = self.get_distance(execution, decision.distance)
```

O metodo `get_distance()` nao existe. A chamada correta deve usar:

```python
distance = self.get_execution_distance(execution, decision.distance)
```

Essa correcao e importante porque a feature pode predizer corretamente, mas falhar ao aplicar a resposta.

## Passo 9: adicionar testes

Eu criaria testes focados em comportamento, nao em detalhes internos da rede neural.

Arquivos sugeridos:

```text
tests/services/test_belief_service.py
tests/services/test_shot_policy_service.py
```

Cenarios importantes:

- inicializa crenca neutra quando `papel_probability` esta vazio;
- normaliza probabilidades corretamente;
- usa sempre `Assistente`, nunca `vice`;
- Xerife prioriza alvo com alta chance de `Fora da lei`;
- Fora da lei prioriza alvo com alta chance de `Xerife`;
- alvo morto nao deve ser escolhido;
- o proprio jogador nao deve ser escolhido como alvo;
- distancia sem tiros nao gera decisao;
- `apply_prediction()` preenche `user_bullets`.

## Passo 10: atualizar documentacao

Depois da implementacao, eu atualizaria:

```text
SHOT_POLICY_SERVICE.md
```

Incluindo:

- novo formato de `papel_probability`;
- como o score de crenca e calculado;
- como a politica combina modelo neural e heuristica;
- como retreinar o modelo.

Tambem atualizaria o `TODO`, marcando a feature de Prioridade alta como concluida quando os testes passarem.

## Ordem de execucao recomendada

1. Corrigir `apply_prediction()` para usar `get_execution_distance()`.
2. Criar `BeliefService`.
3. Evoluir `PlayerDTO.papel_probability`.
4. Criar score heuristico de prioridade por identidade.
5. Integrar score no `ShotPolicyService`.
6. Adicionar testes do fluxo sem depender do modelo `.pt`.
7. Atualizar features do modelo neural.
8. Atualizar `app/training.py`.
9. Retreinar o modelo.
10. Atualizar documentacao final.

## Primeira versao que eu entregaria

Para reduzir risco, eu faria a primeira entrega sem retreinar a rede neural.

Essa primeira versao teria:

- `BeliefService`;
- `papel_probability` por identidade;
- score heuristico de alvo;
- fallback inteligente baseado em crenca;
- combinacao entre score neural e score de crenca quando o modelo existir;
- testes do comportamento principal.

Depois disso, numa segunda entrega, eu atualizaria o vetor de features e o treinamento para o modelo aprender diretamente com essas probabilidades.
