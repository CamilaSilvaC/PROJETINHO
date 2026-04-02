"""Motor unificado de busca para a biblioteca."""

from __future__ import annotations

import re
import time


class MotorBusca:
    """Roteia consultas entre BST, índice invertido e busca fuzzy."""

    def __init__(self, biblioteca):
        """Armazena a referência para a instância de biblioteca."""
        self.biblioteca = biblioteca

    def buscar(self, query: str) -> dict:
        """Executa a busca e retorna metadados do motor utilizado."""
        inicio = time.perf_counter()
        query_limpa = query.strip()
        resultados: list[dict] = []
        motor_usado = "VAZIO"
        comparacoes = None
        score = None
        sugestao = None

        if query_limpa == "":
            fim = time.perf_counter()
            return {
                "resultados": [],
                "motor_usado": "VAZIO",
                "tempo_ms": round((fim - inicio) * 1000, 2),
                "comparacoes": None,
                "score": None,
                "sugestao": None,
            }

        if self.biblioteca.bst and re.fullmatch(r"\d+", query_limpa):
            encontrado = self.biblioteca.bst.buscar(int(query_limpa))
            resultados = [encontrado] if encontrado else []
            motor_usado = "BST_EXATA"
            comparacoes = self.biblioteca.bst.comparacoes
        elif self.biblioteca.bst and re.fullmatch(r"\d+\s*-\s*\d+", query_limpa):
            a, b = re.findall(r"\d+", query_limpa)
            resultados = self.biblioteca.bst.buscar_intervalo(int(a), int(b))
            motor_usado = "BST_INTERVALO"
            comparacoes = self.biblioteca.bst.comparacoes
        # Caso 4 — busca textual
        else:
            from indices.indice_invertido import tokenizar
            tokens = tokenizar(query)
            vocabulario = set(self.biblioteca.indice_invertido.vocabulario())
            tokens_nao_encontrados = [t for t in tokens if t not in vocabulario]

            # Se qualquer token não existe no vocabulário → erro de digitação → Fuzzy
            if tokens_nao_encontrados:
                resultados = self.biblioteca.buscador_fuzzy.buscar(query)
                motor_usado = "FUZZY"
                comparacoes = None
                score = self.biblioteca.buscador_fuzzy.ultimo_score
                sugestao = self.biblioteca.buscador_fuzzy.sugerir_correcao(query)

            else:
                # Todos os tokens são válidos — tenta AND primeiro
                resultados = self.biblioteca.indice_invertido.buscar(query)
                if resultados:
                    motor_usado = "INVERTIDO"
                    comparacoes = None
                    score = None
                    sugestao = None

                else:
                    # AND não achou combinação — tenta OR
                    resultados = self.biblioteca.indice_invertido.buscar_qualquer(query)
                    if resultados:
                        motor_usado = "INVERTIDO_OR"
                        comparacoes = None
                        score = None
                        sugestao = None

                    else:
                        # Nem AND nem OR acharam — usa Fuzzy
                        resultados = self.biblioteca.buscador_fuzzy.buscar(query)
                        motor_usado = "FUZZY"
                        comparacoes = None
                        score = self.biblioteca.buscador_fuzzy.ultimo_score
                        sugestao = self.biblioteca.buscador_fuzzy.sugerir_correcao(query)

        fim = time.perf_counter()
        return {
            "resultados": resultados,
            "motor_usado": motor_usado,
            "tempo_ms": round((fim - inicio) * 1000, 2),
            "comparacoes": comparacoes,
            "score": score,
            "sugestao": sugestao,
        }
