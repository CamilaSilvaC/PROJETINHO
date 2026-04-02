"""Índice invertido para busca textual de livros."""

from __future__ import annotations

import string
import unicodedata

_STOPWORDS_PTBR = {
    "de", "da", "do", "das", "dos", "e", "o", "a", "os", "as",
    "um", "uma", "em", "para", "por", "com", "se", "na", "no",
    "nas", "nos", "ao", "aos",
}


def tokenizar(texto: str) -> list[str]:
    """Converte um texto em tokens limpos para indexação e busca."""
    if not texto:
        return []

    normalizado = unicodedata.normalize("NFD", texto.lower())
    sem_acentos = normalizado.encode("ascii", "ignore").decode("ascii")
    sem_pontuacao = sem_acentos.translate(str.maketrans("", "", string.punctuation))

    tokens = []
    for token in sem_pontuacao.split():
        if len(token) < 2:
            continue
        if token in _STOPWORDS_PTBR:
            continue
        tokens.append(token)
    return tokens


class IndiceInvertido:
    """Estrutura de índice invertido para consulta textual de livros."""

    def __init__(self) -> None:
        """Inicializa estruturas internas vazias."""
        self._indice: dict[str, set[str]] = {}
        self._livros: dict[str, dict] = {}

    def _indexar_livro(self, livro: dict) -> None:
        """Adiciona um livro nas estruturas internas do índice."""
        numeracao = str(livro.get("numeracao", ""))
        if not numeracao:
            return

        self._livros[numeracao] = dict(livro)
        texto = livro["titulo"] + " " + livro["autor"] + " " + livro["genero"]
        for token in tokenizar(texto):
            self._indice.setdefault(token, set()).add(numeracao)

    def _remover_livro_interno(self, numeracao: str) -> None:
        """Remove um livro do índice sem alterar a lista de entrada."""
        livro_antigo = self._livros.get(numeracao)
        if not livro_antigo:
            return

        texto = livro_antigo["titulo"] + " " + livro_antigo["autor"] + " " + livro_antigo["genero"]
        for token in tokenizar(texto):
            numeros = self._indice.get(token)
            if not numeros:
                continue
            numeros.discard(numeracao)
            if not numeros:
                del self._indice[token]
        self._livros.pop(numeracao, None)

    def construir(self, livros: list[dict]) -> None:
        """Reconstrói o índice inteiro a partir de uma lista de livros."""
        self._indice.clear()
        self._livros.clear()
        for livro in livros:
            if isinstance(livro, dict):
                self._indexar_livro(livro)

    def buscar(self, query: str) -> list[dict]:
        """Retorna livros que contêm todos os tokens da consulta."""
        tokens = tokenizar(query)
        if not tokens:
            return []

        sets: list[set[str]] = []
        for token in tokens:
            if token not in self._indice:
                return []
            sets.append(self._indice[token])

        numeracoes = sets[0].intersection(*sets[1:])
        return [self._livros[n] for n in numeracoes if n in self._livros]

    def buscar_qualquer(self, query: str) -> list[dict]:
        """Retorna livros que contêm ao menos um dos tokens da consulta."""
        tokens = tokenizar(query)
        if not tokens:
            return []

        sets: list[set[str]] = []
        for token in tokens:
            if token in self._indice:
                sets.append(self._indice[token])

        if not sets:
            return []

        numeracoes = set().union(*sets)
        return [self._livros[n] for n in numeracoes if n in self._livros]

    def atualizar(self, livro: dict) -> None:
        """Atualiza um livro no índice, substituindo qualquer versão anterior."""
        numeracao = str(livro.get("numeracao", ""))
        if not numeracao:
            return

        if numeracao in self._livros:
            self._remover_livro_interno(numeracao)
        self._indexar_livro(livro)

    def remover(self, numeracao: str) -> None:
        """Remove um livro do índice e limpa tokens sem referências restantes."""
        self._remover_livro_interno(str(numeracao))

    def vocabulario(self) -> list[str]:
        """Retorna o vocabulário ordenado do índice."""
        return sorted(self._indice.keys())


if __name__ == "__main__":
    livros_teste = [
      {"numeracao": "0001", "titulo": "Dom Casmurro",
       "autor": "Machado de Assis", "genero": "Romance",
       "editora": "Penguin", "quantidade": 3},
      {"numeracao": "0002", "titulo": "Memorias Postumas de Bras Cubas",
       "autor": "Machado de Assis", "genero": "Romance",
       "editora": "Penguin", "quantidade": 2},
      {"numeracao": "0003", "titulo": "O Hobbit",
       "autor": "J.R.R. Tolkien", "genero": "Fantasia",
       "editora": "Martins Fontes", "quantidade": 5},
      {"numeracao": "0004", "titulo": "Vidas Secas",
       "autor": "Graciliano Ramos", "genero": "Regionalismo",
       "editora": "Record", "quantidade": 4},
    ]

    idx = IndiceInvertido()
    idx.construir(livros_teste)

    print("=== DIAGNÓSTICO DE TOKENS ===")
    try:
        from indices.indice_invertido import tokenizar
    except ModuleNotFoundError:
        from indice_invertido import tokenizar
    print("tokenizar('Machado Romance'):", tokenizar("Machado Romance"))
    print("tokenizar('Dom Casmurro'):", tokenizar("Dom Casmurro"))
    print()

    print("=== TOKENS DO LIVRO 0001 ===")
    texto = livros_teste[0]["titulo"] + " " + \
        livros_teste[0]["autor"] + " " + \
        livros_teste[0]["genero"]
    print(f"Texto: '{texto}'")
    print(f"Tokens: {tokenizar(texto)}")
    print()

    print("=== TESTES DE BUSCA (todos devem ter resultado) ===")

    r1 = idx.buscar("machado")
    print(f"'machado' → {len(r1)} resultado(s) "
        f"{'OK' if len(r1) == 2 else 'FALHOU'}")

    r2 = idx.buscar("romance")
    print(f"'romance' → {len(r2)} resultado(s) "
        f"{'OK' if len(r2) == 2 else 'FALHOU'}")

    r3 = idx.buscar("Machado Romance")
    print(f"'Machado Romance' → {len(r3)} resultado(s) "
        f"{'OK' if len(r3) == 2 else 'FALHOU'}")

    r4 = idx.buscar("tolkien fantasia")
    print(f"'tolkien fantasia' → {len(r4)} resultado(s) "
        f"{'OK' if len(r4) == 1 else 'FALHOU'}")

    r5 = idx.buscar("tolkien romance")
    print(f"'tolkien romance' → {len(r5)} resultado(s) "
        f"{'OK' if len(r5) == 0 else 'FALHOU'}")

    print()
    print("=== RESULTADO ESPERADO ===")
    print("machado         → 2  (Dom Casmurro e Memorias Postumas)")
    print("romance         → 2  (Dom Casmurro e Memorias Postumas)")
    print("Machado Romance → 2  (ambos têm machado E romance)")
    print("tolkien fantasia → 1 (O Hobbit)")
    print("tolkien romance  → 0 (nenhum livro tem tolkien E romance)")
