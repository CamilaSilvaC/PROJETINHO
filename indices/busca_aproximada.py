"""Busca aproximada para livros usando RapidFuzz."""

from __future__ import annotations

from rapidfuzz import process, fuzz

try:
    from indices.indice_invertido import IndiceInvertido, tokenizar
except ModuleNotFoundError:
    from indice_invertido import IndiceInvertido, tokenizar


class BuscaAproximada:
    """Busca aproximada baseada no vocabulário do índice invertido."""

    def __init__(self, indice_invertido: IndiceInvertido):
        """Armazena a referência ao índice invertido existente."""
        self._indice = indice_invertido
        self.ultimo_score: float = 0.0

    def buscar(self, query: str, limiar: int = 80) -> list[dict]:
        """Busca livros por similaridade textual com agregação de scores médios."""
        tokens = tokenizar(query)
        if not tokens:
            self.ultimo_score = 0.0
            return []

        vocabulario = self._indice.vocabulario()
        if not vocabulario:
            self.ultimo_score = 0.0
            return []

        numeracoes_encontradas: set[str] = set()
        scores_coletados: list[float] = []

        for token in tokens:
            similares = process.extract(
                token,
                vocabulario,
                scorer=fuzz.ratio,
                score_cutoff=limiar,
                limit=5,
            )
            for token_similar, score, _ in similares:
                numeros = self._indice._indice.get(token_similar, set())
                numeracoes_encontradas.update(numeros)
                scores_coletados.append(float(score))

        if not numeracoes_encontradas:
            self.ultimo_score = 0.0
            return []

        self.ultimo_score = round(sum(scores_coletados) / len(scores_coletados), 2) if scores_coletados else 0.0
        return [self._indice._livros[n] for n in sorted(numeracoes_encontradas) if n in self._indice._livros]

    def sugerir_correcao(self, query: str) -> str | None:
        """Sugere uma versão corrigida da consulta quando houver tokens próximos."""
        tokens = tokenizar(query)
        if not tokens:
            return None

        vocabulario = self._indice.vocabulario()
        if not vocabulario:
            return None

        corrigidos: list[str] = []
        todos_certos = True

        for token in tokens:
            melhor = process.extractOne(
                token,
                vocabulario,
                scorer=fuzz.ratio,
                score_cutoff=60,
            )
            if melhor is None:
                corrigidos.append(token)
                todos_certos = False
                continue

            token_similar, score, _ = melhor
            if score >= 95:
                corrigidos.append(token)
            elif score >= 60:
                corrigidos.append(token_similar)
                todos_certos = False
            else:
                corrigidos.append(token)
                todos_certos = False

        if todos_certos:
            return None
        return " ".join(corrigidos)


if __name__ == "__main__":
    try:
        from indices.indice_invertido import IndiceInvertido
    except ModuleNotFoundError:
        from indice_invertido import IndiceInvertido

    livros_teste = [
        {"numeracao": "0001", "titulo": "Dom Casmurro", "autor": "Machado de Assis",
         "genero": "Romance", "editora": "Penguin", "quantidade": 3},
        {"numeracao": "0003", "titulo": "O Hobbit", "autor": "J.R.R. Tolkien",
         "genero": "Fantasia", "editora": "Martins Fontes", "quantidade": 5},
        {"numeracao": "0004", "titulo": "Duna", "autor": "Frank Herbert",
         "genero": "Ficcao Cientifica", "editora": "Aleph", "quantidade": 3},
    ]

    idx = IndiceInvertido()
    idx.construir(livros_teste)

    fuzzy = BuscaAproximada(idx)

    print("=== Busca com erro: 'tolkeen' ===")
    resultados = fuzzy.buscar("tolkeen")
    for r in resultados:
        print(f"  {r['numeracao']} - {r['titulo']}")
    print(f"  Score: {fuzzy.ultimo_score:.1f}%")

    print("\n=== Sugestao de correcao: 'tolkeen' ===")
    sugestao = fuzzy.sugerir_correcao("tolkeen")
    print(f"  Sugestao: {sugestao}")

    print("\n=== Busca correta nao gera sugestao: 'tolkien' ===")
    sugestao2 = fuzzy.sugerir_correcao("tolkien")
    print(f"  Sugestao: {sugestao2}")
