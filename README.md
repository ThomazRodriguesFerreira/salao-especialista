# Consultor do Salão Aurora — Sistema Especialista em Python

Protótipo de sistema especialista para um **salão de beleza** (prestação de serviços). Ele faz a triagem da cliente por perguntas e respostas e recomenda serviços com grau de certeza, avisos de segurança e explicação do raciocínio.

Trabalho da disciplina Programação de Sistemas Especialistas, Universidade Veiga de Almeida.

**Integrantes:** Thomaz Rodrigues Ferreira, Thiago Antunes Da Silva Guimarães, Luiz Felipe Marques Espindola, João Vitor Bitencourt Rodrigues e Caio Rocha Da Silva.

## Como rodar

Requer Python 3.10 ou superior.

```bash
git clone <URL-DO-REPOSITORIO>
cd salao-especialista
python main.py                      # terminal, sem instalar nada
```

Interface gráfica (opcional):

```bash
pip install -r requirements.txt
streamlit run app_streamlit.py
```

Testes:

```bash
pip install -r requirements.txt
python -m pytest
```

## O que o sistema tem

- Base de conhecimento com 38 regras e 17 serviços, em JSON (`data/`)
- Motor de inferência com encadeamento para frente e para trás
- Fatores de certeza para lidar com informações incertas
- Explicações "por que pergunto", "como" e "por que não"
- Tratamento de entradas inválidas e de casos sem conclusão
- Interface de terminal e interface gráfica web
- Estatísticas de um histórico fictício de atendimentos
- Testes automatizados

A documentação técnica completa está em [`docs/DOCUMENTACAO.md`](docs/DOCUMENTACAO.md).
