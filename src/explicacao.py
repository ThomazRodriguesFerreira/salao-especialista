"""Módulo de explicação: "por que perguntamos", "como concluímos" e "por que não".

É o coração de um sistema especialista: o sistema consegue justificar o raciocínio
mostrando as regras e os fatos que usou.
"""


# ---------- formatação ----------
def formatar_preco(valor):
    return "Grátis" if valor == 0 else f"R$ {valor:.2f}".replace(".", ",")


def formatar_duracao(minutos):
    horas, resto = divmod(int(minutos), 60)
    if horas == 0:
        return f"{resto} min"
    return f"{horas}h{resto:02d}" if resto else f"{horas}h"


def nivel_certeza(cf):
    if cf >= 0.7:
        return "alta"
    if cf >= 0.5:
        return "média"
    return "baixa"


def montar_rotulos(perguntas):
    """{(atributo, valor): texto legível} a partir das opções das perguntas."""
    return {(p["id"], o[0]): o[1] for p in perguntas for o in p["opcoes"]}


def _valor(rotulos, atributo, valor):
    return rotulos.get((atributo, valor), valor)


def descrever_condicao(condicao, rotulos=None):
    rotulos = rotulos or {}
    atributo, operador, valor = condicao
    if operador == "=":
        return f"{atributo} = {_valor(rotulos, atributo, valor)}"
    if operador == "em":
        itens = ", ".join(_valor(rotulos, atributo, v) for v in valor)
        return f"{atributo} é um de [{itens}]"
    if operador == "nao":
        return f"NÃO existe o fato ({atributo} = {_valor(rotulos, atributo, valor)})"
    itens = ", ".join(_valor(rotulos, atributo, v) for v in valor)
    return f"NÃO existe nenhum dos fatos ({atributo} em [{itens}])"


# ---------- por que perguntamos ----------
def por_que_perguntar(atributo, regras, orcamento_e_tempo=True):
    """Explica por que uma pergunta é feita: quais regras usam a informação."""
    diretas = [r for r in regras if any(c[0] == atributo for c in r["se"])]
    afetadas = {r["id"] for r in diretas}
    fila = [r["entao"][0] for r in diretas]
    vistos = set()
    while fila:  # segue a cadeia: fatos derivados que alimentam outras regras
        atual = fila.pop()
        if atual in vistos:
            continue
        vistos.add(atual)
        for r in regras:
            if any(c[0] == atual for c in r["se"]):
                afetadas.add(r["id"])
                fila.append(r["entao"][0])
    partes = []
    if afetadas:
        ids = ", ".join(sorted(afetadas))
        partes.append(f"Essa informação é usada em {len(afetadas)} regra(s) da base ({ids}).")
        if diretas:
            exemplo = diretas[0]
            partes.append(f"Por exemplo, {exemplo['id']}: {exemplo['descricao']}.")
    if orcamento_e_tempo and atributo in ("orcamento", "tempo"):
        partes.append("Ela também define se cada serviço recomendado cabe no seu "
                      + ("orçamento." if atributo == "orcamento" else "tempo."))
    return " ".join(partes) or "Essa informação ajuda a profissional a conhecer melhor o seu atendimento."


# ---------- como concluímos ----------
def _fonte(consulta, atributo, valor):
    if consulta.respostas.get(atributo) == valor:
        return "informado por você"
    return None


def _linhas_disparo(consulta, chave, nivel, rotulos, vistos):
    recuo = "    " * nivel
    disparos = [d for d in consulta.resultado.disparos if d.conclusao == chave]
    linhas = []
    for d in disparos:
        linhas.append(f"{recuo}← {d.regra_id}: {d.descricao} "
                      f"[CF da regra {d.cf_regra:.2f} × premissas {d.cf_premissas:.2f} "
                      f"= {d.cf_resultado:.2f}]")
        for atributo, operador, valor, cf in d.premissas:
            texto = descrever_condicao((atributo, operador, valor), rotulos)
            if operador in ("nao", "nao_em"):
                linhas.append(f"{recuo}    • {texto} (nada na base contradiz)")
                continue
            valores = [valor] if operador == "=" else list(valor)
            derivado = [v for v in valores if (atributo, v) in consulta.resultado.derivados]
            if derivado and not any(consulta.respostas.get(atributo) == v for v in valores):
                alvo = (atributo, derivado[0])
                linhas.append(f"{recuo}    • {texto} (derivado, certeza {cf:.0%})")
                if alvo not in vistos:
                    linhas.extend(_linhas_disparo(consulta, alvo, nivel + 2, rotulos, vistos | {alvo}))
            else:
                linhas.append(f"{recuo}    • {texto} (informado por você)")
    return linhas


