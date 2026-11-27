# Documentação técnica — Consultor do Salão Aurora

## 1. Contexto de negócio

**Empresa simulada:** Salão Aurora, salão de beleza (prestação de serviços) com serviços de cabelo, unhas, maquiagem e penteados para eventos.

**Problema de negócio:** a recepção do salão perde tempo fazendo triagem. Muitas clientes chegam sem saber qual serviço escolher, e a escolha errada gera risco (química em cabelo fragilizado, tintura em quem tem alergia) e insatisfação. O sistema especialista faz a triagem inicial: pergunta sobre objetivo, estado do cabelo, histórico químico, alergias, orçamento e tempo, e recomenda serviços com um **grau de certeza**, avisos de segurança e **explicação do raciocínio**.

## 2. Por que Python

- A disciplina tem um eixo em Python e Ciência de Dados. Com Python, o motor de inferência, as estatísticas do histórico de atendimentos e a interface ficam na mesma linguagem.
- Implementamos o motor de encadeamento por conta própria (sem biblioteca pronta), o que deixa explícito como funcionam a base de fatos, as regras, o encadeamento e a explicação.
- A base de conhecimento fica em arquivos JSON, e o salão pode atualizar serviços, preços e regras sem mexer no código.
- Dá para ter console, interface web (Streamlit) e testes automatizados (pytest) sem instalar nada além do Python. O núcleo usa apenas a biblioteca padrão.
- Não escolhemos Prolog nem a solução híbrida para evitar dependências externas (SWI-Prolog, pyswip) que dificultam rodar o projeto em outra máquina.

## 3. Arquitetura

| Arquivo | Função |
|---|---|
| `data/servicos.json` | Catálogo de serviços (preço, duração, profissional) |
| `data/perguntas.json` | Perguntas, opções e condição para serem feitas |
| `data/regras.json` | Regras (38) e textos de alertas |
| `data/historico_atendimentos.csv` | Histórico fictício para estatísticas |
| `src/base_conhecimento.py` | Carrega e valida a base; valida respostas do usuário |
| `src/motor_inferencia.py` | Motor: encadeamento para frente, fatores de certeza, árvore para trás |
| `src/recomendador.py` | Regras de negócio: ordena, checa orçamento/tempo, alertas, "sem conclusão" |
| `src/explicacao.py` | Explicações "por que pergunto", "como" e "por que não" |
| `src/estatisticas.py` | Estatísticas do histórico (desempate por popularidade) |
| `src/interface_console.py`, `main.py` | Interface de terminal |
| `app_streamlit.py` | Interface gráfica web |

## 4. Base de conhecimento

### 4.1 Fatos informados pela cliente (atributos)

| Atributo | Valores |
|---|---|
| objetivo | mudar_cor, alisar, reduzir_volume, hidratar, cortar, evento, couro_cabeludo, unhas |
| tipo_cabelo | liso, ondulado, cacheado, crespo |
| estado_cabelo | saudavel, ressecado, quebradico, danificado |
| quimica_recente | sim, nao |
| cor_atual | natural, colorido, descolorido |
| cor_desejada | mais_claro, mais_escuro |
| alergia_tintura | sim, nao, nao_sei |
| couro_cabeludo | normal, oleoso, seco, caspa, sensivel |
| gestante | sim, nao |
| orcamento | baixo (até R$ 100), medio (até R$ 250), alto |
| tempo | curto (até 1h30), medio (até 3h), longo |

Nem todas as perguntas são feitas: `perguntar_se` em `perguntas.json` esconde as que não se aplicam (ex.: cor atual só aparece se o objetivo for mudar a cor).

### 4.2 Fatos derivados (conclusões intermediárias)

`restricao_quimica`, `cabelo_fragilizado`, `necessita_teste_alergia`, `contraindicado_tintura`, `precisa_descoloracao`.

### 4.3 Conclusões finais

`recomendacao = <id do serviço>` e `alerta = <id do alerta>`.

### 4.4 Regras

Operadores: `=` (fato existe), `em` (algum valor da lista), `nao` (o fato não existe, negação por falha) e `nao_em`.

