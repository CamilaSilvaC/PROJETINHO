import os
import json
import sys
from pathlib import Path
import qdarktheme
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QCalendarWidget, QVBoxLayout,
    QGridLayout, QFormLayout, QWidget, QFrame,
    QApplication, QPushButton, QLabel, QDialog,
    QLineEdit, QSpinBox, QDateEdit, QListWidget,
    QDialogButtonBox, QMessageBox
)

CAMINHO_DB_FILES = Path(__file__).parent / "db_files"
IDS_ALUNOS = os.path.join(CAMINHO_DB_FILES, "id_alunos.json")
INFO_ALUNOS = os.path.join(CAMINHO_DB_FILES, "info_alunos.json")
IDS_LIVROS = os.path.join(CAMINHO_DB_FILES, "id_livros.json")
INFO_LIVROS = os.path.join(CAMINHO_DB_FILES, "info_livros.json")
EMPRESTIMOS = os.path.join(CAMINHO_DB_FILES, "emprestimos.json")
ID_EMPRESTIMO = os.path.join(CAMINHO_DB_FILES, "id_emprestimo.json")

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

    def importacao(self, caminho: str):
        with open(caminho, "r", encoding="utf-8") as arq:
            return json.load(arq)

    def exportacao(self, caminho: str, dados: dict):
        with open(caminho, "w", encoding="utf-8") as arq:
            json.dump(dados, arq, ensure_ascii=False, indent=2)

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
        livro = Livro(numeracao, titulo, genero, autor, editora, qtd)
        self.info_livros[numeracao] = livro.__dict__
        self.id_livros.append(numeracao)
        self.exportacao(IDS_LIVROS, self.id_livros)
        self.exportacao(INFO_LIVROS, self.info_livros)
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
        self.emprestimos.pop(chave)
        self.id_emprestimo.pop(chave)
        self.exportacao(EMPRESTIMOS, self.emprestimos)
        self.exportacao(ID_EMPRESTIMO, self.id_emprestimo)

class JanelaPrincipal(QMainWindow):
    def altera_aluno(
            self, _id: str, nome: str, idade: str, serie: str,
            turno: str, contato: str, endereco: str
            ):

        if _id not in self.id_alunos:
            return None

        self.info_alunos[_id] = {
            "ID": _id,
            "Nome": nome.title(),
            "Série": serie,
            "Turno": turno.title(),
            "Idade": idade,
            "Contato": contato,
            "Endereço": endereco.title()
            }
        self.exportacao(INFO_ALUNOS, self.info_alunos)
        return self.info_alunos[_id]

    def altera_livro(self, numeracao: str, titulo: str, genero: str,
                     autor: str, editora: str, qtd: str
                     ):
        if numeracao not in self.id_livros:
            return None
        self.info_livros[numeracao] = (
            f"Título: {titulo.capitalize()}, "
            f"Gênero: {genero.capitalize()}, "
            f"Autor: {autor.capitalize()}, "
            f"Editora:  {editora.capitalize()}, Quantidade: {qtd}")
        self.exportacao(INFO_LIVROS, self.info_livros)
        return self.info_livros[numeracao]

    def fazer_emprestimo(self, _id: str, livro: str, devo: str):

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

    def fazer_devolucao(self, chave: str):

        self.emprestimos.pop(chave)
        self.id_emprestimo.pop(chave)
        self.exportacao(EMPRESTIMOS, self.emprestimos)
        self.exportacao(ID_EMPRESTIMO, self.id_emprestimo)


