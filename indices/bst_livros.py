"""BST de livros para o sistema de biblioteca."""


class NoLivro:
    """Representa um nó da BST de livros.

    Complexidade: O(1).
    Exemplo: `no = NoLivro({"numeracao": "0042", ...})`.
    """

    def __init__(self, livro: dict):
        self.numeracao = int(livro["numeracao"])
        self.dados = dict(livro)
        self.esq = None
        self.dir = None


class BSTBiblioteca:
    """Árvore Binária de Busca para indexar livros por numeração.

    Complexidade: O(1).
    Exemplo: `bst = BSTBiblioteca()`.
    """

    def __init__(self):
        """Inicializa a BST vazia e zera a contagem de comparações.

        Complexidade de tempo: O(1).
        Exemplo: `bst = BSTBiblioteca()`.
        """
        self.raiz = None
        self.comparacoes = 0

    def inserir(self, livro: dict):
        """Insere ou atualiza um livro na BST pela numeração.

        Complexidade de tempo: O(log n) médio, O(n) pior caso.
        Exemplo: `bst.inserir(livro)`.
        """
        if not livro:
            return

        numeracao = int(livro["numeracao"])

        def _inserir(no, dados):
            if no is None:
                return NoLivro(dados)
            if numeracao < no.numeracao:
                no.esq = _inserir(no.esq, dados)
            elif numeracao > no.numeracao:
                no.dir = _inserir(no.dir, dados)
            else:
                no.dados = dict(dados)
            return no

        self.raiz = _inserir(self.raiz, livro)

    def buscar(self, numeracao: int) -> dict | None:
        """Busca exata de um livro pela numeração.

        Complexidade de tempo: O(log n) médio.
        Exemplo: `livro = bst.buscar(42)`.
        """
        self.comparacoes = 0
        atual = self.raiz

        while atual is not None:
            self.comparacoes += 1
            if numeracao == atual.numeracao:
                return atual.dados
            if numeracao < atual.numeracao:
                atual = atual.esq
            else:
                atual = atual.dir

        return None

    def buscar_intervalo(self, inicio: int, fim: int) -> list[dict]:
        """Retorna livros cuja numeração está entre `inicio` e `fim`.

        Complexidade de tempo: O(log n + k).
        Exemplo: `livros = bst.buscar_intervalo(20, 70)`.
        """
        self.comparacoes = 0
        resultados = []

        def _buscar(no):
            if no is None:
                return

            self.comparacoes += 1

            if no.numeracao > inicio:
                _buscar(no.esq)

            if inicio <= no.numeracao <= fim:
                resultados.append(no.dados)

            if no.numeracao < fim:
                _buscar(no.dir)

        _buscar(self.raiz)
        return resultados

    def remover(self, numeracao: int):
        """Remove um livro da BST usando o sucessor in-order.

        Complexidade de tempo: O(log n) médio.
        Exemplo: `bst.remover(50)`.
        """
        def _minimo(no):
            atual = no
            while atual and atual.esq is not None:
                atual = atual.esq
            return atual

        def _remover(no, chave):
            if no is None:
                return None
            if chave < no.numeracao:
                no.esq = _remover(no.esq, chave)
            elif chave > no.numeracao:
                no.dir = _remover(no.dir, chave)
            else:
                if no.esq is None:
                    return no.dir
                if no.dir is None:
                    return no.esq

                sucessor = _minimo(no.dir)
                no.numeracao = sucessor.numeracao
                no.dados = dict(sucessor.dados)
                no.dir = _remover(no.dir, sucessor.numeracao)
            return no

        self.raiz = _remover(self.raiz, numeracao)

    def em_ordem(self) -> list[dict]:
        """Retorna os livros em ordem crescente de numeração.

        Complexidade de tempo: O(n).
        Exemplo: `ordenados = bst.em_ordem()`.
        """
        resultados = []

        def _em_ordem(no):
            if no is None:
                return
            _em_ordem(no.esq)
            resultados.append(no.dados)
            _em_ordem(no.dir)

        _em_ordem(self.raiz)
        return resultados

    def construir_de_lista(self, livros: list[dict]):
        """Constrói a BST inserindo uma lista de livros.

        Complexidade de tempo: O(n log n) médio.
        Exemplo: `bst.construir_de_lista(livros)`.
        """
        for livro in livros:
            self.inserir(livro)


if __name__ == "__main__":
    livros_teste = [
        {"numeracao": "0050", "titulo": "Duna", "autor": "Frank Herbert",
         "genero": "Ficcao Cientifica", "editora": "Aleph", "quantidade": 3},
        {"numeracao": "0020", "titulo": "1984", "autor": "George Orwell",
         "genero": "Distopia", "editora": "Companhia das Letras", "quantidade": 4},
        {"numeracao": "0080", "titulo": "O Hobbit", "autor": "J.R.R. Tolkien",
         "genero": "Fantasia", "editora": "Martins Fontes", "quantidade": 5},
        {"numeracao": "0010", "titulo": "Dom Casmurro", "autor": "Machado de Assis",
         "genero": "Romance", "editora": "Penguin", "quantidade": 3},
        {"numeracao": "0060", "titulo": "Fundacao", "autor": "Isaac Asimov",
         "genero": "Ficcao Cientifica", "editora": "Aleph", "quantidade": 2},
    ]

    bst = BSTBiblioteca()
    bst.construir_de_lista(livros_teste)

    print("=== Em ordem ===")
    for livro in bst.em_ordem():
        print(f"  {livro['numeracao']} - {livro['titulo']}")

    print("\n=== Busca exata: 0050 ===")
    resultado = bst.buscar(50)
    print(f"  Encontrado: {resultado['titulo'] if resultado else 'Nao encontrado'}")
    print(f"  Comparacoes: {bst.comparacoes}")

    print("\n=== Busca intervalo: 0020 a 0070 ===")
    resultados = bst.buscar_intervalo(20, 70)
    print(f"  {len(resultados)} livros encontrados:")
    for r in resultados:
        print(f"    {r['numeracao']} - {r['titulo']}")
    print(f"  Comparacoes: {bst.comparacoes}")

    print("\n=== Remover 0050 e listar ===")
    bst.remover(50)
    for livro in bst.em_ordem():
        print(f"  {livro['numeracao']} - {livro['titulo']}")