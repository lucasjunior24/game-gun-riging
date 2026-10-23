# Plano de implementação: motor de regras, correções e IA automática

Este documento descreve o plano para melhorar a lógica do jogo (backend e front), corrigir os bugs encontrados e estruturar a IA para que os bots joguem Bang! The Dice Game de forma automática e seguindo as regras.

## Regras de referência (Bang! The Dice Game)

- **Papéis:** Xerife (revelado, +2 de vida), Assistentes (querem o Xerife vivo), Foras da lei (querem o Xerife morto), Renegado (quer ser o último vivo).
  - 4 jogadores: Xerife, Renegado, 2 Foras da lei.
  - 5: + 1 Assistente. 6: + 1 Fora da lei. 7: + 1 Assistente. 8: + 1 Renegado.
- **Turno:** joga 5 dados e pode rolar de novo até 2 vezes, guardando os que quiser. Dinamite não pode ser rolada de novo. Com 3 Dinamites o jogador perde 1 de vida e para de rolar.
- **Faces:**
  - **1:** 1 de dano em um jogador a distância 1.
  - **2:** 1 de dano em um jogador a distância 2.
  - **Cerveja:** +1 de vida para qualquer jogador, sem passar do máximo.
  - **Gatling:** com 3 ou mais, 1 de dano em todos os outros jogadores, e quem rolou devolve suas flechas.
  - **Flecha:** o jogador pega uma flecha na hora. Quando a última das 9 flechas sai, acontece o **ataque indígena**: cada jogador perde 1 de vida por flecha que tem, e as flechas voltam para o centro.
- **Distância:** depende de onde cada um está sentado. Jogadores mortos saem da contagem. Com 3 jogadores ou menos, o resultado "2" alcança a distância 1.
- **Vitória:**
  - Time do Xerife: quando todos os Foras da lei e Renegados morrem.
  - Foras da lei: quando o Xerife morre, exceto se o Renegado for o único vivo.
  - Renegado: quando é o último vivo.
  - Quem morre revela o papel.

## Diagnóstico atual

### Backend

1. **O bot não joga dados.** Em `GameService.execute_bot_turn`, o número de tiros vem da vida do bot (`bullet_total=current.bullet`). Todos os jogadores vivos ficam na distância 1, e a distância 2 é sempre `None`. Não há rolagem, nova rolagem, Gatling, Cerveja, Flechas nem Dinamite.
2. **O Renegado nunca vence.** `_resolve_winner` dá vitória aos Foras da lei quando o Xerife morre, mesmo que sobre só o Renegado.
3. **As notas de vida estão na escala errada.** `ShotPolicyService` usa `(3 - vida) / 3`, mas os personagens começam com 8 de vida (o Xerife com 10). O treino sintético (`app/training.py`) também gera vidas de 0 a 3.
4. **A rede neural não aprende estratégia.** Os rótulos do treino sintético são "escolha o alvo com menos vida e menos flechas". A rede só imita uma regra simples e não recebe as probabilidades de identidade.
5. **Lacunas na crença:**
   - O papel revelado na morte não é aproveitado.
   - Cerveja nunca é registrada no histórico, então a atualização de crença por cerveja nunca acontece.
   - O histórico guarda a identidade **real** de quem age e de quem é alvo. Hoje só é lido para achar o Xerife, mas seria fácil a IA "trapacear" sem querer.
6. **Estratégia do Renegado:** ele tem peso positivo (0,6) para atirar no Xerife. Na prática, o Renegado costuma proteger o Xerife até ser o último contra ele.
7. **O índice do jogador da vez sai errado depois de uma morte.** Mortos são removidos da lista (`state.players = [... if is_alive]`) antes de avançar `current_player_index`. Se morre alguém sentado antes do jogador atual, o próximo é pulado.
8. **O backend confia no cliente.**
   - O limite de 3 rolagens existe só no front.
   - `RollDiceCommandDTO` recebe os dados travados **com a face**, então o cliente pode mandar a face que quiser.
   - `execute_shots` não confere se a quantidade de tiros bate com os dados, se o alvo está na distância certa, nem se quem atira é o jogador da vez. `finish_turn` também não confere quem pediu.
