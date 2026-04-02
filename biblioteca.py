import os
import json
import sys
from pathlib import Path
import qdarktheme
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QMainWindow, QCalendarWidget, QVBoxLayout,
    QGridLayout, QFormLayout, QWidget, QFrame,
    QApplication, QPushButton, QLabel, QDialog,
    QLineEdit, QSpinBox, QDateEdit, QListWidget,
    QDialogButtonBox, QMessageBox, QSplitter,
    QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QAbstractItemView
)

CAMINHO_DB_FILES = Path(__file__).parent / "db_files"
IDS_ALUNOS = os.path.join(CAMINHO_DB_FILES, "id_alunos.json")
INFO_ALUNOS = os.path.join(CAMINHO_DB_FILES, "info_alunos.json")
IDS_LIVROS = os.path.join(CAMINHO_DB_FILES, "id_livros.json")
INFO_LIVROS = os.path.join(CAMINHO_DB_FILES, "info_livros.json")
EMPRESTIMOS = os.path.join(CAMINHO_DB_FILES, "emprestimos.json")
ID_EMPRESTIMO = os.path.join(CAMINHO_DB_FILES, "id_emprestimo.json")
HISTORICO_DEVOLUCOES = os.path.join(CAMINHO_DB_FILES, "historico_devolucoes.json")

class Aluno:
    def __init__(self, id, nome, idade, serie, turno, contato, endereco):
        self.id = id
        self.nome = nome.title()
        self.idade = idade
        self.serie = serie
        self.turno = turno.title()
        self.contato = contato
        self.endereco = endereco.title()

class Livro:
    def __init__(self, numeracao, titulo, genero, autor, editora, quantidade):
        self.numeracao = numeracao
        self.titulo = titulo.capitalize()
        self.genero = genero.capitalize()
        self.autor = autor.capitalize()
        self.editora = editora.capitalize()
        self.quantidade = quantidade

