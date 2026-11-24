from src.interface_console import executar


def rodar(entradas):
    """Executa o console com entradas simuladas e devolve tudo que foi impresso."""
    fila = iter(entradas)
    saida = []

    def entrada(_prompt=""):
        try:
            return next(fila)
        except StopIteration:
            raise EOFError

    executar(entrada=entrada, saida=saida.append)
    return "\n".join(saida)


def test_fluxo_completo_unhas():
    # objetivo=unhas (8), orçamento=médio (2), tempo=médio (2), depois "como" (1) e sair (0)
    texto = rodar(["8", "2", "2", "1", "0"])
    assert "Manicure" in texto
    assert "R36" in texto          # explicação "como" cita a regra
    assert "Obrigado" in texto


def test_entrada_invalida_repete_pergunta():
    texto = rodar(["99", "abc", "8", "2", "2", "0"])
    assert texto.count("Opção inválida") == 2
    assert "Manicure" in texto


def test_interrogacao_explica_por_que_pergunta():
    texto = rodar(["?", "8", "2", "2", "0"])
    assert "Por que pergunto isso?" in texto


def test_sem_conclusao_mostra_mensagem():
    # reduzir_volume(3), liso(1), saudável(1), química não(2), couro normal(1),
    # gestante não(2), orçamento alto(3), tempo curto(1)
    texto = rodar(["3", "1", "1", "2", "1", "2", "3", "1", "0"])
    assert "Não foi possível concluir" in texto


def test_por_que_nao_pelo_menu():
    # unhas, orçamento médio, tempo médio; menu 2 (por que não); serviço 5 = Coloração; sair
    texto = rodar(["8", "2", "2", "2", "5", "0"])
    assert "não foi recomendado" in texto


def test_sair_no_meio():
    texto = rodar(["1", "sair"])
    assert "Obrigado" in texto


def test_fim_da_entrada_nao_quebra():
    texto = rodar(["1"])
    assert "Obrigado" in texto
