"""Estatísticas simples do histórico de atendimentos (apoio à decisão).

Usa apenas a biblioteca padrão. O histórico é fictício e fica em
data/historico_atendimentos.csv (colunas: data, servico_id, valor_pago, avaliacao).
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

ARQUIVO_PADRAO = Path(__file__).resolve().parent.parent / "data" / "historico_atendimentos.csv"
COLUNAS = {"data", "servico_id", "valor_pago", "avaliacao"}


class ErroHistorico(Exception):
    """Problema ao ler o histórico de atendimentos."""


def carregar_historico(caminho=ARQUIVO_PADRAO):
    """Lê o CSV e devolve lista de dicts com tipos convertidos.
    Linhas com valores inválidos são ignoradas."""
    try:
        with open(caminho, newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            if not leitor.fieldnames or not COLUNAS.issubset(leitor.fieldnames):
                raise ErroHistorico(f"O CSV precisa ter as colunas: {sorted(COLUNAS)}")
            historico = []
            for linha in leitor:
                try:
                    historico.append({
                        "data": linha["data"],
                        "servico_id": linha["servico_id"],
                        "valor_pago": float(linha["valor_pago"]),
                        "avaliacao": int(linha["avaliacao"]),
                    })
                except (ValueError, TypeError):
                    continue
            return historico
    except FileNotFoundError as erro:
        raise ErroHistorico(f"Arquivo de histórico não encontrado: {caminho}") from erro


def ranking_servicos(historico):
    """[(servico_id, quantidade)] do mais ao menos procurado."""
    return Counter(item["servico_id"] for item in historico).most_common()


def popularidade(historico):
    """{servico_id: fração dos atendimentos}. Usada como critério de desempate."""
    total = len(historico)
    if total == 0:
        return {}
    return {sid: qtd / total for sid, qtd in ranking_servicos(historico)}


def ticket_medio(historico):
    if not historico:
        return 0.0
    return sum(item["valor_pago"] for item in historico) / len(historico)


def receita_por_servico(historico):
    receita = defaultdict(float)
    for item in historico:
        receita[item["servico_id"]] += item["valor_pago"]
    return dict(sorted(receita.items(), key=lambda par: par[1], reverse=True))


def avaliacao_media_por_servico(historico):
    notas = defaultdict(list)
    for item in historico:
        notas[item["servico_id"]].append(item["avaliacao"])
    return {sid: sum(n) / len(n) for sid, n in notas.items()}
