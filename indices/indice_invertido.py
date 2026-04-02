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
        texto = " ".join(
            str(livro.get(campo, "")) for campo in ("titulo", "autor", "genero")
        )
        for token in tokenizar(texto):
            self._indice.setdefault(token, set()).add(numeracao)

    def _remover_livro_interno(self, numeracao: str) -> None:
        """Remove um livro do índice sem alterar a lista de entrada."""
        livro_antigo = self._livros.get(numeracao)
        if not livro_antigo:
            return

        texto = " ".join(
            str(livro_antigo.get(campo, "")) for campo in ("titulo", "autor", "genero")
        )
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

        conjuntos: list[set[str]] = []
        for token in tokens:
            numeros = self._indice.get(token)
            if not numeros:
                return []
            conjuntos.append(set(numeros))

        resultado_numeracoes = set.intersection(*conjuntos) if conjuntos else set()
        return [self._livros[numeracao] for numeracao in sorted(resultado_numeracoes)]

    def buscar_qualquer(self, query: str) -> list[dict]:
        """Retorna livros que contêm ao menos um dos tokens da consulta."""
        tokens = tokenizar(query)
        if not tokens:
            return []

        resultado_numeracoes: set[str] = set()
        for token in tokens:
            numeros = self._indice.get(token)
            if numeros:
                resultado_numeracoes.update(numeros)

        return [self._livros[numeracao] for numeracao in sorted(resultado_numeracoes)]

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
        {"numeracao": "0001", "titulo": "Dom Casmurro", "autor": "Machado de Assis",
         "genero": "Romance", "editora": "Penguin", "quantidade": 3},
        {"numeracao": "0002", "titulo": "Memorias Postumas de Bras Cubas",
         "autor": "Machado de Assis", "genero": "Romance",
         "editora": "Penguin", "quantidade": 2},
        {"numeracao": "0003", "titulo": "O Hobbit", "autor": "J.R.R. Tolkien",
         "genero": "Fantasia", "editora": "Martins Fontes", "quantidade": 5},
        {"numeracao": "0004", "titulo": "Duna", "autor": "Frank Herbert",
         "genero": "Ficcao Cientifica", "editora": "Aleph", "quantidade": 3},
        {"numeracao": "0005", "titulo": "Fundacao", "autor": "Isaac Asimov",
         "genero": "Ficcao Cientifica", "editora": "Aleph", "quantidade": 2},
    ]

    idx = IndiceInvertido()
    idx.construir(livros_teste)

    print("=== Vocabulario (primeiros 10 tokens) ===")
    print(idx.vocabulario()[:10])

    print("\n=== Busca AND: 'machado romance' ===")
    for r in idx.buscar("machado romance"):
        print(f"  {r['numeracao']} - {r['titulo']}")

    print("\n=== Busca OR: 'tolkien asimov' ===")
    for r in idx.buscar_qualquer("tolkien asimov"):
        print(f"  {r['numeracao']} - {r['titulo']}")

    print("\n=== Busca sem resultado: 'xyz123' ===")
    print(f"  Resultados: {len(idx.buscar('xyz123'))}")

    print("\n=== Atualizar livro 0001 e buscar novamente ===")
    idx.atualizar({"numeracao": "0001", "titulo": "Dom Casmurro Especial",
                   "autor": "Machado de Assis", "genero": "Romance Classico",
                   "editora": "Penguin", "quantidade": 5})
    for r in idx.buscar("especial"):
        print(f"  {r['numeracao']} - {r['titulo']}")

    print("\n=== Remover 0003 e verificar ===")
    idx.remover("0003")
    resultado = idx.buscar("tolkien")
    print(f"  Tolkien apos remocao: {len(resultado)} resultado(s)")
