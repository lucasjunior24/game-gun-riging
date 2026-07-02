# ShotPolicyService

Este documento explica como o `ShotPolicyService` faz a predicao de tiros e como esse modulo se encaixa no fluxo do backend.

## Objetivo do modulo

O `ShotPolicyService`, definido em `app/services/policy_service.py`, decide automaticamente como distribuir tiros quando o jogador atual tem resultados de dado iguais a `1` ou `2`.

Ele recebe um `ExecuteDicesDTO`, analisa as opcoes de jogadores em cada distancia e retorna uma lista de decisoes com:

- jogador alvo;
- quantidade de tiros;
- distancia do tiro;
- confianca da decisao.

Depois disso, a predicao pode ser aplicada no proprio objeto de execucao, preenchendo a lista `user_bullets` de cada distancia.

O alvo agora tambem considera crenca por identidade. A identidade do `XERIFE` e tratada como revelada: se um jogador e reconhecido como Xerife, sua probabilidade de `IdentityDTO.XERIFE` e `1.0`, sem tentativa de inferencia.

## Onde o modulo e usado

O fluxo principal acontece no endpoint `PUT /dices/execution`, em `app/views/dice.py`.

```python
shot_policy_service = ShotPolicyService()
prediction = shot_policy_service.predict(execution)
execution_result = shot_policy_service.apply_prediction(execution, prediction)
```

Ou seja:

1. A API recebe o estado de execucao dos dados.
2. O `ShotPolicyService` carrega o modelo de politica de tiros, se existir.
3. O servico prediz alvo e quantidade de tiros.
4. A predicao e aplicada ao DTO de resposta.
5. A API retorna o `ExecuteDicesDTO` atualizado.

## Entrada da predicao

A entrada principal e o `ExecuteDicesDTO`, definido em `app/dtos/dice.py`.

Campos mais importantes:

- `game_id`: identificador da partida.
- `current_player`: jogador que esta executando a jogada.
- `current_identity`: identidade atual do jogador, por exemplo `Xerife`.
- `table_situation`: descricao do estado da mesa.
- `one_distance`: dados e alvos possiveis para distancia `1`.
- `two_distance`: dados e alvos possiveis para distancia `2`.

Cada distancia usa `ExecuteDistanceDTO`:

- `bullet_total`: quantidade de tiros disponivel naquela distancia.
- `players_options`: jogadores que podem receber tiros naquela distancia.
- `user_bullets`: lista preenchida com o resultado final da decisao.

Cada `PlayerDTO` possui `papel_probability`, que usa um DTO tipado para representar probabilidades por identidade:

- `xerife`;
- `fora_da_lei`;
- `renegado`;
- `assistente`.

As validacoes de identidade usam o enum `IdentityDTO`, definido em `app/dtos/character.py`.

## Saida da predicao

O metodo `predict()` retorna um `ShotPolicyPredictionDTO`, definido em `app/dtos/policy.py`.

Ele contem uma lista de `ShotPolicyDecisionDTO`.

Cada decisao possui:

- `target_user_name`: nome do jogador alvo.
- `shots`: quantidade de tiros, entre `1` e `3`.
- `distance`: distancia da decisao, podendo ser `"1"` ou `"2"`.
- `confidence`: confianca calculada para a escolha.

## Como a predicao funciona

O metodo `predict()` percorre duas distancias possiveis:

```python
for distance_label in ("1", "2"):
```

Para cada distancia, ele busca o respectivo `ExecuteDistanceDTO`:

- `"1"` usa `execution.one_distance`;
- `"2"` usa `execution.two_distance`.

A distancia e ignorada quando:

- nao existe;
- `bullet_total` e menor ou igual a zero;
- nao existem jogadores em `players_options`.

Se a distancia for valida, o servico decide o alvo, a quantidade de tiros e a confianca.

Para escolher o alvo, o servico calcula um score de crenca por candidato. Esse score considera:

- probabilidade do candidato ser `XERIFE`, `FORA_DA_LEI`, `RENEGADO` ou `ASSISTENTE`;
- papel do jogador atual;
- se o candidato esta vivo;
- se o candidato e o proprio jogador atual;
- flechas;
- distancia;
- quantidade de tiros disponiveis.

Quando o modelo neural esta carregado, o score final combina:

```text
score_final = score_neural * 0.35 + score_crenca * 0.65
```

Quando o modelo nao esta carregado, o servico usa somente o score de crenca.

## Carregamento do modelo

No construtor, o servico tenta carregar o arquivo:

```text
app/models/shot_policy_model.pt
```

Esse arquivo e carregado com PyTorch usando CPU:

```python
checkpoint = torch.load(self.model_path, map_location=self.device)
```

O checkpoint precisa conter:

- `input_size`;
- `target_model_state_dict`;
- `shot_model_state_dict`.

Com isso, o servico recria duas redes neurais:

- `ShotPolicyTargetNet`: escolhe o melhor alvo.
- `ShotPolicyShotNet`: escolhe a quantidade de tiros.

Depois de carregar os pesos, os modelos entram em modo de avaliacao com `.eval()`.

## Modelo de alvo

A rede `ShotPolicyTargetNet` recebe o vetor de features e retorna um score unico para cada candidato.

Arquitetura:

```text
input_size -> Linear(32) -> ReLU -> Linear(16) -> ReLU -> Linear(1)
```

Durante a predicao, cada jogador de `players_options` e avaliado separadamente.

O score passa por `sigmoid`:

