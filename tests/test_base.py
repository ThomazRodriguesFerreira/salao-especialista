import json

import pytest

from src.base_conhecimento import (ErroBaseConhecimento, RespostaInvalida,
                                   carregar_base, deve_perguntar, validar_base,
                                   validar_respostas)


@pytest.fixture(scope="module")
def base():
    return carregar_base()


def test_base_tem_volume_minimo(base):
    assert len(base["regras"]) >= 20
    assert len(base["servicos"]) >= 10


def test_ids_de_regras_sao_unicos(base):
    ids = [r["id"] for r in base["regras"]]
    assert len(ids) == len(set(ids))


def test_validar_base_detecta_servico_inexistente(base):
    regras = [{"id": "RX", "descricao": "teste", "se": [["objetivo", "=", "cortar"]],
               "entao": ["recomendacao", "servico_fantasma"], "cf": 0.5}]
    with pytest.raises(ErroBaseConhecimento, match="serviço inexistente"):
        validar_base(base["servicos"], base["perguntas"], regras, base["alertas"])


def test_validar_base_detecta_valor_inexistente_na_pergunta(base):
    regras = [{"id": "RX", "descricao": "teste", "se": [["objetivo", "=", "voar"]],
               "entao": ["recomendacao", "corte"], "cf": 0.5}]
    with pytest.raises(ErroBaseConhecimento, match="não existe na pergunta"):
        validar_base(base["servicos"], base["perguntas"], regras, base["alertas"])


def test_validar_base_detecta_cf_invalido(base):
    regras = [{"id": "RX", "descricao": "teste", "se": [["objetivo", "=", "cortar"]],
               "entao": ["recomendacao", "corte"], "cf": 1.5}]
    with pytest.raises(ErroBaseConhecimento, match="cf"):
        validar_base(base["servicos"], base["perguntas"], regras, base["alertas"])


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroBaseConhecimento, match="não encontrado"):
        carregar_base(tmp_path)


def test_json_invalido(tmp_path):
    (tmp_path / "servicos.json").write_text("{quebrado", encoding="utf-8")
    with pytest.raises(ErroBaseConhecimento, match="JSON inválido"):
        carregar_base(tmp_path)


def test_deve_perguntar(base):
    cor = next(p for p in base["perguntas"] if p["id"] == "cor_atual")
    assert deve_perguntar(cor, {"objetivo": "mudar_cor"})
    assert not deve_perguntar(cor, {"objetivo": "cortar"})
    assert not deve_perguntar(cor, {})


def test_validar_respostas_ok(base):
    assert validar_respostas({"objetivo": "cortar"}, base["perguntas"]) == {"objetivo": "cortar"}


@pytest.mark.parametrize("respostas", [
    {},                                    # sem objetivo
    {"objetivo": "voar"},                  # valor inválido
    {"objetivo": "cortar", "banana": "x"}, # pergunta desconhecida
    "texto",                               # tipo errado
])
def test_validar_respostas_invalidas(base, respostas):
    with pytest.raises(RespostaInvalida):
        validar_respostas(respostas, base["perguntas"])
