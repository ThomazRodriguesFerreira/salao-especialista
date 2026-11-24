import pytest

from src.estatisticas import (ErroHistorico, avaliacao_media_por_servico,
                              carregar_historico, popularidade, ranking_servicos,
                              receita_por_servico, ticket_medio)


@pytest.fixture
def historico():
    return [
        {"data": "2026-05-01", "servico_id": "corte", "valor_pago": 80.0, "avaliacao": 5},
        {"data": "2026-05-02", "servico_id": "corte", "valor_pago": 72.0, "avaliacao": 3},
        {"data": "2026-05-03", "servico_id": "manicure", "valor_pago": 45.0, "avaliacao": 4},
    ]


def test_ranking(historico):
    assert ranking_servicos(historico) == [("corte", 2), ("manicure", 1)]


def test_popularidade_soma_um(historico):
    assert sum(popularidade(historico).values()) == pytest.approx(1.0)


def test_ticket_medio(historico):
    assert ticket_medio(historico) == pytest.approx((80 + 72 + 45) / 3)


def test_receita_e_avaliacao(historico):
    assert receita_por_servico(historico)["corte"] == pytest.approx(152.0)
    assert avaliacao_media_por_servico(historico)["corte"] == pytest.approx(4.0)


def test_historico_vazio():
    assert popularidade([]) == {}
    assert ticket_medio([]) == 0.0


def test_historico_padrao_carrega():
    assert len(carregar_historico()) == 150


def test_linhas_invalidas_sao_ignoradas(tmp_path):
    arquivo = tmp_path / "h.csv"
    arquivo.write_text("data,servico_id,valor_pago,avaliacao\n"
                       "2026-05-01,corte,80,5\n"
                       "2026-05-02,corte,abc,5\n", encoding="utf-8")
    assert len(carregar_historico(arquivo)) == 1


def test_colunas_faltando(tmp_path):
    arquivo = tmp_path / "h.csv"
    arquivo.write_text("data,servico_id\n2026-05-01,corte\n", encoding="utf-8")
    with pytest.raises(ErroHistorico, match="colunas"):
        carregar_historico(arquivo)


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroHistorico, match="não encontrado"):
        carregar_historico(tmp_path / "nao_existe.csv")
