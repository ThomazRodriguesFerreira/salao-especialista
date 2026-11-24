"""Interface de terminal do Salão Aurora (perguntas e respostas).

As funções recebem 'entrada' e 'saida' para poderem ser testadas sem teclado.
"""
from src.base_conhecimento import deve_perguntar
from src.estatisticas import ErroHistorico, carregar_historico, popularidade
from src.explicacao import (como, formatar_resultado, montar_rotulos,
                            por_que_nao, por_que_perguntar)
from src.recomendador import SalaoEspecialista

BANNER = """
==============================================
  Salão Aurora — Consultor de Serviços
  Sistema especialista de triagem e recomendação
==============================================
Responda às perguntas e eu indico os serviços mais adequados.
Em qualquer pergunta, digite ? para saber por que ela é feita.
"""


class SairDoPrograma(Exception):
    pass


def perguntar(pergunta, regras, entrada=input, saida=print):
    """Faz uma pergunta de múltipla escolha e repete até a resposta ser válida."""
    opcoes = pergunta["opcoes"]
    while True:
        saida(f"\n{pergunta['texto']}")
        for numero, (_, rotulo) in enumerate(opcoes, 1):
            saida(f"  {numero}) {rotulo}")
        resposta = entrada("> ").strip().lower()
        if resposta in ("sair", "exit"):
            raise SairDoPrograma
        if resposta == "?":
            saida("\nPor que pergunto isso? " + por_que_perguntar(pergunta["id"], regras))
            continue
        if resposta.isdigit() and 1 <= int(resposta) <= len(opcoes):
            return opcoes[int(resposta) - 1][0]
        if resposta in {valor for valor, _ in opcoes}:
            return resposta
        saida(f"Opção inválida. Digite um número de 1 a {len(opcoes)}, ? ou sair.")


def coletar_respostas(salao, entrada=input, saida=print):
    respostas = {}
    for pergunta in salao.perguntas:
        if deve_perguntar(pergunta, respostas):
            respostas[pergunta["id"]] = perguntar(pergunta, salao.regras, entrada, saida)
    return respostas


def _menu_pos_resultado(salao, consulta, rotulos, entrada, saida):
    while True:
        saida("\nO que deseja fazer?")
        saida("  1) Como chegaram a essas recomendações?")
        saida("  2) Por que um serviço não foi recomendado?")
        saida("  3) Nova consulta")
        saida("  0) Sair")
        opcao = entrada("> ").strip()
        if opcao == "1":
            if not consulta.conclusivo:
                saida("Nenhuma conclusão foi tirada, então não há raciocínio a mostrar.")
            for rec in consulta.recomendacoes if consulta.conclusivo else []:
                saida("\n" + como(consulta, ("recomendacao", rec.servico["id"]),
                                  rotulos, salao.servicos))
        elif opcao == "2":
            _escolher_servico_para_por_que_nao(salao, consulta, rotulos, entrada, saida)
        elif opcao == "3":
            return True
        elif opcao == "0":
            return False
        else:
            saida("Opção inválida.")


def _escolher_servico_para_por_que_nao(salao, consulta, rotulos, entrada, saida):
    ids = [sid for sid in salao.servicos if sid != "avaliacao_presencial"]
    for numero, sid in enumerate(ids, 1):
        saida(f"  {numero}) {salao.servicos[sid]['nome']}")
    escolha = entrada("Número do serviço > ").strip()
    if escolha.isdigit() and 1 <= int(escolha) <= len(ids):
        saida("\n" + por_que_nao(consulta, ids[int(escolha) - 1], salao.motor,
                                 salao.servicos, rotulos))
    else:
        saida("Número inválido.")


def criar_salao():
    """Cria o sistema com a popularidade do histórico (se o CSV existir)."""
    try:
        pop = popularidade(carregar_historico())
    except ErroHistorico:
        pop = {}
    return SalaoEspecialista.padrao(popularidade=pop)


def executar(entrada=input, saida=print):
    salao = criar_salao()
    rotulos = montar_rotulos(salao.perguntas)
    saida(BANNER)
    try:
        continuar = True
        while continuar:
            respostas = coletar_respostas(salao, entrada, saida)
            consulta = salao.consultar(respostas)
            saida("\n" + formatar_resultado(consulta, rotulos))
            continuar = _menu_pos_resultado(salao, consulta, rotulos, entrada, saida)
    except (SairDoPrograma, EOFError, KeyboardInterrupt):
        pass
    saida("\nObrigado por usar o Consultor do Salão Aurora!")
