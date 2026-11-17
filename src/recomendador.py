"""Camada de negócio do Salão Aurora: transforma a inferência em recomendações.

Recebe as respostas da cliente, roda o motor e devolve serviços ordenados por
certeza, com indicação de orçamento/tempo, alertas e tratamento de "sem conclusão".
"""
from dataclasses import dataclass, field

from src.base_conhecimento import carregar_base, validar_respostas
from src.motor_inferencia import MotorInferencia, Resultado

LIMITE_ORCAMENTO = {"baixo": 100, "medio": 250, "alto": float("inf")}
LIMITE_TEMPO_MIN = {"curto": 90, "medio": 180, "longo": float("inf")}
MIN_CF_RECOMENDACAO = 0.3
SERVICO_FALLBACK = "avaliacao_presencial"


@dataclass
class Recomendacao:
    servico: dict
    cf: float
    cabe_orcamento: bool = True
    cabe_tempo: bool = True
    popularidade: float = 0.0   # fração dos atendimentos históricos (0 a 1)


@dataclass
class Consulta:
    respostas: dict
    resultado: Resultado
    recomendacoes: list
    alertas: list = field(default_factory=list)   # [(id, texto, cf)]
    conclusivo: bool = True


class SalaoEspecialista:
    def __init__(self, base, popularidade=None):
        self.servicos = base["servicos"]
        self.perguntas = base["perguntas"]
        self.regras = base["regras"]
        self.alertas = base["alertas"]
        self.popularidade = popularidade or {}
        self.motor = MotorInferencia(self.regras)

    @classmethod
    def padrao(cls, popularidade=None, dir_dados=None):
        base = carregar_base(dir_dados) if dir_dados else carregar_base()
        return cls(base, popularidade)

    def consultar(self, respostas):
        """Executa uma consulta completa. Levanta RespostaInvalida se os dados forem inválidos."""
        respostas = validar_respostas(respostas, self.perguntas)
        resultado = self.motor.inferir(respostas)
        recomendacoes = self._montar_recomendacoes(resultado, respostas)
        alertas = [(valor, self.alertas[valor], cf)
                   for valor, cf in resultado.valores("alerta")]
        conclusivo = bool(recomendacoes)
        if not conclusivo:
            fallback = self.servicos[SERVICO_FALLBACK]
            recomendacoes = [Recomendacao(fallback, 0.0)]
        return Consulta(respostas, resultado, recomendacoes, alertas, conclusivo)

    def _montar_recomendacoes(self, resultado, respostas):
        limite_preco = LIMITE_ORCAMENTO.get(respostas.get("orcamento"), float("inf"))
        limite_tempo = LIMITE_TEMPO_MIN.get(respostas.get("tempo"), float("inf"))
        itens = []
        for servico_id, cf in resultado.valores("recomendacao"):
            if cf < MIN_CF_RECOMENDACAO:
                continue
            servico = self.servicos[servico_id]
            itens.append(Recomendacao(
                servico, cf,
                cabe_orcamento=servico["preco"] <= limite_preco,
                cabe_tempo=servico["duracao_min"] <= limite_tempo,
                popularidade=self.popularidade.get(servico_id, 0.0)))
        # ordena por certeza; empate decidido pela popularidade e depois pelo preço
        itens.sort(key=lambda r: (-r.cf, -r.popularidade, r.servico["preco"]))
        return itens
