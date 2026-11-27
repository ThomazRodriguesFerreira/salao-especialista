"""Interface gráfica (web) do Salão Aurora.  Execute: streamlit run app_streamlit.py

A interface só coleta as respostas e exibe o resultado: toda a inferência
acontece no motor (src/motor_inferencia.py).
"""
import streamlit as st

from src.base_conhecimento import deve_perguntar
from src.estatisticas import (ErroHistorico, avaliacao_media_por_servico,
                              carregar_historico, popularidade, ranking_servicos,
                              ticket_medio)
from src.explicacao import (como, descrever_condicao, formatar_duracao,
                            formatar_preco, montar_rotulos, nivel_certeza,
                            por_que_nao, por_que_perguntar)
from src.recomendador import SalaoEspecialista

st.set_page_config(page_title="Salão Aurora — Consultor de Serviços", page_icon="✂️")


@st.cache_resource
def carregar_sistema():
    try:
        historico = carregar_historico()
    except ErroHistorico:
        historico = []
    return SalaoEspecialista.padrao(popularidade=popularidade(historico)), historico


salao, historico = carregar_sistema()
rotulos = montar_rotulos(salao.perguntas)

st.title("Salão Aurora")
st.caption("Consultor de serviços: responda às perguntas e veja o que recomendamos para você.")

aba_consulta, aba_regras, aba_dados = st.tabs(["Consulta", "Base de conhecimento", "Estatísticas"])

# ---------------- Consulta ----------------
with aba_consulta:
    respostas = {}
    for pergunta in salao.perguntas:
        if not deve_perguntar(pergunta, respostas):
            continue
        opcoes = [valor for valor, _ in pergunta["opcoes"]]
        escolha = st.selectbox(
            pergunta["texto"], opcoes, index=None, placeholder="Selecione uma opção",
            format_func=lambda v, p=pergunta["id"]: rotulos[(p, v)], key=f"p_{pergunta['id']}")
        with st.expander("Por que estou perguntando isso?"):
            st.write(por_que_perguntar(pergunta["id"], salao.regras))
        if escolha is not None:
            respostas[pergunta["id"]] = escolha

    obrigatorias = [p["id"] for p in salao.perguntas if deve_perguntar(p, respostas)]
    faltando = [p for p in obrigatorias if p not in respostas]
    if st.button("Ver recomendações", type="primary"):
        if faltando:
            st.error("Responda todas as perguntas para continuar.")
        else:
            st.session_state["respostas"] = dict(respostas)

    if "respostas" in st.session_state and not faltando and \
            st.session_state["respostas"] == respostas:
        consulta = salao.consultar(respostas)
        st.divider()
        if not consulta.conclusivo:
            st.warning("Não foi possível concluir com as informações fornecidas. "
                       "Sugerimos uma avaliação presencial gratuita.")
        for rec in consulta.recomendacoes:
            s = rec.servico
            with st.container(border=True):
                st.subheader(s["nome"])
                st.write(s["descricao"])
                st.write(f"{formatar_preco(s['preco'])} · {formatar_duracao(s['duracao_min'])} · "
                         f"{s['profissional']}")
                if consulta.conclusivo:
                    st.progress(rec.cf, text=f"Certeza {rec.cf:.0%} ({nivel_certeza(rec.cf)})")
                if not rec.cabe_orcamento:
                    st.caption("Acima do orçamento informado.")
                if not rec.cabe_tempo:
                    st.caption("Demora mais do que o tempo disponível.")
        for _, texto, _ in consulta.alertas:
            st.warning(texto)

        if consulta.conclusivo:
            with st.expander("Como chegamos a essas recomendações?"):
                for rec in consulta.recomendacoes:
                    st.code(como(consulta, ("recomendacao", rec.servico["id"]),
                                 rotulos, salao.servicos), language=None)
        with st.expander("Por que um serviço não foi recomendado?"):
            nomes = {sid: s["nome"] for sid, s in salao.servicos.items()
                     if sid != "avaliacao_presencial"}
            sid = st.selectbox("Serviço", list(nomes), format_func=nomes.get, index=None,
                               placeholder="Escolha um serviço", key="pq_nao")
            if sid:
                st.code(por_que_nao(consulta, sid, salao.motor, salao.servicos, rotulos),
                        language=None)

# ---------------- Base de conhecimento ----------------
with aba_regras:
    st.write(f"{len(salao.regras)} regras carregadas de `data/regras.json`. "
             "Para atualizar a base, edite o arquivo; não é preciso mexer no código.")
    tabela = [{
        "Regra": r["id"],
        "Descrição": r["descricao"],
        "Se": " E ".join(descrever_condicao(c, rotulos) for c in r["se"]),
        "Então": f"{r['entao'][0]} = {r['entao'][1]}",
        "CF": r["cf"],
    } for r in salao.regras]
    st.dataframe(tabela, hide_index=True)

# ---------------- Estatísticas ----------------
with aba_dados:
    if not historico:
        st.info("Histórico de atendimentos não encontrado em data/historico_atendimentos.csv.")
    else:
        st.write("Dados fictícios de atendimentos, usados como critério de desempate "
                 "entre recomendações com a mesma certeza.")
        col1, col2 = st.columns(2)
        col1.metric("Atendimentos no histórico", len(historico))
        col2.metric("Ticket médio", formatar_preco(ticket_medio(historico)))
        ranking = ranking_servicos(historico)
        st.bar_chart({salao.servicos[sid]["nome"]: qtd for sid, qtd in ranking},
                     horizontal=True)
        medias = avaliacao_media_por_servico(historico)
        st.dataframe([{"Serviço": salao.servicos[sid]["nome"], "Avaliação média": round(m, 2)}
                      for sid, m in sorted(medias.items(), key=lambda x: -x[1])],
                     hide_index=True)
