import pytest

from src.explicacao import (como, descrever_condicao, formatar_duracao,
                            formatar_preco, formatar_resultado, montar_rotulos,
                            nivel_certeza, por_que_nao, por_que_perguntar)
from src.recomendador import SalaoEspecialista


@pytest.fixture(scope="module")
def salao():
    return SalaoEspecialista.padrao()


@pytest.fixture(scope="module")
def rotulos(salao):
    return montar_rotulos(salao.perguntas)


@pytest.fixture(scope="module")
def consulta_clarear(salao):
    return salao.consultar({"objetivo": "mudar_cor", "tipo_cabelo": "liso", "estado_cabelo": "saudavel",
                            "quimica_recente": "nao", "cor_atual": "natural", "cor_desejada": "mais_claro",
                            "alergia_tintura": "nao", "couro_cabeludo": "normal", "gestante": "nao",
                            "orcamento": "alto", "tempo": "longo"})


def test_formatacao():
    assert formatar_preco(0) == "Grátis"
    assert formatar_preco(80) == "R$ 80,00"
    assert formatar_duracao(45) == "45 min"
    assert formatar_duracao(60) == "1h"
    assert formatar_duracao(150) == "2h30"
    assert nivel_certeza(0.9) == "alta" and nivel_certeza(0.55) == "média" and nivel_certeza(0.3) == "baixa"


def test_descrever_condicao(rotulos):
    assert descrever_condicao(("objetivo", "=", "alisar"), rotulos) == "objetivo = Alisar o cabelo"
    assert "NÃO" in descrever_condicao(("restricao_quimica", "nao", "sim"))


def test_como_mostra_cadeia_de_regras(salao, consulta_clarear, rotulos):
    texto = como(consulta_clarear, ("recomendacao", "mechas_luzes"), rotulos, salao.servicos)
    assert "R12" in texto and "R10" in texto       # regra final e regra intermediária
    assert "informado por você" in texto


def test_como_fato_nao_concluido(consulta_clarear):
    assert "não foi concluído" in como(consulta_clarear, ("recomendacao", "corte"))


def test_por_que_nao_aponta_condicao_que_falhou(salao, consulta_clarear, rotulos):
    texto = por_que_nao(consulta_clarear, "coloracao", salao.motor, salao.servicos, rotulos)
    assert "R11" in texto and "✗" in texto and "Mais escuro" in texto


def test_por_que_nao_para_servico_recomendado(salao, consulta_clarear):
    texto = por_que_nao(consulta_clarear, "mechas_luzes", salao.motor, salao.servicos)
    assert "foi recomendado" in texto


def test_por_que_perguntar_cita_regras(salao):
    texto = por_que_perguntar("quimica_recente", salao.regras)
    assert "R01" in texto
    assert "orçamento" in por_que_perguntar("orcamento", salao.regras)


def test_formatar_resultado_conclusivo(consulta_clarear, rotulos):
    texto = formatar_resultado(consulta_clarear, rotulos)
    assert "Mechas" in texto and "76%" in texto


def test_formatar_resultado_sem_conclusao(salao):
    c = salao.consultar({"objetivo": "reduzir_volume", "tipo_cabelo": "liso", "estado_cabelo": "saudavel",
                         "quimica_recente": "nao", "couro_cabeludo": "normal", "gestante": "nao",
                         "orcamento": "alto", "tempo": "curto"})
    assert "Não foi possível concluir" in formatar_resultado(c)
