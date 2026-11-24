# Pessoa 3 — Dados e estatísticas

**Antes de começar:** espere o push da Pessoa 2 e rode `git pull origin main`.

Copie os arquivos desta pasta para dentro do seu clone do repositório, mantendo as subpastas (ex.: `src/motor_inferencia.py` vai dentro de `src/`).
Antes, configure no git o seu nome e o e-mail da sua conta do GitHub (veja o GUIA_GITHUB.md).

## Commits (um por item, nesta ordem)

```bash
git pull --rebase origin main
git add scripts/gerar_historico.py data/historico_atendimentos.csv
git commit -m "feat: gera historico ficticio de atendimentos"
git add src/estatisticas.py
git commit -m "feat: estatisticas do historico (ranking, ticket medio, popularidade)"
git add tests/test_estatisticas.py
git commit -m "test: testes das estatisticas"
git push origin main
```

## Para o vídeo: você precisa saber explicar

- De onde vêm os dados (histórico fictício gerado com semente fixa) e o que cada função de `estatisticas.py` calcula.
- Como a popularidade entra no sistema: critério de desempate entre recomendações com a mesma certeza.
- Como o CSV é lido e validado (colunas obrigatórias, linhas inválidas ignoradas, arquivo ausente).
- Por que esse recurso aproxima o trabalho do eixo de Ciência de Dados da disciplina.

Além da sua parte, leia o código dos colegas: o professor pode pedir que você explique qualquer trecho do projeto.

## Testar sua parte

```bash
python -m pytest tests/test_estatisticas.py
```
