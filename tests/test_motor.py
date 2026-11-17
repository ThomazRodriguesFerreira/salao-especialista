import pytest

from src.base_conhecimento import RespostaInvalida
from src.motor_inferencia import MotorInferencia
from src.recomendador import SalaoEspecialista


@pytest.fixture(scope="module")
def salao():
    return SalaoEspecialista.padrao()


def ids(consulta):
    return [r.servico["id"] for r in consulta.recomendacoes]


def test_combinar_cf():
    assert MotorInferencia.combinar_cf(0.9, 0.8) == pytest.approx(0.98)
    assert MotorInferencia.combinar_cf(0.0, 0.5) == pytest.approx(0.5)


def test_clarear_cabelo_natural_recomenda_mechas(salao):
    c = salao.consultar({"objetivo": "mudar_cor", "tipo_cabelo": "liso", "estado_cabelo": "saudavel",
                         "quimica_recente": "nao", "cor_atual": "natural", "cor_desejada": "mais_claro",
                         "alergia_tintura": "nao", "couro_cabeludo": "normal", "gestante": "nao",
                         "orcamento": "alto", "tempo": "longo"})
    assert ids(c) == ["mechas_luzes"]
    assert c.recomendacoes[0].cf == pytest.approx(0.765)
    assert c.conclusivo


def test_alergia_bloqueia_coloracao_e_gera_alerta(salao):
    c = salao.consultar({"objetivo": "mudar_cor", "tipo_cabelo": "liso", "estado_cabelo": "saudavel",
                         "quimica_recente": "nao", "cor_atual": "natural", "cor_desejada": "mais_escuro",
                         "alergia_tintura": "sim", "couro_cabeludo": "normal", "gestante": "nao",
                         "orcamento": "medio", "tempo": "longo"})
    assert "coloracao" not in ids(c)
    assert [a[0] for a in c.alertas] == ["alergia_tintura"]


def test_nao_sei_se_tem_alergia_pede_teste_antes(salao):
    c = salao.consultar({"objetivo": "mudar_cor", "tipo_cabelo": "liso", "estado_cabelo": "saudavel",
                         "quimica_recente": "nao", "cor_atual": "natural", "cor_desejada": "mais_escuro",
                         "alergia_tintura": "nao_sei", "couro_cabeludo": "normal", "gestante": "nao",
                         "orcamento": "medio", "tempo": "longo"})
    assert ids(c)[0] == "teste_alergia"
    assert "coloracao" in ids(c)


def test_quimica_recente_bloqueia_progressiva(salao):
    c = salao.consultar({"objetivo": "alisar", "tipo_cabelo": "cacheado", "estado_cabelo": "saudavel",
                         "quimica_recente": "sim", "couro_cabeludo": "normal", "gestante": "nao",
                         "orcamento": "alto", "tempo": "longo"})
    assert "progressiva" not in ids(c)
    assert "botox_capilar" in ids(c)
    assert any(a[0] == "pausa_quimica" for a in c.alertas)


def test_gestante_nao_recebe_progressiva_e_ve_alerta(salao):
    c = salao.consultar({"objetivo": "alisar", "tipo_cabelo": "crespo", "estado_cabelo": "saudavel",
                         "quimica_recente": "nao", "couro_cabeludo": "normal", "gestante": "sim",
                         "orcamento": "alto", "tempo": "longo"})
    assert "progressiva" not in ids(c)
    assert {a[0] for a in c.alertas} >= {"gestacao", "pausa_quimica"}


def test_alisar_sem_restricao_recomenda_progressiva(salao):
    c = salao.consultar({"objetivo": "alisar", "tipo_cabelo": "cacheado", "estado_cabelo": "saudavel",
                         "quimica_recente": "nao", "couro_cabeludo": "normal", "gestante": "nao",
                         "orcamento": "alto", "tempo": "longo"})
    assert ids(c) == ["progressiva"]


def test_regras_diferentes_combinam_certeza(salao):
    # R24 (0.9) e R26 (0.8) apoiam hidratação: 0.9 + 0.8 * 0.1 = 0.98
    c = salao.consultar({"objetivo": "hidratar", "tipo_cabelo": "cacheado", "estado_cabelo": "ressecado",
                         "quimica_recente": "nao", "couro_cabeludo": "normal",
                         "orcamento": "medio", "tempo": "medio"})
    assert c.recomendacoes[0].servico["id"] == "hidratacao"
    assert c.recomendacoes[0].cf == pytest.approx(0.98)


def test_encadeamento_em_varias_rodadas(salao):
    c = salao.consultar({"objetivo": "mudar_cor", "tipo_cabelo": "liso", "estado_cabelo": "saudavel",
                         "quimica_recente": "nao", "cor_atual": "natural", "cor_desejada": "mais_claro",
                         "alergia_tintura": "nao", "couro_cabeludo": "normal", "gestante": "nao",
                         "orcamento": "alto", "tempo": "longo"})
    # R10 deriva precisa_descoloracao, que alimenta R12
    assert c.resultado.cf("precisa_descoloracao", "sim") == pytest.approx(0.9)
    assert c.resultado.rodadas >= 2


def test_sem_conclusao_usa_avaliacao_presencial(salao):
    c = salao.consultar({"objetivo": "reduzir_volume", "tipo_cabelo": "liso", "estado_cabelo": "saudavel",
                         "quimica_recente": "nao", "couro_cabeludo": "normal", "gestante": "nao",
                         "orcamento": "alto", "tempo": "curto"})
    assert not c.conclusivo
    assert ids(c) == ["avaliacao_presencial"]


def test_servico_fora_do_orcamento_e_do_tempo_e_sinalizado(salao):
    c = salao.consultar({"objetivo": "mudar_cor", "tipo_cabelo": "liso", "estado_cabelo": "saudavel",
                         "quimica_recente": "nao", "cor_atual": "natural", "cor_desejada": "mais_claro",
                         "alergia_tintura": "nao", "couro_cabeludo": "normal", "gestante": "nao",
                         "orcamento": "baixo", "tempo": "curto"})
    rec = c.recomendacoes[0]
    assert not rec.cabe_orcamento and not rec.cabe_tempo


def test_popularidade_desempata_certezas_iguais():
    # R36 (manicure 0.9) e demais: usamos evento com tempo médio -> penteado 0.9 > maquiagem 0.7
    base_salao = SalaoEspecialista.padrao(popularidade={"manicure": 0.5, "pedicure": 0.1})
    c = base_salao.consultar({"objetivo": "unhas", "orcamento": "medio", "tempo": "curto"})
    assert ids(c) == ["manicure", "pedicure"]


def test_entradas_invalidas_sao_rejeitadas(salao):
    with pytest.raises(RespostaInvalida):
        salao.consultar({"objetivo": "voar"})
    with pytest.raises(RespostaInvalida):
        salao.consultar({})


def test_motor_estabiliza_para_qualquer_objetivo(salao):
    for objetivo in ("mudar_cor", "alisar", "reduzir_volume", "hidratar", "cortar",
                     "evento", "couro_cabeludo", "unhas"):
        salao.consultar({"objetivo": objetivo})  # não deve levantar RuntimeError
