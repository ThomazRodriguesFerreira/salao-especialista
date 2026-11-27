from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

CAMINHO_APP = str(Path(__file__).resolve().parent.parent / "app_streamlit.py")


def _app():
    return AppTest.from_file(CAMINHO_APP, default_timeout=30).run()


def test_app_abre_sem_erros():
    at = _app()
    assert not at.exception
    assert [s.key for s in at.selectbox][0] == "p_objetivo"


def test_perguntas_condicionais_aparecem_conforme_objetivo():
    at = _app()
    at.selectbox(key="p_objetivo").select("unhas").run()
    chaves = [s.key for s in at.selectbox]
    assert "p_tipo_cabelo" not in chaves and "p_orcamento" in chaves


def test_consulta_completa_mostra_recomendacoes():
    at = _app()
    at.selectbox(key="p_objetivo").select("unhas").run()
    at.selectbox(key="p_orcamento").select("medio").run()
    at.selectbox(key="p_tempo").select("medio").run()
    at.button[0].click().run()
    assert not at.exception
    assert "Manicure" in [s.value for s in at.subheader]


def test_botao_sem_responder_mostra_erro():
    at = _app()
    at.selectbox(key="p_objetivo").select("unhas").run()
    at.button[0].click().run()
    assert at.error