| Regra | Descrição | Se | Então | CF |
|---|---|---|---|---|
| R01 | Química recente exige cautela com novos procedimentos químicos | quimica_recente = sim | restricao_quimica = sim | 0.9 |
| R02 | Cabelo muito danificado não deve receber química | estado_cabelo = danificado | restricao_quimica = sim | 1.0 |
| R03 | Cabelo quebradiço sugere evitar química | estado_cabelo = quebradico | restricao_quimica = sim | 0.8 |
| R04 | Gestação restringe procedimentos químicos | gestante = sim | restricao_quimica = sim | 1.0 |
| R05 | Cabelo danificado ou quebradiço está fragilizado | estado_cabelo é um de [danificado, quebradico] | cabelo_fragilizado = sim | 0.95 |
| R06 | Cabelo ressecado com química recente tende a estar fragilizado | estado_cabelo = ressecado E quimica_recente = sim | cabelo_fragilizado = sim | 0.7 |
| R07 | Quem não sabe se tem alergia precisa de teste antes da coloração | alergia_tintura = nao_sei E objetivo = mudar_cor | necessita_teste_alergia = sim | 1.0 |
| R08 | Couro cabeludo sensível pede teste antes de coloração ou alisamento | couro_cabeludo = sensivel E objetivo é um de [mudar_cor, alisar] | necessita_teste_alergia = sim | 0.8 |
| R09 | Alergia declarada contraindica tintura | alergia_tintura = sim | contraindicado_tintura = sim | 1.0 |
| R10 | Clarear cabelo natural ou pintado exige descoloração | objetivo = mudar_cor E cor_desejada = mais_claro E cor_atual é um de [natural, colorido] | precisa_descoloracao = sim | 0.9 |
| R11 | Escurecer o cabelo sem restrições: coloração | objetivo = mudar_cor E cor_desejada = mais_escuro E NÃO existe o fato (contraindicado_tintura = sim) E NÃO existe o fato (restricao_quimica = sim) | recomendacao = coloracao | 0.9 |
| R12 | Clarear sem restrições: mechas ou luzes | objetivo = mudar_cor E precisa_descoloracao = sim E NÃO existe o fato (contraindicado_tintura = sim) E NÃO existe o fato (restricao_quimica = sim) | recomendacao = mechas_luzes | 0.85 |
| R13 | Mudar a cor com restrição química: tonalização suave | objetivo = mudar_cor E restricao_quimica = sim E NÃO existe o fato (contraindicado_tintura = sim) | recomendacao = tonalizacao | 0.7 |
| R14 | Cabelo descolorido que vai escurecer: tonalização | objetivo = mudar_cor E cor_atual = descolorido E cor_desejada = mais_escuro | recomendacao = tonalizacao | 0.6 |
| R15 | Quem precisa de teste de alergia deve fazê-lo primeiro | necessita_teste_alergia = sim | recomendacao = teste_alergia | 1.0 |
| R16 | Alerta de alergia para quem quer mudar a cor | objetivo = mudar_cor E contraindicado_tintura = sim | alerta = alergia_tintura | 1.0 |
| R17 | Alerta de pausa química para coloração ou alisamento | objetivo é um de [mudar_cor, alisar] E restricao_quimica = sim | alerta = pausa_quimica | 0.9 |
| R18 | Alerta de gestação para coloração ou alisamento | objetivo é um de [mudar_cor, alisar] E gestante = sim | alerta = gestacao | 1.0 |
| R19 | Alisar cabelo com textura e sem restrição: progressiva | objetivo = alisar E tipo_cabelo é um de [ondulado, cacheado, crespo] E NÃO existe o fato (restricao_quimica = sim) | recomendacao = progressiva | 0.85 |
| R20 | Alisar com restrição química: botox capilar | objetivo = alisar E restricao_quimica = sim | recomendacao = botox_capilar | 0.7 |
| R21 | Cabelo já liso: escova resolve | objetivo = alisar E tipo_cabelo = liso | recomendacao = escova | 0.85 |
| R22 | Reduzir volume em cabelo com textura: botox capilar | objetivo = reduzir_volume E tipo_cabelo é um de [ondulado, cacheado, crespo] | recomendacao = botox_capilar | 0.8 |
| R23 | Reduzir volume com orçamento baixo: hidratação | objetivo = reduzir_volume E orcamento = baixo | recomendacao = hidratacao | 0.6 |
| R24 | Hidratar cabelo ressecado: hidratação profunda | objetivo = hidratar E estado_cabelo = ressecado | recomendacao = hidratacao | 0.9 |
| R25 | Manutenção de cabelo saudável: hidratação | objetivo = hidratar E estado_cabelo = saudavel | recomendacao = hidratacao | 0.6 |
| R26 | Cabelo cacheado ou crespo ressecado precisa de hidratação | estado_cabelo = ressecado E tipo_cabelo é um de [cacheado, crespo] | recomendacao = hidratacao | 0.8 |
| R27 | Cabelo fragilizado: reconstrução capilar | cabelo_fragilizado = sim | recomendacao = reconstrucao_capilar | 0.9 |
| R28 | Quem quer cortar: corte de cabelo | objetivo = cortar | recomendacao = corte | 0.9 |
| R29 | Corte em cabelo quebradiço ou danificado: reconstrução | objetivo = cortar E estado_cabelo é um de [quebradico, danificado] | recomendacao = reconstrucao_capilar | 0.7 |
| R30 | Caspa ou oleosidade: tratamento do couro cabeludo | couro_cabeludo é um de [caspa, oleoso] | recomendacao = tratamento_couro_cabeludo | 0.85 |
| R31 | Objetivo de cuidar do couro cabeludo | objetivo = couro_cabeludo | recomendacao = tratamento_couro_cabeludo | 0.7 |
| R32 | Alerta para caspa persistente | couro_cabeludo = caspa | alerta = caspa | 0.8 |
| R33 | Evento: penteado para festa | objetivo = evento | recomendacao = penteado_festa | 0.9 |
| R34 | Evento com tempo disponível: maquiagem social | objetivo = evento E tempo é um de [medio, longo] | recomendacao = maquiagem_social | 0.7 |
| R35 | Evento com pouco tempo: escova rápida | objetivo = evento E tempo = curto | recomendacao = escova | 0.7 |
| R36 | Cuidar das unhas: manicure | objetivo = unhas | recomendacao = manicure | 0.9 |
| R37 | Unhas com orçamento médio ou alto: pedicure | objetivo = unhas E orcamento é um de [medio, alto] | recomendacao = pedicure | 0.6 |
| R38 | Unhas com tempo e orçamento: esmaltação em gel | objetivo = unhas E tempo é um de [medio, longo] E orcamento é um de [medio, alto] | recomendacao = esmaltacao_gel | 0.8 |

