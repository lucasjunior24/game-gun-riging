# Fluxo de historico e crenca

O diagrama PlantUML esta em:

```text
BELIEF_HISTORY_FLOW.puml
```

Ele descreve a evolucao da IA para salvar acoes da partida em um historico e usar esse historico para atualizar `papel_probability` antes da proxima decisao de tiro.

Status atual: implementado no fluxo do `ShotPolicyService` quando o payload de execucao traz `action_history`.

## O que salvar no historico

Para cada acao relevante, o backend pode salvar um evento tipado usando `GameActionHistoryDTO`.

Campos principais:

- `game_id`
- `round_number`
- `turn_number`
- `actor_user_name`
- `actor_identity`, quando revelada
- `action_type`
- `target_user_name`
- `target_identity`, quando revelada
- `distance`
- `shots`
- `target_life_before`
- `target_life_after`
- `actor_bullets_before`
- `actor_bullets_after`
- `target_arrows_before`
- `target_arrows_after`
- `created_at`

Tipos de acao iniciais:

- `TIRO`
- `GATLING`
- `CERVEJA`
- `INDIOS`

## Como o historico atualizaria a crenca

A cada evento novo, o `BeliefService` avaliaria quem agiu, quem foi alvo e qual identidade ja e conhecida.

Regras iniciais:

- se alguem atira no Xerife revelado, aumenta a suspeita desse ator ser `FORA_DA_LEI` e um pouco `RENEGADO`;
- se alguem atira em jogador com alta chance de `FORA_DA_LEI`, aumenta a chance do ator ser `XERIFE` ou `ASSISTENTE`;
- se alguem ajuda o Xerife, por exemplo com `CERVEJA`, aumenta a chance do ator ser `ASSISTENTE`;
- jogadores que nao sao o Xerife revelado devem continuar com `IdentityDTO.XERIFE = 0.0`;
- depois de cada ajuste, o `IdentityProbabilityDTO` e normalizado para soma `1.0`.

Na proxima chamada do `ShotPolicyService.predict()`, o servico aplica `BeliefService.update_beliefs_from_history()` antes de calcular o alvo. Assim, o `score_crenca` usa essas probabilidades atualizadas e o `score_final` muda naturalmente conforme os tiros e acoes da partida acontecem.