```python
score = torch.sigmoid(self.target_model(features)).item()
```

Esse score neural e combinado com o score de crenca. O jogador com maior score final e escolhido como alvo:

```python
return max(scores, key=lambda item: item[0])[1]
```

## Modelo de quantidade de tiros

A rede `ShotPolicyShotNet` recebe o mesmo vetor de features, mas retorna tres logits.

Arquitetura:

```text
input_size -> Linear(24) -> ReLU -> Linear(12) -> ReLU -> Linear(3)
```

Cada posicao representa uma quantidade possivel de tiros:

- indice `0`: 1 tiro;
- indice `1`: 2 tiros;
- indice `2`: 3 tiros.

O servico pega o maior logit com `argmax`, soma `1` e limita o resultado entre `1` e `3`.

```python
shot_index = int(logits.argmax(dim=1).item()) + 1
return min(3, max(1, shot_index))
```

## Vetor de features

Antes de chamar as redes neurais, o servico transforma o estado do jogo em um vetor numerico.

O vetor atual tem 12 posicoes:

| Indice | Feature | Descricao |
| --- | --- | --- |
| 0 | `distance.bullet_total` | Total de tiros disponiveis na distancia |
| 1 | `len(distance.players_options)` | Quantidade de alvos possiveis |
| 2 | `target_player.position` | Posicao do candidato na mesa |
| 3 | `target_player.is_alive` | `1.0` se o candidato esta vivo, senao `0.0` |
| 4 | `target_player.bullet` | Balas do candidato |
| 5 | `target_player.arrow` | Flechas do candidato |
| 6 | `target_player.is_bot` | `1.0` se o candidato e bot, senao `0.0` |
| 7 | `execution.current_player.bullet` | Balas do jogador atual |
| 8 | `execution.current_player.arrow` | Flechas do jogador atual |
| 9 | `execution.current_identity == IdentityDTO.XERIFE` | `1.0` se o jogador atual e xerife |
| 10 | `current_player == target_player` | `1.0` se o candidato e o proprio jogador atual |
| 11 | `distance.bullet_total > 1` | `1.0` se ha mais de um tiro disponivel |

Esse vetor e convertido para um tensor `float32` e ganha uma dimensao de batch:

```python
torch.tensor(features, dtype=torch.float32, device=self.device).unsqueeze(0)
```

## Calculo da confianca

A confianca usa o score do alvo escolhido.

Quando o modelo neural esta disponivel, o servico combina o score neural e o score de crenca. Quando o modelo nao esta disponivel, usa apenas a crenca. O resultado e limitado entre `0.3` e `0.95`.

```python
confidence = score_neural * 0.35 + score_crenca * 0.65
return round(float(max(0.3, min(0.95, confidence))), 2)
```

Isso evita confiancas muito baixas ou artificialmente perfeitas.

## Fallback sem modelo treinado

Se o arquivo `app/models/shot_policy_model.pt` nao existir, ou se os modelos nao forem carregados, o servico usa a politica de crenca.

Nesse caso:

- o alvo escolhido e o candidato com maior score de crenca;
- jogadores mortos recebem penalidade forte;
- o proprio jogador recebe penalidade forte;
- a quantidade de tiros respeita `bullet_total` e e limitada entre `1` e `3`;
- a confianca vem do score de crenca, limitada entre `0.3` e `0.95`.

Esse fallback permite que o endpoint continue funcionando mesmo sem modelo treinado.

## Aplicacao da predicao

Depois de gerar a predicao, `apply_prediction()` percorre cada decisao e adiciona um `UserBulletsDTO` na distancia correspondente.

Resultado esperado em cada distancia:

```python
UserBulletsDTO(
    user_name=decision.target_user_name,
    shots=decision.shots,
)
```

Assim, a resposta final do endpoint ja vem com `user_bullets` preenchido.

## Treinamento do modelo

O treinamento esta em `app/training.py`.

O arquivo gera exemplos sinteticos com:

- jogador atual chamado `Alice`;
- identidade sorteada entre `Xerife`, `Fora da lei` e `Renegado`;
- jogadores simulados com posicao, balas e flechas aleatorias;
- distancias `1` e `2` com totais de tiros aleatorios.

Para cada exemplo valido, o treinamento escolhe como alvo sintetico o jogador com maior combinacao de:

```python
(p.is_alive, p.bullet, p.arrow)
```

A label de tiros e:

```python
min(3, max(1, distance.bullet_total))
```

O treinamento usa:

- `binary_cross_entropy_with_logits` para o modelo de alvo;
- `cross_entropy` para o modelo de quantidade de tiros;
- otimizador `Adam`;
- `20` epocas;
- seed fixa `42`.

Ao final, o checkpoint e salvo em:

```text
app/models/shot_policy_model.pt
```

## Resumo do fluxo

```text
ExecuteDicesDTO
    |
    v
ShotPolicyService.predict()
    |
    |-- valida distancia 1
    |-- valida distancia 2
    |
    |-- cria vetor de features para cada candidato
    |-- ShotPolicyTargetNet escolhe o alvo
    |-- ShotPolicyShotNet escolhe a quantidade de tiros
    |-- calcula confianca
    |
    v
ShotPolicyPredictionDTO
    |
    v
ShotPolicyService.apply_prediction()
    |
    v
ExecuteDicesDTO com user_bullets preenchido
```

## Correcao aplicada

O metodo `apply_prediction()` usa `get_execution_distance()` para localizar a distancia correta antes de preencher `user_bullets`.
