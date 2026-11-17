"""Motor de inferência: encadeamento para frente com fatores de certeza (CF).

Memória de trabalho: {atributo: {valor: cf}}.
- Fatos informados pelo usuário entram com CF = 1.0.
- Cada regra tem um CF próprio. Ao disparar, o CF da conclusão é
  CF_regra x menor CF entre as premissas (estilo MYCIN).
- Se várias regras concluem o mesmo fato, os CFs são combinados:
  cf = a + b * (1 - a).

Operadores das condições [atributo, operador, valor]:
  "="      o fato (atributo, valor) existe
  "em"     algum dos valores da lista existe
  "nao"    o fato NÃO existe (negação por falha)
  "nao_em" nenhum dos valores da lista existe
"""
from dataclasses import dataclass

LIMIAR_PRESENCA = 0.2   # CF mínimo para um fato ser considerado verdadeiro
MAX_RODADAS = 20        # proteção contra regras que nunca estabilizam


@dataclass
class Disparo:
    """Registro de uma regra que disparou (usado na explicação)."""
    regra_id: str
    descricao: str
    premissas: list      # [(atributo, operador, valor, cf)]
    conclusao: tuple     # (atributo, valor)
    cf_regra: float
    cf_premissas: float
    cf_resultado: float


@dataclass
class Resultado:
    respostas: dict      # fatos informados pelo usuário
    memoria: dict        # fatos do usuário + derivados, com CF
    derivados: dict      # {(atributo, valor): cf} apenas os derivados
    disparos: list       # regras que dispararam na rodada final
    rodadas: int

    def cf(self, atributo, valor):
        return self.memoria.get(atributo, {}).get(valor, 0.0)

    def valores(self, atributo):
        """Lista [(valor, cf)] do atributo, do maior CF para o menor."""
        itens = self.memoria.get(atributo, {}).items()
        return sorted(itens, key=lambda item: item[1], reverse=True)


class MotorInferencia:
    def __init__(self, regras, limiar=LIMIAR_PRESENCA):
        self.regras = regras
        self.limiar = limiar
        self._conclusoes = {tuple(r["entao"]) for r in regras}

    @staticmethod
    def combinar_cf(a, b):
        """Combina dois CFs positivos que apoiam a mesma conclusão."""
        return a + b * (1 - a)

    # ---------- avaliação de condições ----------
    def _avaliar_condicao(self, memoria, condicao):
        atributo, operador, valor = condicao
        existentes = memoria.get(atributo, {})
        if operador == "=":
            cf = existentes.get(valor, 0.0)
            return cf >= self.limiar, cf
        if operador == "em":
            cf = max((existentes.get(v, 0.0) for v in valor), default=0.0)
            return cf >= self.limiar, cf
        if operador == "nao":
            return existentes.get(valor, 0.0) < self.limiar, 1.0
        if operador == "nao_em":
            return all(existentes.get(v, 0.0) < self.limiar for v in valor), 1.0
        raise ValueError(f"Operador desconhecido: {operador}")

    def avaliar_condicoes(self, regra, memoria):
        """Retorna [(condição, satisfeita, cf)] para cada premissa da regra."""
        saida = []
        for condicao in regra["se"]:
            ok, cf = self._avaliar_condicao(memoria, condicao)
            saida.append((tuple(condicao), ok, cf))
        return saida

    def _disparar(self, regra, memoria):
        avaliacoes = self.avaliar_condicoes(regra, memoria)
        if not all(ok for _, ok, _ in avaliacoes):
            return None
        cf_premissas = min((cf for _, _, cf in avaliacoes), default=1.0)
        cf_resultado = round(regra["cf"] * cf_premissas, 4)
        if cf_resultado < self.limiar:
            return None
        premissas = [(c[0], c[1], c[2], cf) for c, _, cf in avaliacoes]
        return Disparo(regra["id"], regra["descricao"], premissas,
                       tuple(regra["entao"]), regra["cf"], cf_premissas, cf_resultado)

    # ---------- encadeamento para frente ----------
    def inferir(self, respostas):
        """Roda as regras repetidamente até os fatos derivados estabilizarem."""
        base = {atributo: {valor: 1.0} for atributo, valor in respostas.items()}
        derivados, disparos = {}, []
        for rodada in range(1, MAX_RODADAS + 1):
            memoria = self._montar_memoria(base, derivados)
            novos, disparos_rodada = {}, []
            for regra in self.regras:
                disparo = self._disparar(regra, memoria)
                if disparo is None:
                    continue
                disparos_rodada.append(disparo)
                chave = disparo.conclusao
                if chave in novos:
                    novos[chave] = self.combinar_cf(novos[chave], disparo.cf_resultado)
                else:
                    novos[chave] = disparo.cf_resultado
            novos = {k: round(v, 4) for k, v in novos.items()}
            estavel = novos == derivados
            derivados, disparos = novos, disparos_rodada
            if estavel:
                break
        else:
            raise RuntimeError("As regras não estabilizaram: verifique ciclos na base.")
        return Resultado(dict(respostas), self._montar_memoria(base, derivados),
                         derivados, disparos, rodada)

    @staticmethod
    def _montar_memoria(base, derivados):
        memoria = {a: dict(v) for a, v in base.items()}
        for (atributo, valor), cf in derivados.items():
            memoria.setdefault(atributo, {}).setdefault(valor, cf)
        return memoria

    # ---------- encadeamento para trás ----------
    def arvore_objetivo(self, objetivo, memoria, _visitados=frozenset()):
        """Parte de um objetivo (atributo, valor) e procura as regras que o
        concluem, verificando cada premissa (e, recursivamente, as premissas
        que também são conclusões de outras regras).
        Serve para explicar 'como' e 'por que não'."""
        atributo, valor = objetivo
        cf = memoria.get(atributo, {}).get(valor, 0.0)
        no = {"objetivo": tuple(objetivo), "cf": cf,
              "provado": cf >= self.limiar, "regras": []}
        visitados = _visitados | {tuple(objetivo)}
        for regra in self.regras:
            if tuple(regra["entao"]) != tuple(objetivo):
                continue
            condicoes = []
            for condicao in regra["se"]:
                atr, operador, val = condicao
                ok, cf_cond = self._avaliar_condicao(memoria, condicao)
                sub = None
                alvo = (atr, val)
                if operador in ("=", "nao") and alvo in self._conclusoes and alvo not in visitados:
                    sub = self.arvore_objetivo(alvo, memoria, visitados)
                condicoes.append({"condicao": tuple(condicao), "satisfeita": ok,
                                  "cf": cf_cond, "sub": sub})
            no["regras"].append({"regra": regra,
                                 "disparou": all(c["satisfeita"] for c in condicoes),
                                 "condicoes": condicoes})
        return no
