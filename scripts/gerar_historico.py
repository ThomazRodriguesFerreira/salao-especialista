"""Gera um histórico FICTÍCIO de atendimentos do Salão Aurora (data/historico_atendimentos.csv).

Uso: python scripts/gerar_historico.py
A semente fixa garante que o arquivo gerado seja sempre o mesmo.
"""
import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# permite rodar o script direto da raiz do projeto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.base_conhecimento import carregar_servicos  # noqa: E402

# peso = quão procurado é o serviço (valores inventados para a simulação)
PESOS = {
    "corte": 18, "escova": 16, "hidratacao": 14, "manicure": 15, "pedicure": 9,
    "coloracao": 8, "esmaltacao_gel": 7, "reconstrucao_capilar": 5, "tonalizacao": 4,
    "mechas_luzes": 3, "progressiva": 3, "botox_capilar": 4,
    "tratamento_couro_cabeludo": 3, "penteado_festa": 5, "maquiagem_social": 3,
}
TOTAL_ATENDIMENTOS = 150


def gerar(destino):
    aleatorio = random.Random(2026)
    servicos = carregar_servicos()
    ids = list(PESOS)
    inicio = date(2026, 5, 1)
    linhas = []
    for _ in range(TOTAL_ATENDIMENTOS):
        servico_id = aleatorio.choices(ids, weights=[PESOS[i] for i in ids])[0]
        preco = servicos[servico_id]["preco"]
        desconto = 0.9 if aleatorio.random() < 0.15 else 1.0
        dia = inicio + timedelta(days=aleatorio.randint(0, 180))
        nota = aleatorio.choices([3, 4, 5], weights=[1, 3, 6])[0]
        linhas.append((dia.isoformat(), servico_id, round(preco * desconto, 2), nota))
    linhas.sort()
    with open(destino, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(["data", "servico_id", "valor_pago", "avaliacao"])
        escritor.writerows(linhas)


if __name__ == "__main__":
    destino = Path(__file__).resolve().parent.parent / "data" / "historico_atendimentos.csv"
    gerar(destino)
    print(f"Histórico gerado em {destino}")