def como(consulta, objetivo, rotulos=None, servicos=None):
    """Mostra a cadeia de regras e fatos que levou a uma conclusão.
    objetivo = (atributo, valor), ex.: ("recomendacao", "progressiva")."""
    rotulos = rotulos or {}
    atributo, valor = objetivo
    cf = consulta.resultado.cf(atributo, valor)
    if cf == 0:
        return "Esse fato não foi concluído nesta consulta."
    nome = servicos[valor]["nome"] if servicos and atributo == "recomendacao" else valor
    cabecalho = f"{atributo}: {nome} (certeza {cf:.0%})"
    linhas = _linhas_disparo(consulta, tuple(objetivo), 0, rotulos, {tuple(objetivo)})
    return "\n".join([cabecalho] + linhas)


# ---------- por que não ----------
def _regras_que_dispararam(no):
    return [item["regra"]["id"] for item in no["regras"] if item["disparou"]]


def por_que_nao(consulta, servico_id, motor, servicos, rotulos=None):
    """Explica por que um serviço NÃO foi recomendado (encadeamento para trás)."""
    rotulos = rotulos or {}
    nome = servicos[servico_id]["nome"]
    if consulta.resultado.cf("recomendacao", servico_id) >= 0.3:
        return f"{nome} foi recomendado. Use a opção 'como' para ver o raciocínio."
    arvore = motor.arvore_objetivo(("recomendacao", servico_id), consulta.resultado.memoria)
    if not arvore["regras"]:
        return f"Nenhuma regra da base leva a {nome}."
    linhas = [f"{nome} não foi recomendado. Regras que poderiam recomendá-lo:"]
    for item in arvore["regras"]:
        regra = item["regra"]
        linhas.append(f"  {regra['id']}: {regra['descricao']}")
        if item["disparou"]:
            linhas.append("     as condições foram atendidas, mas a certeza ficou abaixo do mínimo.")
            continue
        for cond in item["condicoes"]:
            marca = "✓" if cond["satisfeita"] else "✗"
            texto = descrever_condicao(cond["condicao"], rotulos)
            extra = ""
            sub = cond["sub"]
            if not cond["satisfeita"] and sub is not None and sub["provado"]:
                extra = f" — o fato foi derivado por {', '.join(_regras_que_dispararam(sub))}"
            linhas.append(f"     {marca} {texto}{extra}")
    return "\n".join(linhas)


# ---------- relatório completo ----------
def formatar_resultado(consulta, rotulos=None):
    linhas = []
    if not consulta.conclusivo:
        linhas.append("Não foi possível concluir com as informações fornecidas.")
        linhas.append("Sugestão: uma avaliação presencial gratuita com nossa equipe.")
    else:
        linhas.append("Recomendações para você:")
    for posicao, rec in enumerate(consulta.recomendacoes, 1):
        s = rec.servico
        linha = (f"{posicao}. {s['nome']} — {formatar_preco(s['preco'])}, "
                 f"{formatar_duracao(s['duracao_min'])}")
        if consulta.conclusivo:
            linha += f" — certeza {rec.cf:.0%} ({nivel_certeza(rec.cf)})"
        linhas.append(linha)
        linhas.append(f"   {s['descricao']} Profissional: {s['profissional']}.")
        if not rec.cabe_orcamento:
            linhas.append("   Atenção: acima do orçamento informado.")
        if not rec.cabe_tempo:
            linhas.append("   Atenção: demora mais do que o tempo disponível.")
    if consulta.alertas:
        linhas.append("")
        linhas.append("Avisos importantes:")
        for _, texto, _ in consulta.alertas:
            linhas.append(f"  ! {texto}")
    return "\n".join(linhas)