9. O estado das partidas fica num dicionário em memória (`GameService._games`) e se perde quando o servidor reinicia. Aceitável por enquanto.
10. O pacote `backend/ai/` é um protótipo que não está ligado à API e tem partes quebradas: `ai/trainer.py` importa uma função `encode_state` que não existe, e ainda usa o nome "vice" em vez de Assistente.

### Front (`mobile-gun-firing`)

1. **O turno do bot é executado duas vezes.** Quando o modal de tiro abre num turno de bot, dois efeitos chamam `executeBotTurn` ao mesmo tempo:
   - `src/components/dices/index.tsx`, no efeito que depende de `openModal`;
   - `src/components/shotComponent/index.tsx`, no efeito que depende de `isVisible`.

   O bot pode atirar duas vezes e o turno pode pular um jogador.
2. **As rolagens do bot são de enfeite.** O front rola os dados do bot com `sleep` e efeitos encadeados, mas o backend ignora esses dados.
3. **Não existe distância de verdade.** Todos os vivos aparecem como alvos tanto na distância 1 quanto na 2. Os jogadores aparecem numa `FlatList` simples, mesmo já existindo o componente `circularList`.
4. **Faltam mecânicas:** Flechas e ataque indígena, Cerveja, Gatling, 3 Dinamites, e o papel revelado de quem morreu.
5. **Código obsoleto:** `src/game/*`, `executeDicesComponent` e `src/dtos/dice.ts`. O `DICES` antigo usa um mapeamento de faces diferente do backend.

## Plano

### Fase 1: motor de regras no backend

Criar `backend/app/engine/` em Python puro, sem FastAPI e sem banco, e totalmente testável.

- **Estado e assentos:**
  - Jogadores mortos continuam na lista com `is_alive=False`, o que corrige o bug do índice do jogador da vez.
  - As distâncias são calculadas pelo círculo, ignorando os mortos.
  - Com 3 jogadores ou menos, o resultado "2" passa a alcançar a distância 1.
- **Setup:**
  - Papéis por número de jogadores, de 3 a 8, embaralhados.
  - Vida do personagem, com +2 para o Xerife, e vida máxima respeitada.
  - Mapeamento de faces num único enum.
- **O turno como uma sequência de fases:** `ROLANDO` → `RESOLVENDO` → `FIM`.
  - O servidor guarda as rolagens restantes.
  - Flechas são resolvidas na hora em que saem e podem disparar o ataque indígena.
  - Dinamite fica travada, e 3 delas tiram 1 de vida e encerram as rolagens.
  - Na resolução: 1s e 2s nos alvos válidos, Cervejas, e Gatling com 3 ou mais.
- **Morte e vitória:**
  - Quem morre revela o papel.
  - Regras de vitória completas, incluindo o Renegado vencendo quando é o último vivo.
- **Registro de eventos tipados** (`DADO_ROLADO`, `FLECHA`, `ATAQUE_INDIGENA`, `TIRO`, `CERVEJA`, `GATLING`, `MORTE`, `VITORIA`…). Ele serve ao mesmo tempo para animar o front e para alimentar a crença da IA.

### Fase 2: API autoritativa

- `POST /games/{id}/roll` recebe só `{reroll_indexes}`, e o servidor valida tudo.
- `POST /games/{id}/resolve` recebe `{assignments: [{dice_index, target}]}`, e o servidor valida alcance e quantidade.
- `POST /games/{id}/finish-turn` confere se quem pediu é o jogador da vez.
- `POST /games/{id}/bots/advance` joga os turnos dos bots até chegar a vez do humano e devolve a **lista de eventos**.
- O estado devolvido traz as ações permitidas e os alvos válidos por distância, já calculados. O front deixa de calcular regras.
- Uma camada de "visão por jogador" impede que identidades ocultas vazem na resposta e no histórico entregue à IA.

### Fase 3: front como tela do estado

- Remover toda a orquestração do bot que hoje está no front (os dois efeitos, os `sleep`, o contador local). O front chama `bots/advance` e **anima a lista de eventos**, um por um.
- O humano trava e rola os dados, depois atribui cada dado a um alvo, sempre escolhendo entre os alvos que o backend permite.
- Mostrar a mesa em círculo (`circularList`), flechas e Dinamites, e o papel revelado de quem morreu.
- Apagar o código obsoleto: `src/game/*`, `executeDicesComponent` e `src/dtos/dice.ts`.