## 5. Motor de inferência

### 5.1 Encadeamento para frente
A memória de trabalho guarda `{atributo: {valor: CF}}`. A cada rodada, o motor avalia todas as regras contra a memória (fatos da cliente + fatos derivados na rodada anterior). Regras cujas premissas são verdadeiras disparam e geram fatos novos. O processo repete até os fatos derivados pararem de mudar (estabilização). Exemplo: R10 deriva `precisa_descoloracao`, que na rodada seguinte permite disparar R12.

### 5.2 Fatores de certeza
- Fatos informados pela cliente têm CF 1,0.
- Ao disparar, `CF da conclusão = CF da regra × menor CF entre as premissas`.
- Se mais de uma regra conclui o mesmo fato, os CFs são combinados: `CF = a + b × (1 − a)`. Exemplo: R24 (0,9) e R26 (0,8) para hidratação geram 0,98.
- Fatos com CF abaixo de 0,2 são descartados; recomendações com CF abaixo de 0,3 não são exibidas.

### 5.3 Encadeamento para trás
`arvore_objetivo` parte de um objetivo (ex.: `recomendacao = progressiva`), busca as regras que o concluem e verifica cada premissa, descendo recursivamente nas premissas que também são conclusões de outras regras. É usado para responder "por que não".

## 6. Módulo de explicação

- **Por que pergunto isso?** Lista as regras da base que usam a resposta, inclusive indiretamente por fatos derivados.
- **Como?** Mostra a cadeia de regras e fatos que levou à recomendação, com os CFs. É montado a partir dos disparos da rodada final.
- **Por que não?** Para um serviço não recomendado, mostra cada regra que poderia concluí-lo e quais condições falharam (✓ / ✗).

## 7. Casos de exceção

- **Sem conclusão:** se nenhuma recomendação passa do CF mínimo, o sistema diz "Não foi possível concluir com as informações fornecidas" e sugere a avaliação presencial gratuita.
- **Entradas inválidas:** no console, opções fora do intervalo são recusadas e a pergunta se repete. O motor rejeita respostas desconhecidas com `RespostaInvalida`.
- **Base com erro:** `validar_base` detecta serviço inexistente, CF fora de 0 a 1, valores que não existem nas perguntas e ids duplicados.
- **Arquivos ausentes ou corrompidos:** geram mensagens claras (`ErroBaseConhecimento`, `ErroHistorico`).

## 8. Recursos adicionais implementados

Interface gráfica web (Streamlit), tratamento de incerteza (fatores de certeza), base extensível em JSON, estatísticas do histórico, testes automatizados e esta documentação.

## 9. Como executar

```bash
python main.py                      # versão de terminal
pip install -r requirements.txt
streamlit run app_streamlit.py      # interface gráfica
python -m pytest                    # testes
```

## 10. Limitações

- O sistema é um protótipo de triagem. As regras foram escritas pelo grupo para a simulação e não substituem a avaliação de uma profissional nem orientação médica.
- O histórico de atendimentos é fictício (gerado por `scripts/gerar_historico.py`).
