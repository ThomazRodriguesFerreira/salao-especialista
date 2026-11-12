"""Base de conhecimento do Salão Aurora: carregamento e validação.

Os fatos (serviços, perguntas) e as regras ficam em arquivos JSON na pasta
data/. Assim a base pode ser atualizada sem mexer no código-fonte.
"""
import json
from pathlib import Path

DIR_DADOS = Path(__file__).resolve().parent.parent / "data"
OPERADORES = {"=", "em", "nao", "nao_em"}
OPERADORES_LISTA = {"em", "nao_em"}


class ErroBaseConhecimento(Exception):
    """Problema ao carregar ou validar a base de conhecimento."""


class RespostaInvalida(ValueError):
    """Resposta do usuário fora do que a base de conhecimento aceita."""


def _ler_json(nome, dir_dados):
    caminho = Path(dir_dados) / nome
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError as erro:
        raise ErroBaseConhecimento(f"Arquivo não encontrado: {caminho}") from erro
    except json.JSONDecodeError as erro:
        raise ErroBaseConhecimento(f"JSON inválido em {caminho}: {erro}") from erro


def carregar_servicos(dir_dados=DIR_DADOS):
    """Retorna {id_do_serviço: dados do serviço}."""
    return {s["id"]: s for s in _ler_json("servicos.json", dir_dados)}


def carregar_perguntas(dir_dados=DIR_DADOS):
    return _ler_json("perguntas.json", dir_dados)


def carregar_regras(dir_dados=DIR_DADOS):
    """Retorna (lista de regras, dicionário de alertas)."""
    dados = _ler_json("regras.json", dir_dados)
    return dados["regras"], dados["alertas"]


def carregar_base(dir_dados=DIR_DADOS):
    """Carrega e valida toda a base de conhecimento."""
    servicos = carregar_servicos(dir_dados)
    perguntas = carregar_perguntas(dir_dados)
    regras, alertas = carregar_regras(dir_dados)
    validar_base(servicos, perguntas, regras, alertas)
    return {"servicos": servicos, "perguntas": perguntas,
            "regras": regras, "alertas": alertas}


def validar_base(servicos, perguntas, regras, alertas):
    """Confere a consistência da base; levanta ErroBaseConhecimento se houver erros."""
    erros = []
    opcoes_validas = {}
    for pergunta in perguntas:
        for campo in ("id", "texto", "opcoes"):
            if campo not in pergunta:
                erros.append(f"Pergunta sem o campo '{campo}': {pergunta}")
        if "id" in pergunta and "opcoes" in pergunta:
            opcoes_validas[pergunta["id"]] = {o[0] for o in pergunta["opcoes"]}

    ids_vistos = set()
    for regra in regras:
        rid = regra.get("id", "?")
        if rid in ids_vistos:
            erros.append(f"{rid}: id de regra duplicado")
        ids_vistos.add(rid)
        for campo in ("id", "descricao", "se", "entao", "cf"):
            if campo not in regra:
                erros.append(f"{rid}: falta o campo '{campo}'")
        if not isinstance(regra.get("cf"), (int, float)) or not 0 < regra["cf"] <= 1:
            erros.append(f"{rid}: cf deve estar entre 0 (exclusivo) e 1")
        conclusao = regra.get("entao", [])
        if len(conclusao) != 2:
            erros.append(f"{rid}: 'entao' deve ter [atributo, valor]")
        elif conclusao[0] == "recomendacao" and conclusao[1] not in servicos:
            erros.append(f"{rid}: serviço inexistente '{conclusao[1]}'")
        elif conclusao[0] == "alerta" and conclusao[1] not in alertas:
            erros.append(f"{rid}: alerta inexistente '{conclusao[1]}'")
        for condicao in regra.get("se", []):
            if len(condicao) != 3 or condicao[1] not in OPERADORES:
                erros.append(f"{rid}: condição inválida {condicao}")
                continue
            atributo, operador, valor = condicao
            if (operador in OPERADORES_LISTA) != isinstance(valor, list):
                erros.append(f"{rid}: operador '{operador}' com valor incompatível em {condicao}")
                continue
            valores = valor if isinstance(valor, list) else [valor]
            if atributo in opcoes_validas:
                for v in valores:
                    if v not in opcoes_validas[atributo]:
                        erros.append(f"{rid}: valor '{v}' não existe na pergunta '{atributo}'")
    if erros:
        raise ErroBaseConhecimento("\n".join(erros))


def deve_perguntar(pergunta, respostas):
    """True se a pergunta se aplica, dadas as respostas já coletadas."""
    for atributo, valores in pergunta.get("perguntar_se", {}).items():
        if respostas.get(atributo) not in valores:
            return False
    return True


def validar_respostas(respostas, perguntas):
    """Valida as respostas do usuário; levanta RespostaInvalida se algo estiver errado."""
    if not isinstance(respostas, dict):
        raise RespostaInvalida("As respostas devem ser informadas como um dicionário.")
    opcoes = {p["id"]: {o[0] for o in p["opcoes"]} for p in perguntas}
    if "objetivo" not in respostas:
        raise RespostaInvalida("É obrigatório informar o objetivo do atendimento.")
    for atributo, valor in respostas.items():
        if atributo not in opcoes:
            raise RespostaInvalida(f"Pergunta desconhecida: '{atributo}'.")
        if valor not in opcoes[atributo]:
            raise RespostaInvalida(f"Valor inválido '{valor}' para '{atributo}'.")
    return dict(respostas)