class JanelaPrincipal(QMainWindow):

    def __init__(self) -> None:
        super().__init__()

        self.b1 = Biblioteca()  
        
        # Criando o widget central
        self.widgetCentral = QWidget(self)

        # Criando janelas para cada botão
        self.janelaCA = JanelaCadastraAluno(self.b1)  
        self.janelaCL = JanelaCadastroLivro(self.b1)  
        self.janelaAA = JanelaAteraAluno(self.b1)  
        self.janelaAL = JanelaAlteraLivro(self.b1)  
        self.janelaEP = JanelaEmprestimo(self.b1)  
        self.janelaDV = JanelaDevolucao(self.b1) 
        
        # Criando os layouts da janela principal
        self.meuLayout1 = QVBoxLayout(self.widgetCentral)
        self.layout_botoes = QGridLayout()
        self.logo_label = QLabel(self)
        caminho_logo = os.path.join(os.path.dirname(__file__), 'img', 'logo.png')
        
        self.logo_pixmap = QPixmap(caminho_logo)
        
        if self.logo_pixmap.isNull():
            print(f"Erro: Não encontrei a logo em {caminho_logo}")
        
        self.logo_pixmap = self.logo_pixmap.scaled(350, 300, Qt.AspectRatioMode.KeepAspectRatio)
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.meuLayout1.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Criando os botões
        self.criabotoes()  

        # Adicionando os botões ao layout
        self.layout_botoes.addWidget(self.CA, 0, 0)
        self.layout_botoes.addWidget(self.CL, 0, 1)
        self.layout_botoes.addWidget(self.AA, 1, 0)
        self.layout_botoes.addWidget(self.AL, 1, 1)
        self.layout_botoes.addWidget(self.EP, 2, 0)
        self.layout_botoes.addWidget(self.DV, 2, 1)

        self.layout_botoes.addWidget(
            alunos := Botao("Listagem Alunos"),
            3, 0, 1, 2
        )
        self.layout_botoes.addWidget(
            livros := Botao("Listagem Livros"),
            4, 0, 1, 2
        )
        self.layout_botoes.addWidget(
            emprestimos := Botao("Listagem Empréstimos"),
            5, 0, 1, 2
        )

        # Adicionando os botões ao layout principal
        self.meuLayout1.addLayout(self.layout_botoes)

        # Configurando o estilo da janela
        self.config_style()

        # Conectando os botões com os métodos apropriados
        self.CA.clicked.connect(self.janelaCA.show)
        self.CL.clicked.connect(self.janelaCL.show)
        self.AA.clicked.connect(self.janelaAA.show)
        self.AL.clicked.connect(self.janelaAL.show)
        self.EP.clicked.connect(self.janelaEP.show)
        self.DV.clicked.connect(self.janelaDV.show)

        alunos.clicked.connect(self.faz_slot(
            self.listagem_dados,
            self.b1.info_alunos
        ))
        livros.clicked.connect(self.faz_slot(
            self.listagem_dados,
            self.b1.info_livros
        ))
        emprestimos.clicked.connect(self.faz_slot(
            self.listagem_dados,
            self.b1.emprestimos
        ))

        self.setCentralWidget(self.widgetCentral)

    def config_style(self):
        screen = QApplication.primaryScreen()
        screen_size = screen.size()

        self.resize(screen_size.width(), screen_size.height())

        self.showMaximized()

        self.setMinimumSize(screen_size.width() * 0.8, screen_size.height() * 0.8)

        qdarktheme.setup_theme(
            theme='dark',
            corner_shape='rounded',
            custom_colors={
                "[dark]": {"primary": "#AD49E1"},
                "[light]": {"primary": "#AD49E1"},
            }
        )



    def criabotoes(self):
        self.CA = Botao("Cadastra Aluno")
        self.CL = Botao("Cadastra Livro")
        self.AA = Botao("Altera Aluno")
        self.AL = Botao("Altera Livro")
        self.EP = Botao("Empréstimo")
        self.DV = Botao("Devoluçao")

    def listagem_dados(self, dados: dict):
        _janela = QDialog()
        _janela.setWindowTitle("Listagem dos dados")
        _janela.setFixedSize(1000, 800)
        _layout = QVBoxLayout()
        _lista = QListWidget()
        for chave, dado in dados.items():
            _lista.addItem((f"ID: {chave}\n {dado}"))
            _lista.addItem("\n")
        _layout.addWidget(_lista)
        _janela.setLayout(_layout)
        _janela.exec()

    def faz_slot(self, func, dicionario):
        def slot():
            func(dicionario)
        return slot


class BarraTitulo(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(50)
        self.setStyleSheet("background-color: #AD49E1; color: white;")

        layout = QVBoxLayout(self)

        self.titulo_label = QLabel("Biblioteca")
        self.titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo_label.setStyleSheet("font-size: 30px; font-weight: bold;")


        layout.addWidget(self.titulo_label)


class Botao(QPushButton):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        fonte = self.font()
        fonte.setPixelSize(30)
        fonte.setBold(True)
        self.setFont(fonte)


# classes para as janelas secundárias apenas com estilos
class JanelaCadastraAluno(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

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

    def faz_slot(self, func, *args: Botao):
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