### Fase 4: a IA

A IA se divide em duas decisões, com um simulador por trás.

- **Observação sem trapaça:** a IA recebe só a informação pública mais a própria identidade, montada pela camada de visão da Fase 2.
- **Crença bayesiana com restrições** (substitui os ajustes somados de hoje):
  - Considerar todas as distribuições de papéis possíveis entre os jogadores ocultos. Com no máximo 7 ocultos são poucas centenas, então dá para listar todas.
  - Descartar as que contradizem fatos conhecidos: Xerife revelado, papéis revelados na morte e a quantidade de cada papel.
  - Reponderar as que sobram por P(ação observada | papel) a cada evento: tiro, cerveja, em quem cada um mira.
- **Decisão de resolução (alvos dos 1s e 2s, cervejas, gatling):**
  - Calcular a utilidade esperada sobre a crença, ou seja, o quanto aquela jogada aproxima a vitória do meu time.
  - Incluir regras estratégicas por papel. Exemplo: o Renegado protege o Xerife até ser o último contra ele.
- **Decisão de rolar de novo (quais dados manter):** simulação de Monte Carlo.
  - Para cada conjunto de dados que posso manter, simular algumas centenas de rolagens.
  - Avaliar cada resultado com a mesma função de utilidade.
  - Considerar o risco de Dinamite e de Flecha.
- **Explicação e nível de dificuldade:**
  - Retornar o motivo da decisão e a confiança.
  - Nível de dificuldade com escolha softmax e temperatura: um bot "fácil" escolhe com mais aleatoriedade.

### Fase 5: simulador e treino

- Um script roda milhares de partidas bot contra bot usando o mesmo motor e mede a taxa de vitória por papel. Ele também serve para comparar versões da política.
- Trocar o treino sintético atual, que só imita "atire em quem tem menos vida", por dados de self-play.
- Opcional depois: uma rede de valor treinada nesses dados para avaliar as posições na simulação de Monte Carlo, ou aprendizado por reforço.

### Fase 6: testes e limpeza

- Testes do motor: distâncias, flechas, dinamite, gatling, vitórias.
- Testes da crença e da política, com cenários fixos.
- Teste ponta a ponta de uma partida simulada inteira.
- Remover ou arquivar o pacote experimental `backend/ai/`.

### Ordem sugerida

1 → 2 → 4 (heurística + Bayes) → 3 → 5 → 6. As correções do índice do jogador da vez e da vitória do Renegado são pequenas e podem entrar já na Fase 1.

## Conceitos de IA

- **Agente inteligente (perceber → decidir → agir):** o bot recebe uma observação e devolve uma ação, com uma interface única tanto para bots quanto para o simulador.
- **Informação parcial (POMDP):** o bot não vê os papéis ocultos, então decide com base no que acredita, não no estado real.
- **Inferência bayesiana:** combina o que se sabia antes com a probabilidade da ação observada e gera a crença atualizada. Junto com **restrições** (quantos papéis de cada tipo existem, quem já foi revelado), ela elimina o que é impossível.
- **Teoria da utilidade esperada:** cada ação é pontuada pela média do valor dela em cada mundo possível, ponderada pela crença.
- **Simulação de Monte Carlo:** decidir o que rolar de novo simulando muitas rolagens. Uma evolução natural é o **ISMCTS** (MCTS para informação oculta), que sorteia distribuições de papéis compatíveis com a crença e busca a melhor jogada.
- **Função de avaliação heurística:** vida, flechas, distâncias e ameaça ao Xerife resumidas num número, usado pela simulação.
- **Self-play e aprendizado supervisionado:** gerar partidas e treinar uma rede para prever o valor das posições.
- **Aprendizado por reforço (opcional, depois):** recompensa por vitória do time, com REINFORCE ou PPO.
- **Exploração vs. aproveitamento (softmax/temperatura):** controla a dificuldade e evita que o bot jogue sempre igual.
- **IA explicável:** cada decisão vem com motivo e confiança, o que ajuda a depurar e cobre itens do `TODO`.

Recomendação: **heurística + Bayes + Monte Carlo** primeiro. Isso já faz o bot jogar bem e rápido, sem depender de treino. Aprendizado por reforço só vale depois que o motor e o simulador estiverem sólidos.