class Biblioteca:
    def __init__(self):
        self.id_alunos = self.importacao(IDS_ALUNOS)
        self.info_alunos = self.importacao(INFO_ALUNOS)
        self.id_livros = self.importacao(IDS_LIVROS)
        self.info_livros = self.importacao(INFO_LIVROS)
        self.emprestimos = self.importacao(EMPRESTIMOS)
        self.id_emprestimo = self.importacao(ID_EMPRESTIMO)
        self.historico_devolucoes = self.importacao(HISTORICO_DEVOLUCOES)
        
        # Hooks de índice para implementação futura
        self.bst = None
        self.indice_invertido = None
        self.buscador_fuzzy = None
        self.motor = None
        
        self.inicializar_indices()

    def importacao(self, caminho: str):
        with open(caminho, "r", encoding="utf-8-sig") as arq:
            return json.load(arq)

    def exportacao(self, caminho: str, dados: dict):
        with open(caminho, "w", encoding="utf-8") as arq:
            json.dump(dados, arq, ensure_ascii=False, indent=2)

    def inicializar_indices(self):
        from indices.bst_livros import BSTBiblioteca
        from indices.indice_invertido import IndiceInvertido

        self.bst = BSTBiblioteca()
        livros_lista = list(self.info_livros.values())
        self.bst.construir_de_lista(livros_lista)
        print(f"[BST] Construida com {len(livros_lista)} livros.")

        self.indice_invertido = IndiceInvertido()
        self.indice_invertido.construir(livros_lista)
        print(f"[IndiceInvertido] Vocabulario: {len(self.indice_invertido.vocabulario())} tokens.")

    def cadastra_aluno(self, nome, idade, serie, turno, contato, endereco):
        _id = str(len(self.id_alunos))
        if _id in self.id_alunos:
            return False
        aluno = Aluno(_id, nome, idade, serie, turno, contato, endereco)
        self.id_alunos.append(_id)
        self.info_alunos[_id] = aluno.__dict__
        self.exportacao(IDS_ALUNOS, self.id_alunos)
        self.exportacao(INFO_ALUNOS, self.info_alunos)
        return self.info_alunos[_id]

    def cadastra_livro(self, numeracao, titulo, genero, autor, editora, qtd):
        livro = Livro(numeracao, titulo, genero, autor, editora, int(qtd) if isinstance(qtd, str) else qtd)
        self.info_livros[numeracao] = livro.__dict__
        self.id_livros.append(numeracao)
        self.exportacao(IDS_LIVROS, self.id_livros)
        self.exportacao(INFO_LIVROS, self.info_livros)
        if self.bst:
            self.bst.inserir(self.info_livros[numeracao])
        if self.indice_invertido:
            self.indice_invertido.atualizar(self.info_livros[numeracao])
        return self.info_livros[numeracao]

    def altera_aluno(self, _id, nome, idade, serie, turno, contato, endereco):
        if _id not in self.id_alunos:
            return None
        aluno = Aluno(_id, nome, idade, serie, turno, contato, endereco)
        self.info_alunos[_id] = aluno.__dict__
        self.exportacao(INFO_ALUNOS, self.info_alunos)
        return self.info_alunos[_id]

    def altera_livro(self, numeracao, titulo, genero, autor, editora, qtd):
        if numeracao not in self.id_livros:
            return None
        livro = Livro(numeracao, titulo, genero, autor, editora, qtd)
        self.info_livros[numeracao] = livro.__dict__
        self.exportacao(INFO_LIVROS, self.info_livros)
        if self.bst:
            self.bst.inserir(self.info_livros[numeracao])
        if self.indice_invertido:
            self.indice_invertido.atualizar(self.info_livros[numeracao])
        return self.info_livros[numeracao]

    def fazer_emprestimo(self, _id, livro, devo):
        chave = str(datetime.now().microsecond)
        self.emprestimos[chave] = {
            "aluno": self.info_alunos[_id],
            "livro": livro.title(),
            "devolucao": devo
        }
        self.id_emprestimo[chave] = _id
        self.exportacao(EMPRESTIMOS, self.emprestimos)
        self.exportacao(ID_EMPRESTIMO, self.id_emprestimo)
        return chave, self.emprestimos[chave]

    def fazer_devolucao(self, chave):
        emprestimo = self.emprestimos.get(chave)
        if not emprestimo:
            return

        # Busca nome do aluno
        aluno_info = emprestimo.get("aluno", {})
        if isinstance(aluno_info, dict):
            nome_aluno = aluno_info.get("nome", "Desconhecido")
        else:
            nome_aluno = str(aluno_info)

        # Salva no histórico de devoluções
        chave_devolucao = f"DEV-{chave}"
        self.historico_devolucoes[chave_devolucao] = {
            "chave_emprestimo": chave,
            "livro": emprestimo.get("livro", ""),
            "aluno": nome_aluno,
            "data_devolucao": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        self.exportacao(HISTORICO_DEVOLUCOES, self.historico_devolucoes)

        # Remove o empréstimo ativo
        self.emprestimos.pop(chave)
        self.id_emprestimo.pop(chave)
        self.exportacao(EMPRESTIMOS, self.emprestimos)
        self.exportacao(ID_EMPRESTIMO, self.id_emprestimo)

class JanelaPrincipal(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sistema de Biblioteca")
        
        # Instancia biblioteca
        self.b1 = Biblioteca()
        
        # Cria janelas secundárias
        self.janelaCA = JanelaCadastraAluno(self.b1)
        self.janelaCL = JanelaCadastroLivro(self.b1)
        self.janelaAA = JanelaAteraAluno(self.b1)
        self.janelaAL = JanelaAlteraLivro(self.b1)
        self.janelaEP = JanelaEmprestimo(self.b1)
        self.janelaDV = JanelaDevolucao(self.b1)
        
        # Cria layout principal com splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Cria sidebar (painel esquerdo)
        self.sidebar = self._criar_sidebar()
        
        # Cria stacked widget para os painéis (painel direito)
        self.stacked = QStackedWidget()
        self.painel_acervo = self._criar_painel_acervo()
        self.painel_alunos = self._criar_painel_alunos()
        self.painel_emprestimos = self._criar_painel_emprestimos()
        self.painel_devolucoes = self._criar_painel_devolucoes()
        
        self.stacked.addWidget(self.painel_acervo)        # 0
        self.stacked.addWidget(self.painel_alunos)        # 1
        self.stacked.addWidget(self.painel_emprestimos)   # 2
        self.stacked.addWidget(self.painel_devolucoes)    # 3
        
        # Adiciona sidebar e stacked ao splitter
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.stacked)
        self.splitter.setSizes([220, 1280])
        
        self.setCentralWidget(self.splitter)
        self.config_style()
        self._conectar_atualizacao_dialogos()
        self._atualizar_tabela_acervo()
        self._atualizar_tabela_alunos()
        self._atualizar_tabela_emprestimos()
        self._atualizar_cards()
    
    def _criar_sidebar(self) -> QFrame:
        """Cria sidebar com navegação"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo real do sistema
        logo_label = QLabel()
        pixmap = QPixmap("img/logo.png")
        pixmap = pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        # Texto abaixo da logo
        
        separador1 = QFrame()
        separador1.setFrameShape(QFrame.HLine)
        separador1.setStyleSheet("background: rgba(173, 73, 225, 0.2);")
        layout.addWidget(separador1)
        
        # Seção ACERVO
        secao_acervo = QLabel("ACERVO")
        secao_acervo.setObjectName("section-label")
        secao_acervo.setStyleSheet(
            "color: rgba(173, 73, 225, 0.45); font-size: 10px; "
            "letter-spacing: 2px; padding: 12px 16px 4px; font-weight: bold;"
        )
        layout.addWidget(secao_acervo)
        
        # Botões de navegação ACERVO
        self.btn_acervo = self._criar_botao_nav("📚 Acervo de Livros", True)
        self.btn_acervo.clicked.connect(lambda: self._switch_panel(0, self.btn_acervo))
        layout.addWidget(self.btn_acervo)
        
        self.btn_alunos = self._criar_botao_nav("👥 Alunos")
        self.btn_alunos.clicked.connect(lambda: self._switch_panel(1, self.btn_alunos))
        layout.addWidget(self.btn_alunos)
        
        self.btn_emprestimos = self._criar_botao_nav("📤 Empréstimos")
        self.btn_emprestimos.clicked.connect(lambda: self._switch_panel(2, self.btn_emprestimos))
        layout.addWidget(self.btn_emprestimos)
        
        self.btn_devolucoes = self._criar_botao_nav("📥 Devoluções")
        self.btn_devolucoes.clicked.connect(lambda: self._switch_panel(3, self.btn_devolucoes))
        layout.addWidget(self.btn_devolucoes)
        
        self.nav_buttons = [self.btn_acervo, self.btn_alunos, self.btn_emprestimos, self.btn_devolucoes]
        
        separador2 = QFrame()
        separador2.setFrameShape(QFrame.HLine)
        separador2.setStyleSheet("background: rgba(173, 73, 225, 0.2); margin: 8px 0;")
        layout.addWidget(separador2)
        
        # Seção CADASTRO
        secao_cadastro = QLabel("CADASTRO")
        secao_cadastro.setObjectName("section-label")
        secao_cadastro.setStyleSheet(
            "color: rgba(173, 73, 225, 0.45); font-size: 10px; "
            "letter-spacing: 2px; padding: 12px 16px 4px; font-weight: bold;"
        )
        layout.addWidget(secao_cadastro)
        
        btn_novo_livro = self._criar_botao_nav("➕ Novo Livro")
        btn_novo_livro.clicked.connect(self.janelaCL.show)
        layout.addWidget(btn_novo_livro)
        
        btn_novo_aluno = self._criar_botao_nav("➕ Novo Aluno")
        btn_novo_aluno.clicked.connect(self.janelaCA.show)
        layout.addWidget(btn_novo_aluno)
        
        layout.addStretch()
        
        return sidebar
    
    def _criar_botao_nav(self, texto: str, ativo: bool = False) -> QPushButton:
        """Cria um botão de navegação da sidebar"""
        btn = QPushButton(texto)
        btn.setObjectName("nav-btn")
        btn.setProperty("active", ativo)
        btn.setFlat(True)
        btn.setStyleSheet(
            """
            QPushButton#nav-btn {
                background: transparent;
                border: none;
                border-left: 2px solid transparent;
                padding: 9px 16px 9px 14px;
                text-align: left;
                color: rgba(255,255,255,0.55);
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#nav-btn:hover {
                background: rgba(173, 73, 225, 0.08);
                color: rgba(255,255,255,0.85);
            }
            QPushButton#nav-btn[active="true"] {
                background: rgba(173, 73, 225, 0.12);
                border-left: 2px solid #AD49E1;
                color: #c97ff0;
            }
            """
        )
        return btn
    
    def _switch_panel(self, index: int, btn: QPushButton):
        """Troca entre painéis e atualiza estilo do botão"""
        # Desativa todos os botões
        for b in self.nav_buttons:
            b.setProperty("active", False)
            b.style().unpolish(b)
            b.style().polish(b)
        
        # Ativa botão clicado
        btn.setProperty("active", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        
        # Troca painel
        self.stacked.setCurrentIndex(index)
        
        # Recarrega dados se necessário
        if index == 0:
            self._atualizar_tabela_acervo()
        elif index == 1:
            self._atualizar_tabela_alunos()
        elif index == 2:
            self._atualizar_tabela_emprestimos()
        elif index == 3:
            self._atualizar_tabela_devolucoes()
        self._atualizar_cards()
    
    def _criar_painel_acervo(self) -> QWidget:
        """Cria painel de acervo de livros"""
        painel = QWidget()
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Cards de métricas
        metrics_layout = QHBoxLayout()
        self.card_livros = self._criar_metric_card("LIVROS NO\nACERVO", "0", "Total de livros cadastrados")
        self.card_emprestimos = self._criar_metric_card("EMPRÉSTIMOS\nATIVOS", "0", "Livros em circulação")
        self.card_alunos = self._criar_metric_card("ALUNOS\nCADASTRADOS", "0", "Total de alunos")
        self.card_disponiveis = self._criar_metric_card("DISPONÍVEIS\nAGORA", "0", "Prontos para empréstimo")
        self.card_livros_label = self.card_livros.valor_label
        self.card_emprestimos_label = self.card_emprestimos.valor_label
        self.card_alunos_label = self.card_alunos.valor_label
        self.card_disponiveis_label = self.card_disponiveis.valor_label
        
        metrics_layout.addWidget(self.card_livros)
        metrics_layout.addWidget(self.card_emprestimos)
        metrics_layout.addWidget(self.card_alunos)
        metrics_layout.addWidget(self.card_disponiveis)
        layout.addLayout(metrics_layout)
        
        # Barra de busca
        busca_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search-bar")
        self.search_bar.setPlaceholderText(
            "Buscar por título, autor, gênero ou numeração (ex: tolkien · 0016 · 10-20)…"
        )
        self.search_bar.setFixedHeight(40)
        
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setFixedWidth(100)
        btn_buscar.clicked.connect(self._buscar_livros)
        self.search_bar.returnPressed.connect(self._buscar_livros)
        
        busca_layout.addWidget(self.search_bar)
        busca_layout.addWidget(btn_buscar)
        layout.addLayout(busca_layout)
        
        # Status da busca
        self.status_label = QLabel()
        self.status_label.setObjectName("status-bar")
        self.status_label.setVisible(False)
        self.status_label.setStyleSheet(
            "background: rgba(173, 73, 225, 0.08); border: 1px solid rgba(173, 73, 225, 0.2); "
            "border-radius: 6px; padding: 5px 12px; color: rgba(255,255,255,0.6); font-size: 12px;"
        )
        layout.addWidget(self.status_label)
        
        # Filtros rápidos
        filtros_layout = QHBoxLayout()
        self.label_filtros = QLabel("Filtros:")
        self.label_filtros.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 13px; font-weight: 500;")
        filtros_layout.addWidget(self.label_filtros)
        
        self.btn_todos = QPushButton("Todos")
        self.btn_todos.setCheckable(True)
        self.btn_todos.setChecked(True)
        self.btn_todos.clicked.connect(lambda: self._filtrar_livros("todos"))
        filtros_layout.addWidget(self.btn_todos)
        
        self.btn_disponiveis = QPushButton("Disponíveis")
        self.btn_disponiveis.setCheckable(True)
        self.btn_disponiveis.clicked.connect(lambda: self._filtrar_livros("disponiveis"))
        filtros_layout.addWidget(self.btn_disponiveis)
        
        filtros_layout.addStretch()
        layout.addLayout(filtros_layout)
        
        # Tabela de livros
        self.table_livros = QTableWidget()
        self.table_livros.setColumnCount(6)
        self.table_livros.setHorizontalHeaderLabels(
            ["Num.", "Título", "Autor", "Gênero", "Qtd.", "Ações"]
        )
        self.table_livros.setColumnWidth(0, 70)
        self.table_livros.setColumnWidth(1, 300)
        self.table_livros.setColumnWidth(2, 160)
        self.table_livros.setColumnWidth(3, 120)
        self.table_livros.setColumnWidth(4, 70)
        self.table_livros.setColumnWidth(5, 180)
        self.table_livros.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)

        self.table_livros.setAlternatingRowColors(False)
        self.table_livros.setStyleSheet(
            """
            QTableWidget { background-color: #1a1a2e; }
            QTableWidget::item { background-color: #1a1a2e; color: #e0e0e0; }
            QTableWidget::item:selected { background-color: rgba(173,73,225,0.25); color: #ffffff; }
            QTableWidget::item:hover { background-color: rgba(173,73,225,0.1); }
            """
        )
        self.table_livros.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_livros.horizontalHeader().setStretchLastSection(False)
        layout.addWidget(self.table_livros)
        
        return painel
    
    def _criar_painel_alunos(self) -> QWidget:
        """Cria painel de alunos"""
        painel = QWidget()
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Barra de busca
        busca_layout = QHBoxLayout()
        self.search_alunos = QLineEdit()
        self.search_alunos.setObjectName("search-bar")
        self.search_alunos.setPlaceholderText("Buscar aluno por nome ou ID…")
        self.search_alunos.setFixedHeight(40)
        
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setFixedWidth(100)
        btn_buscar.clicked.connect(self._buscar_alunos)
        self.search_alunos.returnPressed.connect(self._buscar_alunos)
        
        busca_layout.addWidget(self.search_alunos)
        busca_layout.addWidget(btn_buscar)
        layout.addLayout(busca_layout)
        
        # Tabela de alunos
        self.table_alunos = QTableWidget()
        self.table_alunos.setColumnCount(7)
        self.table_alunos.setHorizontalHeaderLabels(
            ["ID", "Nome", "Série", "Turno", "Contato", "Endereço", "Ações"]
        )
        self.table_alunos.setColumnWidth(0, 60)
        self.table_alunos.setColumnWidth(1, 200)
        self.table_alunos.setColumnWidth(2, 80)
        self.table_alunos.setColumnWidth(3, 100)
        self.table_alunos.setColumnWidth(4, 150)
        self.table_alunos.setColumnWidth(5, 200)
        self.table_alunos.setColumnWidth(6, 180)
        self.table_alunos.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        
        self.table_alunos.setAlternatingRowColors(False)
        self.table_alunos.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table_alunos)
        
        return painel
    
    def _criar_painel_emprestimos(self) -> QWidget:
        """Cria painel de empréstimos"""
        painel = QWidget()
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        titulo = QLabel("EMPRÉSTIMOS ATIVOS")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(titulo)
        
        # Tabela de empréstimos
        self.table_emprestimos = QTableWidget()
        self.table_emprestimos.setColumnCount(5)
        self.table_emprestimos.setHorizontalHeaderLabels(
            ["Chave", "Aluno", "Livro", "Devolução", "Ações"]
        )
        self.table_emprestimos.setColumnWidth(0, 100)
        self.table_emprestimos.setColumnWidth(1, 200)
        self.table_emprestimos.setColumnWidth(2, 250)
        self.table_emprestimos.setColumnWidth(3, 150)
        self.table_emprestimos.setColumnWidth(4, 180)
        self.table_emprestimos.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.table_emprestimos.setAlternatingRowColors(False)
        self.table_emprestimos.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table_emprestimos)
        
        layout.addStretch()
        return painel
    
    def _criar_painel_devolucoes(self) -> QWidget:
        painel = QWidget()
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        titulo = QLabel("HISTÓRICO DE DEVOLUÇÕES")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(titulo)

        self.table_devolucoes = QTableWidget()
        self.table_devolucoes.setColumnCount(4)
        self.table_devolucoes.setHorizontalHeaderLabels(
            ["Chave Devolução", "Livro", "Aluno", "Data de Devolução"]
        )
        self.table_devolucoes.setColumnWidth(0, 150)
        self.table_devolucoes.setColumnWidth(1, 280)
        self.table_devolucoes.setColumnWidth(2, 200)
        self.table_devolucoes.setColumnWidth(3, 180)
        self.table_devolucoes.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_devolucoes.setAlternatingRowColors(False)
        self.table_devolucoes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_devolucoes.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout.addWidget(self.table_devolucoes)
        return painel
    
    def _criar_metric_card(self, titulo: str, valor: str, subtitulo: str) -> QFrame:
        """Cria um card de métrica"""
        card = QFrame()
        card.setObjectName("metric-card")
        card.setStyleSheet(
            "background: rgba(255,255,255,0.04); border: 1px solid rgba(173, 73, 225, 0.15); "
            "border-radius: 8px; padding: 12px;"
        )
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet(
            "font-size: 11px; color: rgba(173, 73, 225, 0.6); letter-spacing: 0.5px; font-weight: bold;"
        )
        layout.addWidget(titulo_label)
        
        valor_label = QLabel(valor)
        valor_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(valor_label)
        
        subtitulo_label = QLabel(subtitulo)
        subtitulo_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.5);")
        layout.addWidget(subtitulo_label)
        
        # Armazenar labels para atualização
        card.titulo_label = titulo_label
        card.valor_label = valor_label
        card.subtitulo_label = subtitulo_label
        
        return card
    
    def _atualizar_tabela_acervo(self):
        """Atualiza a tabela de acervo"""
        self.table_livros.setRowCount(0)
        
        for numeracao, livro in self.b1.info_livros.items():
            row = self.table_livros.rowCount()
            self.table_livros.insertRow(row)
            
            if isinstance(livro, dict):
                item_num = QTableWidgetItem(str(livro.get("numeracao", "")))
                item_num.setForeground(Qt.white)
                item_num.setTextAlignment(Qt.AlignCenter)
                self.table_livros.setItem(row, 0, item_num)

                item_titulo = QTableWidgetItem(str(livro.get("titulo", "")))
                item_titulo.setForeground(Qt.white)
                item_titulo.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table_livros.setItem(row, 1, item_titulo)

                item_autor = QTableWidgetItem(str(livro.get("autor", "")))
                item_autor.setForeground(Qt.white)
                item_autor.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table_livros.setItem(row, 2, item_autor)

                item_genero = QTableWidgetItem(str(livro.get("genero", "")))
                item_genero.setForeground(Qt.white)
                item_genero.setTextAlignment(Qt.AlignCenter)
                self.table_livros.setItem(row, 3, item_genero)

                item_qtd = QTableWidgetItem(str(livro.get("quantidade", "")))
                item_qtd.setForeground(Qt.white)
                item_qtd.setTextAlignment(Qt.AlignCenter)
                self.table_livros.setItem(row, 4, item_qtd)
                
                # Botões de ação
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(4, 2, 4, 2)
                btn_layout.setSpacing(6)
                
                btn_emprestar = QPushButton("Emprestar")
                btn_emprestar.setFixedWidth(88)
                btn_emprestar.clicked.connect(
                    lambda checked, n=numeracao: self._abrir_emprestimo(n)
                )
                
                btn_editar = QPushButton("Editar")
                btn_editar.setFixedWidth(72)
                btn_editar.clicked.connect(
                    lambda checked, n=numeracao: self._abrir_altera_livro(n)
                )
                
                btn_layout.addWidget(btn_emprestar)
                btn_layout.addWidget(btn_editar)
                
                self.table_livros.setCellWidget(row, 5, btn_container)

            self._atualizar_cards()
    
    def _atualizar_tabela_alunos(self):
        """Atualiza a tabela de alunos"""
        self.table_alunos.setRowCount(0)
        
        for aluno_id, aluno in self.b1.info_alunos.items():
            row = self.table_alunos.rowCount()
            self.table_alunos.insertRow(row)
            
            if isinstance(aluno, dict):
                item_id = QTableWidgetItem(str(aluno_id))
                item_id.setForeground(Qt.white)
                self.table_alunos.setItem(row, 0, item_id)
                item_nome = QTableWidgetItem(str(aluno.get("nome", "")))
                item_nome.setForeground(Qt.white)
                self.table_alunos.setItem(row, 1, item_nome)
                item_serie = QTableWidgetItem(str(aluno.get("serie", "")))
                item_serie.setForeground(Qt.white)
                self.table_alunos.setItem(row, 2, item_serie)
                item_turno = QTableWidgetItem(str(aluno.get("turno", "")))
                item_turno.setForeground(Qt.white)
                self.table_alunos.setItem(row, 3, item_turno)
                item_contato = QTableWidgetItem(str(aluno.get("contato", "")))
                item_contato.setForeground(Qt.white)
                self.table_alunos.setItem(row, 4, item_contato)
                item_endereco = QTableWidgetItem(str(aluno.get("endereco", "")))
                item_endereco.setForeground(Qt.white)
                self.table_alunos.setItem(row, 5, item_endereco)
                
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                btn_editar = QPushButton("Editar")
                btn_editar.setFixedWidth(70)
                btn_editar.clicked.connect(
                    lambda checked, aid=aluno_id: self._abrir_altera_aluno(aid)
                )
                
                btn_layout.addWidget(btn_editar)
                self.table_alunos.setCellWidget(row, 6, btn_container)
    
    def _atualizar_tabela_emprestimos(self):
        """Atualiza a tabela de empréstimos"""
        self.table_emprestimos.setRowCount(0)
        
        for chave, emprestimo in self.b1.emprestimos.items():
            row = self.table_emprestimos.rowCount()
            self.table_emprestimos.insertRow(row)
            
            if isinstance(emprestimo, dict):
                item_chave = QTableWidgetItem(str(chave))
                item_chave.setForeground(Qt.white)
                self.table_emprestimos.setItem(row, 0, item_chave)
                
                aluno_info = emprestimo.get("aluno", {})
                if isinstance(aluno_info, dict):
                    aluno_nome = aluno_info.get("nome", "N/A")
                else:
                    aluno_nome = str(aluno_info)
                item_aluno = QTableWidgetItem(aluno_nome)
                item_aluno.setForeground(Qt.white)
                self.table_emprestimos.setItem(row, 1, item_aluno)
                
                item_livro = QTableWidgetItem(str(emprestimo.get("livro", "")))
                item_livro.setForeground(Qt.white)
                self.table_emprestimos.setItem(row, 2, item_livro)
                item_devolucao = QTableWidgetItem(str(emprestimo.get("devolucao", "")))
                item_devolucao.setForeground(Qt.white)
                self.table_emprestimos.setItem(row, 3, item_devolucao)
                
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                btn_devolver = QPushButton("Devolver")
                btn_devolver.setFixedWidth(70)
                btn_devolver.clicked.connect(
                    lambda checked, c=chave: self._fazer_devolucao(c)
                )
                
                btn_layout.addWidget(btn_devolver)
                self.table_emprestimos.setCellWidget(row, 4, btn_container)

    def _atualizar_tabela_devolucoes(self):
        self.table_devolucoes.setRowCount(0)
        for chave_dev, registro in self.b1.historico_devolucoes.items():
            row = self.table_devolucoes.rowCount()
            self.table_devolucoes.insertRow(row)

            item_chave = QTableWidgetItem(str(chave_dev))
            item_chave.setForeground(Qt.white)
            self.table_devolucoes.setItem(row, 0, item_chave)

            item_livro = QTableWidgetItem(str(registro.get("livro", "")))
            item_livro.setForeground(Qt.white)
            self.table_devolucoes.setItem(row, 1, item_livro)

            item_aluno = QTableWidgetItem(str(registro.get("aluno", "")))
            item_aluno.setForeground(Qt.white)
            self.table_devolucoes.setItem(row, 2, item_aluno)

            item_data = QTableWidgetItem(str(registro.get("data_devolucao", "")))
            item_data.setForeground(Qt.white)
            self.table_devolucoes.setItem(row, 3, item_data)
    
    def _atualizar_cards(self):
        total_livros = len(self.b1.info_livros)
        emprestimos_ativos = len(self.b1.emprestimos)
        total_alunos = len(self.b1.info_alunos)
        disponiveis = sum(
            int(dados.get("quantidade", 0))
            for dados in self.b1.info_livros.values()
            if isinstance(dados, dict)
        )
        self.card_livros_label.setText(str(total_livros))
        self.card_emprestimos_label.setText(str(emprestimos_ativos))
        self.card_alunos_label.setText(str(total_alunos))
        self.card_disponiveis_label.setText(str(disponiveis))

    def _conectar_atualizacao_dialogos(self):
        self.janelaCA.finished.connect(self._atualizar_interface_dados)
        self.janelaCL.finished.connect(self._atualizar_interface_dados)
        self.janelaAA.finished.connect(self._atualizar_interface_dados)
        self.janelaAL.finished.connect(self._atualizar_interface_dados)
        self.janelaEP.finished.connect(self._atualizar_interface_dados)
        self.janelaDV.finished.connect(self._atualizar_interface_dados)

    def _atualizar_interface_dados(self):
        self._atualizar_tabela_acervo()
        self._atualizar_tabela_alunos()
        self._atualizar_tabela_emprestimos()
        self._atualizar_cards()
        self._atualizar_tabela_devolucoes()
    
    def _buscar_livros(self):
        """Busca livros por substring (busca placeholder)"""
        query = self.search_bar.text().lower()
        
        if not query:
            self._atualizar_tabela_acervo()
            self.status_label.setVisible(False)
            return
        
        # Busca sequencial simples
        resultados = []
        for numeracao, livro in self.b1.info_livros.items():
            if isinstance(livro, dict):
                titulo = str(livro.get("titulo", "")).lower()
                autor = str(livro.get("autor", "")).lower()
                genero = str(livro.get("genero", "")).lower()
                num = str(livro.get("numeracao", "")).lower()
                
                if query in titulo or query in autor or query in genero or query in num:
                    resultados.append((numeracao, livro))
        
        # Mostra resultados
        self.table_livros.setRowCount(0)
        for numeracao, livro in resultados:
            row = self.table_livros.rowCount()
            self.table_livros.insertRow(row)
            
            item_num = QTableWidgetItem(str(livro.get("numeracao", "")))
            item_num.setForeground(Qt.white)
            item_num.setTextAlignment(Qt.AlignCenter)
            self.table_livros.setItem(row, 0, item_num)

            item_titulo = QTableWidgetItem(str(livro.get("titulo", "")))
            item_titulo.setForeground(Qt.white)
            item_titulo.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table_livros.setItem(row, 1, item_titulo)

            item_autor = QTableWidgetItem(str(livro.get("autor", "")))
            item_autor.setForeground(Qt.white)
            item_autor.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table_livros.setItem(row, 2, item_autor)

            item_genero = QTableWidgetItem(str(livro.get("genero", "")))
            item_genero.setForeground(Qt.white)
            item_genero.setTextAlignment(Qt.AlignCenter)
            self.table_livros.setItem(row, 3, item_genero)

            item_qtd = QTableWidgetItem(str(livro.get("quantidade", "")))
            item_qtd.setForeground(Qt.white)
            item_qtd.setTextAlignment(Qt.AlignCenter)
            self.table_livros.setItem(row, 4, item_qtd)
            
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)
            
            btn_emprestar = QPushButton("Emprestar")
            btn_emprestar.setFixedWidth(88)
            btn_emprestar.clicked.connect(lambda checked, n=numeracao: self._abrir_emprestimo(n))
            
            btn_editar = QPushButton("Editar")
            btn_editar.setFixedWidth(72)
            btn_editar.clicked.connect(lambda checked, n=numeracao: self._abrir_altera_livro(n))
            
            btn_layout.addWidget(btn_emprestar)
            btn_layout.addWidget(btn_editar)
            self.table_livros.setCellWidget(row, 5, btn_container)
        
        # Mostra status
        self.status_label.setText(f" Listagem completa · {len(resultados)} resultado(s)")
        self.status_label.setVisible(True)
    
    def _buscar_alunos(self):
        """Busca alunos por nome ou ID"""
        query = self.search_alunos.text().lower()
        
        self.table_alunos.setRowCount(0)
        
        for aluno_id, aluno in self.b1.info_alunos.items():
            if isinstance(aluno, dict):
                nome = str(aluno.get("nome", "")).lower()
                aid = str(aluno_id).lower()
                
                if not query or query in nome or query in aid:
                    row = self.table_alunos.rowCount()
                    self.table_alunos.insertRow(row)
                    
                    item_id = QTableWidgetItem(str(aluno_id))
                    item_id.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 0, item_id)
                    item_nome = QTableWidgetItem(str(aluno.get("nome", "")))
                    item_nome.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 1, item_nome)
                    item_serie = QTableWidgetItem(str(aluno.get("serie", "")))
                    item_serie.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 2, item_serie)
                    item_turno = QTableWidgetItem(str(aluno.get("turno", "")))
                    item_turno.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 3, item_turno)
                    item_contato = QTableWidgetItem(str(aluno.get("contato", "")))
                    item_contato.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 4, item_contato)
                    item_endereco = QTableWidgetItem(str(aluno.get("endereco", "")))
                    item_endereco.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 5, item_endereco)
                    
                    btn_container = QWidget()
                    btn_layout = QHBoxLayout(btn_container)
                    btn_layout.setContentsMargins(2, 2, 2, 2)
                    
                    btn_editar = QPushButton("Editar")
                    btn_editar.setFixedWidth(70)
                    btn_editar.clicked.connect(lambda checked, aid=aluno_id: self._abrir_altera_aluno(aid))
                    
                    btn_layout.addWidget(btn_editar)
                    self.table_alunos.setCellWidget(row, 6, btn_container)
    
    def _filtrar_livros(self, filtro: str):
        """Filtra a tabela de livros"""
        self.search_bar.clear()
        self.status_label.setVisible(False)
        
        # Desmarca todos os filtros
        self.btn_todos.setChecked(filtro == "todos")
        self.btn_disponiveis.setChecked(filtro == "disponiveis")
        
        self.table_livros.setRowCount(0)
        
        for numeracao, livro in self.b1.info_livros.items():
            if isinstance(livro, dict):
                if filtro == "todos":
                    incluir = True
                elif filtro == "disponiveis":
                    incluir = livro.get("quantidade", 0) > 0
                else:
                    incluir = True
                
                if incluir:
                    row = self.table_livros.rowCount()
                    self.table_livros.insertRow(row)
                    
                    item_num = QTableWidgetItem(str(livro.get("numeracao", "")))
                    item_num.setForeground(Qt.white)
                    item_num.setTextAlignment(Qt.AlignCenter)
                    self.table_livros.setItem(row, 0, item_num)

                    item_titulo = QTableWidgetItem(str(livro.get("titulo", "")))
                    item_titulo.setForeground(Qt.white)
                    item_titulo.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.table_livros.setItem(row, 1, item_titulo)

                    item_autor = QTableWidgetItem(str(livro.get("autor", "")))
                    item_autor.setForeground(Qt.white)
                    item_autor.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.table_livros.setItem(row, 2, item_autor)

                    item_genero = QTableWidgetItem(str(livro.get("genero", "")))
                    item_genero.setForeground(Qt.white)
                    item_genero.setTextAlignment(Qt.AlignCenter)
                    self.table_livros.setItem(row, 3, item_genero)

                    item_qtd = QTableWidgetItem(str(livro.get("quantidade", "")))
                    item_qtd.setForeground(Qt.white)
                    item_qtd.setTextAlignment(Qt.AlignCenter)
                    self.table_livros.setItem(row, 4, item_qtd)
                    
                    btn_container = QWidget()
                    btn_layout = QHBoxLayout(btn_container)
                    btn_layout.setContentsMargins(4, 2, 4, 2)
                    btn_layout.setSpacing(6)
                    
                    btn_emprestar = QPushButton("Emprestar")
                    btn_emprestar.setFixedWidth(88)
                    btn_emprestar.clicked.connect(lambda checked, n=numeracao: self._abrir_emprestimo(n))
                    
                    btn_editar = QPushButton("Editar")
                    btn_editar.setFixedWidth(72)
                    btn_editar.clicked.connect(lambda checked, n=numeracao: self._abrir_altera_livro(n))
                    
                    btn_layout.addWidget(btn_emprestar)
                    btn_layout.addWidget(btn_editar)
                    self.table_livros.setCellWidget(row, 5, btn_container)
    
    def _abrir_emprestimo(self, numeracao: str):
        """Abre janela de empréstimo com livro pré-preenchido"""
        livro = self.b1.info_livros.get(numeracao)
        if isinstance(livro, dict):
            self.janelaEP.livro.setText(livro.get("titulo", ""))
        self.janelaEP.show()
    
    def _abrir_altera_livro(self, numeracao: str):
        """Abre janela de alteração de livro com dados pré-preenchidos"""
        livro = self.b1.info_livros.get(numeracao)
        if isinstance(livro, dict):
            # Preencher campos (precisa acessar campos da janela)
            # Para agora, apenas abre a janela
            pass
        self.janelaAL.show()
    
    def _abrir_altera_aluno(self, aluno_id: str):
        """Abre janela de alteração de aluno"""
        self.janelaAA.show()
    
    def _fazer_devolucao(self, chave: str):
        """Faz a devolução de um livro"""
        try:
            self.b1.fazer_devolucao(chave)
            faz_msg_box("Sucesso", "Devolução realizada com sucesso!", False)
            self._atualizar_tabela_emprestimos()
            self._atualizar_tabela_devolucoes()
            self._atualizar_cards()
        except KeyError:
            faz_msg_box("Erro", "Chave de empréstimo não encontrada!", True)
    
    def config_style(self):
        """Configura o estilo visual"""
        screen = QApplication.primaryScreen()
        screen_size = screen.size()

        self.resize(int(screen_size.width() * 0.95), int(screen_size.height() * 0.95))
        self.showMaximized()

        # Tema escuro roxo
        STYLESHEET = """
        QMainWindow, QDialog {
            background-color: #1a1a2e;
        }
        QFrame#sidebar {
            background-color: #12122a;
            border-right: 1px solid rgba(173, 73, 225, 0.2);
        }
        QPushButton#nav-btn {
            background: transparent;
            border: none;
            border-left: 2px solid transparent;
            padding: 9px 16px 9px 14px;
            text-align: left;
            color: rgba(255,255,255,0.55);
            font-size: 13px;
        }
        QPushButton#nav-btn:hover {
            background: rgba(173, 73, 225, 0.08);
            color: rgba(255,255,255,0.85);
        }
        QPushButton#nav-btn[active="true"] {
            background: rgba(173, 73, 225, 0.12);
            border-left: 2px solid #AD49E1;
            color: #c97ff0;
        }
        QFrame#metric-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(173, 73, 225, 0.15);
            border-radius: 8px;
            padding: 12px;
        }
        QTableWidget {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(173, 73, 225, 0.12);
            border-radius: 8px;
            gridline-color: rgba(255,255,255,0.04);
        }
        QTableWidget::item:selected {
            background: rgba(173, 73, 225, 0.2);
        }
        QHeaderView::section {
            background: rgba(173, 73, 225, 0.07);
            color: rgba(120, 30, 170, 1.0);
            font-size: 10px;
            letter-spacing: 1px;
            border: none;
            padding: 6px 8px;
        }
        QLineEdit#search-bar {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(173, 73, 225, 0.3);
            border-radius: 8px;
            padding: 9px 14px 9px 14px;
            color: #e0e0e0;
            font-size: 13px;
        }
        QLabel#status-bar {
            background: rgba(173, 73, 225, 0.08);
            border: 1px solid rgba(173, 73, 225, 0.2);
            border-radius: 6px;
            padding: 5px 12px;
            color: rgba(255,255,255,0.6);
            font-size: 12px;
        }
        QLabel#section-label {
            color: rgba(173, 73, 225, 0.45);
            font-size: 10px;
            letter-spacing: 2px;
            padding: 12px 16px 4px;
        }
        QPushButton {
            background: rgba(173, 73, 225, 0.2);
            color: #e0e0e0;
            border: 1px solid rgba(173, 73, 225, 0.3);
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: 500;
        }
        QPushButton:hover {
            background: rgba(173, 73, 225, 0.3);
        }
        QPushButton:pressed {
            background: rgba(173, 73, 225, 0.4);
        }
        """

        STYLESHEET += """
        QTableWidget {
            color: #e0e0e0;
        }
        QTableWidgetItem {
            color: #e0e0e0;
        }
        """
        
        self.setStyleSheet(STYLESHEET)


class JanelaCadastraAluno(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)

        self.setWindowTitle("Cadastro de Aluno")
        self.setMinimumSize(900, 350)
        self.layoutca = QFormLayout()
        self.setLayout(self.layoutca)

        self.campo_texto = [nome := QLineEdit(), idade := QSpinBox(),
                            serie := QLineEdit(), turno := QLineEdit(),
                            contato := QLineEdit(), endereco := QLineEdit()]
        self.titulos = ["Nome Aluno", "Idade", "Série", "Turno", "Contato", "Endereço"]

        for titulo, campo in zip(self.titulos, self.campo_texto):
            self.layoutca.addRow(titulo, campo)

        self.botoes_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.layoutca.addWidget(self.botoes_box)

        self.botoes_box.accepted.connect(self.faz_slot(
            biblioteca.cadastra_aluno,
            nome, idade, serie,
            turno, contato, endereco
        ))

        self.botoes_box.rejected.connect(self.reject)

    def faz_slot(self, func, *args):
        def slot():
            n, i, s, t, c, e = args
            if self.verifica_campos(n, i, s, t, c, e):
                msg = func(n.text(), str(i.value()), s.text(), t.text(), c.text(), e.text())
                for b in args:
                    b.clear()
                faz_msg_box("Cadastro realizado!", str(msg), False)
            else:
                faz_msg_box("Erro", "Preencha todos os campos corretamente.", True)

        return slot

    def verifica_campos(self, nome, idade, serie, turno, contato, endereco):
        if not nome.text() or not serie.text() or not turno.text() or not contato.text() or not endereco.text():
            return False
        if idade.value() <= 0:
            return False
        return True


#Configurações da janela de cadastro dos livros 
class JanelaCadastroLivro(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)

        self.setWindowTitle("Cadastro de Livro")
        self.setMinimumSize(900, 350)
        layoutcl = QFormLayout()
        self.setLayout(layoutcl)

        layoutcl.addRow("Numeração:", numeracao := QSpinBox())
        numeracao.setRange(0, 9999999)

        layoutcl.addRow("Titulo Livro:", titulo := QLineEdit())
        layoutcl.addRow("Genero:", genero := QLineEdit())
        layoutcl.addRow("Autor:", autor := QLineEdit())
        layoutcl.addRow("Editora:", editora := QLineEdit())
        layoutcl.addRow("Quantidade:", qtd := QSpinBox())
        qtd.setRange(0, 9999)

        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layoutcl.addWidget(b_box)

        b_box.accepted.connect(
            self.faz_slot(
                biblioteca.cadastra_livro,
                numeracao, titulo, genero, autor, editora, qtd
            )
        )
        b_box.rejected.connect(self.reject)

    def faz_slot(self, func, *args):
        def slot():
            n, t, g, a, e, q = args
            if self.verifica_campos(*args):  
                msg = func(
                    n.text(), t.text(), g.text(), a.text(), e.text(), q.value()
                )
                for b in args:
                    b.clear()
                faz_msg_box(
                    "Cadastro Realizado!", str(msg), False
                )
        return slot

    def verifica_campos(self, *args):
        n, t, g, a, e, q = args
        if not n.text() or not t.text() or not g.text() or not a.text() or not e.text():
            faz_msg_box("Erro", "Todos os campos precisam ser preenchidos.", True)
            return False
        if q.value() <= 0:
            faz_msg_box("Erro", "A quantidade deve ser maior que zero.", True)
            return False
        return True

def faz_msg_box(titulo, mensagem, erro=False):
    msg = QMessageBox()
    msg.setWindowTitle(titulo)
    msg.setText(mensagem)
    if erro:
        msg.setIcon(QMessageBox.Critical)  
    else:
        msg.setIcon(QMessageBox.Information)  
    msg.exec()

class JanelaAteraAluno(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)

        self.setWindowTitle("Altera Cadastro - Aluno")
        self.setMinimumSize(900, 350)
        layoutaa = QFormLayout()
        self.setLayout(layoutaa)

        campo_texto = [_id := QSpinBox(), nome := QLineEdit(),
                       idade := QSpinBox(), serie := QLineEdit(),
                       turno := QLineEdit(), contato := QLineEdit(),
                       endereco := QLineEdit()]

        _id.setRange(0, 999999)
        titulos = ["ID", "Nome Aluno", "Idade", "Série", "Turno", "Contato", "Endereço"]

        for titulo, campo in zip(titulos, campo_texto):
            layoutaa.addRow(str(titulo), campo)

        self.botoes_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layoutaa.addWidget(self.botoes_box)

        self.botoes_box.accepted.connect(self.faz_slot(
            biblioteca.altera_aluno,
            _id, nome, idade, serie, turno, contato, endereco
        ))

        self.botoes_box.rejected.connect(self.reject)

    def faz_slot(self, func, *args):
        def slot():
            __id, n, i, s, t, c, e = args
            if self.verifica_campos(*args):
                aluno_id = str(__id.value())
                msg = func(aluno_id, n.text(), i.text(), s.text(), t.text(), c.text(), e.text())

                if msg is None:
                    faz_msg_box("ERRO!", "O ID digitado não existe.", True)
                else:
                    for b in args:
                        b.clear()
                    faz_msg_box("Cadastro atualizado!", str(msg), False)

        return slot

    def verifica_campos(self, *args):
        nome, idade, serie, turno, contato, endereco = args[1:]

        if not nome.text() or not serie.text() or not turno.text() or not contato.text() or not endereco.text():
            return False
        if idade.value() <= 0:
            return False
        return True


#Configurações da janela de alteção dos livros 
class JanelaAlteraLivro(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)

        self.setWindowTitle("Altera Cadastro - Livro")
        self.setMinimumSize(900, 350)
        layoutcl = QFormLayout()
        self.setLayout(layoutcl)

        layoutcl.addRow("Numeração:", numeracao := QSpinBox())
        numeracao.setRange(0, 9999999)

        layoutcl.addRow("Titulo Livro:", titulo := QLineEdit())
        layoutcl.addRow("Genero:", genero := QLineEdit())
        layoutcl.addRow("Autor:", autor := QLineEdit())
        layoutcl.addRow("Editora:", editora := QLineEdit())
        layoutcl.addRow("Quantidade:", qtd := QSpinBox())
        qtd.setRange(0, 999)

        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layoutcl.addWidget(b_box)

        b_box.accepted.connect(
            self.faz_slot(
                biblioteca.altera_livro,
                numeracao, titulo, genero, autor, editora, qtd
            )
        )
        b_box.rejected.connect(self.reject)

    def faz_slot(self, func, *args):
        def slot():
            n, t, g, a, e, q = args
            if self.verifica_campos(*args): 
                msg = func(
                    n.text(), t.text(), g.text(), a.text(), e.text(), q.value()
                )
                for b in args:
                    b.clear()
                if msg is None:
                    faz_msg_box("ERRO!", "ID não encontrado.", True)
                    return
                # Exibe a mensagem de sucesso após a alteração
                faz_msg_box("Cadastro Alterado!", "O livro foi alterado com sucesso.", False) 

        return slot

    def verifica_campos(self, *args):
        n, t, g, a, e, q = args
        if not n.text() or not t.text() or not g.text() or not a.text() or not e.text():
            faz_msg_box("Erro", "Todos os campos precisam ser preenchidos.", True)
            return False
        if q.value() <= 0:
            faz_msg_box("Erro", "A quantidade deve ser maior que zero.", True)
            return False
        return True

def faz_msg_box(titulo, mensagem, erro=False):
    msg = QMessageBox()
    msg.setWindowTitle(titulo)
    msg.setText(mensagem)  
    if erro:
        msg.setIcon(QMessageBox.Critical)  
    else:
        msg.setIcon(QMessageBox.Information)  
    msg.exec()


#Configurações da janela de Emprestimo
class JanelaEmprestimo(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)
        self.biblioteca = biblioteca  
        self.setWindowTitle("Empréstimo de Livro")
        self.setMinimumSize(500, 200)

        # Adicionando os campos necessários
        self._id = QLineEdit() 
        self.livro = QLineEdit()  
        self.data = QDateEdit() 
        self.data.setCalendarPopup(True)

        # Layout
        layout = QFormLayout()
        layout.addRow("ID do Aluno:", self._id)
        layout.addRow("Título do Livro:", self.livro)
        layout.addRow("Data de Devolução:", self.data)
        self.setLayout(layout)

        # Botões
        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b_box.accepted.connect(self.realiza_emprestimo)
        b_box.rejected.connect(self.reject)
        layout.addWidget(b_box)

    def verifica_campos(self, _id, livro, data):
        """Verificar se todos os campos foram preenchidos."""
        if not _id or not livro or not data:
            return False
        return True

    def realiza_emprestimo(self):
        """Processa o empréstimo após a verificação dos campos."""
        _id = self._id.text()  # Obtendo o valor do campo de ID
        livro = self.livro.text()  
        data = self.data.date().toString('yyyy-MM-dd')  

        # Verifica se os campos estão preenchidos corretamente
        if self.verifica_campos(_id, livro, data):
            try:
                chave, msg = self.biblioteca.fazer_emprestimo(_id, livro, data)
                faz_msg_box("Empréstimo realizado!", f"Chave do empréstimo: {chave}", False)
            except KeyError as e:
                faz_msg_box("Erro", f"ID de aluno não encontrado: {e}", True)
            except ValueError as e:
                faz_msg_box("Erro", str(e), True)
        else:
            faz_msg_box("Erro", "Todos os campos precisam ser preenchidos!", True)

class JanelaDevolucao(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)
        self.setWindowTitle("Devolução")
        self.setMinimumSize(600, 350)

        layoutdv = QFormLayout()
        self.setLayout(layoutdv)

        self.chave = QSpinBox()
        self.chave.setRange(0, 9999999)
        layoutdv.addRow("Chave da Devolução:", self.chave)

        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layoutdv.addWidget(b_box)

        b_box.accepted.connect(lambda: self.faz_slot(biblioteca.fazer_devolucao)())
        b_box.rejected.connect(self.reject)

    def faz_slot(self, func):
        def slot():
            chave_value = self.chave.value()  
            try:
                func(str(chave_value))  
                self.chave.clear()  
                faz_msg_box("Devolução Realizada!", "Devolução bem sucedida.", False)
            except KeyError:
                faz_msg_box("Falha!", "Devolução mal sucedida.\nERRO: CHAVE NÃO ENCONTRADA", True)
        return slot

if __name__ == "__main__":
    app = QApplication(sys.argv)

    janelaCentral = JanelaPrincipal()

    janelaCentral.show()
    sys.exit(app.exec())  