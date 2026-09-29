import sys
import os
import hashlib
import subprocess
from datetime import datetime, time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, 
    QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem, QCheckBox, 
    QDialog, QTabWidget, QButtonGroup, QStackedWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

import sqlite3

try:
    import qrcode
    from io import BytesIO
    QRCODE_DISPONIVEL = True
except ImportError:
    QRCODE_DISPONIVEL = False

try:
    from reportlab.lib.pagesizes import mm
    from reportlab.pdfgen import canvas
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False


NOME_ESTABELECIMENTO = "CANTINA DO PABLO"

PRATOS_DIARIOS = {
    0: [("Bife com fritas, arroz, feijão e salada", 22.00, "imagens/bife.png"), ("Frango empanado, arroz, feijão e salada", 22.00, "imagens/frango.png")],
    1: [("Strogonoff de carne com batata palha", 22.00, "imagens/strogocarne.png"), ("Strogonoff de frango com batata palha", 22.00, "imagens/strogofrango.png")],
    2: [("Churrasco misto com arroz, feijão e vinagrete", 22.00, "imagens/churras.png")],
    3: [("Bife a cavalo com arroz, feijão e salada", 22.00, "imagens/bifecavalo.png"), ("Frango frito com arroz, feijão e salada", 22.00, "imagens/ffrito.png")],
    4: [("Carne com calabresa, arroz e feijão", 22.00, "imagens/sextacalabresa.png"), ("Frango ao molho com arroz e feijão", 22.00, "imagens/sextafrango.png")],
}

PRODUTOS_BASE = {
    "Salgados": [
        ("Croissant Presunto e Queijo", 7.00, "imagens/cro.png"), ("Risole 4 queijos", 5.50, "imagens/RISOLE.png"),
        ("Risole de carne", 5.50, "imagens/RISOLE.png"), ("Croissant 3 queijos", 6.50, "imagens/cro.png"),
        ("Hambúrguer com cheddar", 7.00, "imagens/3.png"), ("Enroladinho de bauru", 7.00, "imagens/bauru.png"),
        ("Pão de batata calabresa", 6.50, "imagens/5.png"), ("Pão de batata frango", 6.50, "imagens/5.png"),
        ("Esfiha de carne", 7.00, "imagens/2.png"), ("Coxinha", 5.50, "imagens/1.png"),
        ("Pão de queijo", 3.50, "imagens/4.png"), ("Caldo", 20.00, "imagens/cup.png"), ("Espeto Variado", 9.00, "imagens/espeto.png")
    ],
    "Bebidas": [
        ("Guaraná 350ml", 5.50, "imagens/guarana.png"), ("Fanta Uva 350ml", 5.50, "imagens/uva.png"),
        ("Fanta Laranja 350ml", 5.50, "imagens/laranja.png"), ("Coca Cola Zero 350ml", 5.50, "imagens/zero.png"),
        ("Coca Cola 350ml", 5.50, "imagens/coca.png"), ("Suco Tropical 480ml", 8.00, "imagens/suco.png"),
        ("Suco Kmais 300ml", 7.50, "imagens/kmais.png"), ("Refrigerante Caçula", 4.00, "imagens/cacula.png")
    ]
}


def iniciar_bd():
    conexao = sqlite3.connect("sistema_restaurante_pt.db")
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS administradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_cliente TEXT,
            pratos TEXT NOT NULL,
            valor_total REAL DEFAULT 0.0,
            pagamento TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            status TEXT DEFAULT 'Pendente'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor REAL NOT NULL,
            data_hora TEXT NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM administradores")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO administradores (usuario, senha) VALUES (?, ?)", ("admin", hashlib.sha256("123".encode()).hexdigest()))
    conexao.commit()
    conexao.close()

def gerar_ticket_pdf(id_pedido, nome_cliente, texto_pratos, pagamento, valor_total):
    nome_arquivo = f"ticket_pedido_{id_pedido}.pdf"
    if REPORTLAB_DISPONIVEL:
        largura, altura = 80 * mm, 180 * mm 
        c = canvas.Canvas(nome_arquivo, pagesize=(largura, altura))
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(largura / 2, altura - 20, NOME_ESTABELECIMENTO)
        c.setFont("Helvetica", 8)
        c.drawCentredString(largura / 2, altura - 32, "-" * 38)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(largura / 2, altura - 46, f"PEDIDO Nº: {id_pedido}")
        c.setFont("Helvetica", 8)
        c.drawString(10, altura - 60, f"Cliente: {nome_cliente}")
        c.drawString(10, altura - 72, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        c.drawCentredString(largura / 2, altura - 82, "-" * 38)
        c.drawString(10, altura - 95, "Itens:")
        
        posicao_y = altura - 107
        for item in texto_pratos.split(" | "):
            linha = f"- {item}"
            c.drawString(10, posicao_y, linha[:40] + "..." if len(linha) > 40 else linha)
            posicao_y -= 12
            
        c.drawString(10, posicao_y - 10, f"Pagamento: {pagamento}")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(10, posicao_y - 22, f"Total: R$ {valor_total:.2f}")
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(largura / 2, posicao_y - 45, "STATUS: PAGAMENTO APROVADO")
        c.save()
    else:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(f"{NOME_ESTABELECIMENTO}\nPEDIDO: {id_pedido}\nCLIENTE: {nome_cliente}\nITENS: {texto_pratos}\nTOTAL: R$ {valor_total:.2f}")
    return nome_arquivo

def abrir_arquivo_pdf(caminho):
    try:
        if sys.platform == "win32": os.startfile(os.path.abspath(caminho))
        elif sys.platform == "darwin": subprocess.run(["open", os.path.abspath(caminho)])
        else: subprocess.run(["xdg-open", os.path.abspath(caminho)])
    except: pass

class DialogoPix(QDialog):
    def __init__(self, valor_total, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Pagamento via PIX - {NOME_ESTABELECIMENTO}")
        self.setFixedSize(320, 400)
        self.setStyleSheet("background-color: white; border-radius: 12px;")
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h3 style='text-align:center; color:#0f172a;'>Escaneie o QR Code</h3>"))
        layout.addWidget(QLabel(f"<p style='text-align:center; color:#16a34a; font-size:18px;'><b>R$ {valor_total:.2f}</b></p>"))
        
        self.label_qr = QLabel()
        self.label_qr.setAlignment(Qt.AlignCenter)
        if QRCODE_DISPONIVEL:
            qr = qrcode.make("00020126580014br.gov.bcb.pix0136sua-chave-pix-aqui520400005303986540520.005802BR5913Restaurante6009Sao Paulo62070503***6304")
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            self.label_qr.setPixmap(QPixmap.fromImage(QImage.fromData(buffer.getvalue())).scaled(210, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.label_qr)
        
        btn_confirmar = QPushButton("Confirmar Pagamento")
        btn_confirmar.setStyleSheet("background:#16a34a; color:white; font-weight:bold; font-size:15px; padding:12px; border-radius:8px;")
        btn_confirmar.clicked.connect(self.accept)
        layout.addWidget(btn_confirmar)
        self.setLayout(layout)

class CartaoProduto(QFrame):
    def __init__(self, nome, preco, callback_atualizar, imagem="", disponivel=True):
        super().__init__()
        self.nome = nome
        self.preco = preco
        self.callback_atualizar = callback_atualizar
        self.setFixedSize(190, 260)
        
        self.setStyleSheet(f"""
            CartaoProduto {{ 
                border: 1px solid #e2e8f0; border-radius: 12px; background-color: {'#ffffff' if disponivel else '#f8fafc'}; 
            }}
            CartaoProduto:hover {{ border: 2px solid {'#2563eb' if disponivel else '#e2e8f0'}; }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 15)
        
        lbl_img = QLabel()
        lbl_img.setFixedSize(110, 110)
        lbl_img.setAlignment(Qt.AlignCenter)
        if imagem and os.path.exists(imagem):
            lbl_img.setPixmap(QPixmap(imagem).scaled(110, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            pix = QPixmap(110, 110)
            pix.fill(Qt.lightGray if disponivel else Qt.darkGray)
            lbl_img.setPixmap(pix)
            lbl_img.setText("Sem Foto")
            lbl_img.setStyleSheet("color: white; font-weight: bold;")
  
        lbl_nome = QLabel(nome)
        lbl_nome.setWordWrap(True)
        lbl_nome.setAlignment(Qt.AlignCenter)
        lbl_nome.setStyleSheet(f"font-size:12px; font-weight:bold; color:{'#1e293b' if disponivel else '#94a3b8'};")
        
        lbl_preco = QLabel(f"R$ {preco:.2f}")
        lbl_preco.setAlignment(Qt.AlignCenter)
        lbl_preco.setStyleSheet(f"font-size:15px; font-weight:bold; color:{'#16a34a' if disponivel else '#94a3b8'};")
        
        self.checkbox = QCheckBox("Adicionar")
        self.checkbox.setStyleSheet(f"font-size:14px; font-weight:bold; color:{'#2563eb' if disponivel else '#94a3b8'};")
        if not disponivel:
            self.checkbox.setText("Indisponível")
            self.checkbox.setEnabled(False)
        else:
            self.checkbox.toggled.connect(self.callback_atualizar)
            
        layout.addWidget(lbl_img, alignment=Qt.AlignCenter)
        layout.addWidget(lbl_nome)
        layout.addWidget(lbl_preco)
        layout.addWidget(self.checkbox, alignment=Qt.AlignCenter)
        self.setLayout(layout)

class AbaCategoriaPaginada(QWidget):
    def __init__(self, itens, disponivel, callback, lista_global, mensagem_indisponivel=None):
        super().__init__()
        self.colunas, self.linhas_visiveis = 4, 2
        self.indice_linha = 0
        self.cartoes = []
        self.mensagem_indisponivel = mensagem_indisponivel or "⏰ Os pratos de Almoço só estão disponíveis das 11h às 15h."
        
        layout = QVBoxLayout()
        self.grid = QGridLayout()
        self.grid.setSpacing(15)
        
        if not disponivel:

            self.grid.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            lbl_aviso = QLabel(self.mensagem_indisponivel)
            lbl_aviso.setStyleSheet("""
                background-color: #fef2f2; color: #991b1b; padding: 10px 16px;
                border: 1px solid #fecaca; border-radius: 8px; font-weight: bold; font-size: 15px;
            """)
            lbl_aviso.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(lbl_aviso, 0, 0, 1, self.colunas, Qt.AlignHCenter)
            
            for i, item in enumerate(itens):
                nome, preco = item[0], item[1]
                img = item[2] if len(item) == 3 else ""
                cartao = CartaoProduto(nome, preco, callback, img, disponivel=False)
                self.cartoes.append(cartao)
                self.grid.addWidget(cartao, 1 + (i // self.colunas), i % self.colunas)
        else:
            for i, item in enumerate(itens):
                nome, preco = item[0], item[1]
                img = item[2] if len(item) == 3 else ""
                cartao = CartaoProduto(nome, preco, callback, img, disponivel=True)
                self.cartoes.append(cartao)
                lista_global.append(cartao)
                self.grid.addWidget(cartao, i // self.colunas, i % self.colunas)
                
        layout_botoes = QHBoxLayout()
        estilo_btn = "QPushButton { font-size:14px; font-weight:bold; padding:10px 20px; background:#f1f5f9; border: 1px solid #cbd5e1; border-radius:6px; color:#334155; } QPushButton:hover { background:#e2e8f0; } QPushButton:disabled { color:#cbd5e1; border-color:#e2e8f0; }"
        
        self.btn_ant = QPushButton("◀ Anterior")
        self.btn_ant.setStyleSheet(estilo_btn)
        self.btn_ant.clicked.connect(self.voltar)
        
        self.btn_prox = QPushButton("Próximo ▶")
        self.btn_prox.setStyleSheet(estilo_btn)
        self.btn_prox.clicked.connect(self.avancar)
        
        layout_botoes.addStretch()
        layout_botoes.addWidget(self.btn_ant)
        layout_botoes.addWidget(self.btn_prox)
        layout_botoes.addStretch()
        
        layout.addLayout(self.grid)
        layout.addLayout(layout_botoes)
        self.setLayout(layout)
        self.atualizar_tela()
        
    def atualizar_tela(self):
        inicio = self.indice_linha * self.colunas
        fim = inicio + (self.linhas_visiveis * self.colunas)
        for i, c in enumerate(self.cartoes):
            c.show() if inicio <= i < fim else c.hide()
        self.btn_ant.setEnabled(self.indice_linha > 0)
        self.btn_prox.setEnabled(fim < len(self.cartoes))
        
    def avancar(self):
        self.indice_linha += self.linhas_visiveis
        self.atualizar_tela()
        
    def voltar(self):
        if self.indice_linha > 0:
            self.indice_linha -= self.linhas_visiveis
            if self.indice_linha < 0:
                self.indice_linha = 0
        self.atualizar_tela()

class JanelaCliente(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autoatendimento - Cliente")
        self.resize(1000, 950)
        self.setStyleSheet("""
            QMainWindow { background-color: #f4f6f9; }
            QFrame { background: white; border-radius: 14px; border: 1px solid #e1e8ed; }
        """)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        widget_main = QWidget()
        layout_main = QVBoxLayout(widget_main)
        layout_main.setContentsMargins(25, 25, 25, 25)
        layout_main.setSpacing(25)
        
        lbl_titulo = QLabel("SEJA BEM-VINDO!")
        lbl_titulo.setStyleSheet("font-size:32px; font-weight:900; color:#1e293b; letter-spacing: 1px;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        
        lbl_subtitulo = QLabel("Siga os passos abaixo para realizar o seu pedido rapidamente.")
        lbl_subtitulo.setStyleSheet("font-size:15px; color:#64748b; font-weight: 500; margin-bottom: 10px;")
        lbl_subtitulo.setAlignment(Qt.AlignCenter)
        
        layout_main.addWidget(lbl_titulo)
        layout_main.addWidget(lbl_subtitulo)
        

        frame_id = QFrame()
        layout_id = QVBoxLayout(frame_id)
        layout_id.setContentsMargins(20, 20, 20, 20)
        
        lbl_b1_titulo = QLabel("👤 PASSO 1: Quem está fazendo o pedido?")
        lbl_b1_titulo.setStyleSheet("font-size:18px; font-weight:800; color:#0f172a; border: none;")
        
        lbl_b1_sub = QLabel("Digite o seu nome abaixo para ser chamado quando o prato estiver pronto.")
        lbl_b1_sub.setStyleSheet("font-size:13px; color:#64748b; font-weight: 500; border: none; margin-bottom: 8px;")
        
        layout_id.addWidget(lbl_b1_titulo)
        layout_id.addWidget(lbl_b1_sub)
        
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Toque nas teclas para digitar o seu nome...")
        self.input_nome.setStyleSheet("""
            QLineEdit {
                font-size: 20px;
                font-weight: bold;
                padding: 14px;
                border: 2px solid #cbd5e1;
                border-radius: 10px;
                background-color: #f8fafc;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 2px solid #2563eb;
                background-color: #ffffff;
            }
        """)
        self.input_nome.setAlignment(Qt.AlignCenter)
        layout_id.addWidget(self.input_nome)
        
        grid_teclado = QGridLayout()
        grid_teclado.setSpacing(8)
        grid_teclado.setContentsMargins(0, 10, 0, 0)
        
        teclas = ['Q','W','E','R','T','Y','U','I','O','P','A','S','D','F','G','H','J','K','L','Z','X','C','V','B','N','M',' Espaço ','⌫ Apagar','Limpar']
        r, c = 0, 0
        for t in teclas:
            btn = QPushButton(t)
            
            if t in ['⌫ Apagar', 'Limpar']:
                estilo_tecla = """
                    QPushButton {
                        font-size: 14px; font-weight: bold; padding: 14px;
                        background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; border-radius: 8px;
                    }
                    QPushButton:pressed { background: #fca5a5; }
                """
            elif t == ' Espaço ':
                estilo_tecla = """
                    QPushButton {
                        font-size: 14px; font-weight: bold; padding: 14px;
                        background: #e2e8f0; color: #334155; border: 1px solid #cbd5e1; border-radius: 8px;
                    }
                    QPushButton:pressed { background: #cbd5e1; }
                """
            else:
                estilo_tecla = """
                    QPushButton {
                        font-size: 16px; font-weight: bold; padding: 14px;
                        background: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; border-radius: 8px;
                    }
                    QPushButton:pressed { background: #e2e8f0; }
                """
                
            btn.setStyleSheet(estilo_tecla)
            btn.clicked.connect(lambda _, k=t: self.digitar(k))
            
            col_span = 2 if t in ['⌫ Apagar', 'Limpar', ' Espaço '] else 1
            grid_teclado.addWidget(btn, r, c, 1, col_span)
            c += col_span
            if c > 9: c, r = 0, r + 1
            
        layout_id.addLayout(grid_teclado)
        layout_main.addWidget(frame_id)
        
        frame_menu = QFrame()
        layout_menu = QVBoxLayout(frame_menu)
        layout_menu.setContentsMargins(20, 20, 20, 20)
        
        lbl_b2_titulo = QLabel("🍽️ PASSO 2: Monte o seu pedido")
        lbl_b2_titulo.setStyleSheet("font-size:18px; font-weight:800; color:#0f172a; border: none;")
        
        lbl_b2_sub = QLabel("Navegue pelas abas abaixo e escolha os itens desejados.")
        lbl_b2_sub.setStyleSheet("font-size:13px; color:#64748b; font-weight: 500; border: none; margin-bottom: 8px;")
        
        layout_menu.addWidget(lbl_b2_titulo)
        layout_menu.addWidget(lbl_b2_sub)
        
        self.abas = QTabWidget()
        self.abas.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 8px; background: white; }
            QTabBar::tab {
                background: #f1f5f9; padding: 14px 28px; border-top-left-radius: 8px; border-top-right-radius: 8px;
                font-weight: bold; font-size: 15px; color: #64748b; margin-right: 4px;
            }
            QTabBar::tab:selected { background: #2563eb; color: white; }
            QTabBar::tab:hover:!selected { background: #e2e8f0; }
        """)
        
        self.cartoes_ativos = []
        agora = datetime.now()
        dia_semana = agora.weekday() 
        hora_almoco = time(11, 0) <= agora.time() <= time(15, 0)
        funcionamento_semana = dia_semana <= 4
        
        pratos_de_hoje = PRATOS_DIARIOS.get(dia_semana, [])
        
        if not funcionamento_semana:
            mensagem_almoco = "🍴 A CANTINA DO PABLO funciona de segunda a sexta. Hoje não há almoço disponível."
        elif not hora_almoco:
            mensagem_almoco = "⏰ Os pratos de almoço só estão disponíveis das 11h às 15h."
        else:
            mensagem_almoco = None
        
        dicionario = {
            "Almoço": pratos_de_hoje,
            "Salgados": PRODUTOS_BASE["Salgados"],
            "Bebidas": PRODUTOS_BASE["Bebidas"]
        }
        
        for cat, itens in dicionario.items():
            aba = QWidget()
            l_aba = QVBoxLayout(aba)
            disp = True
            mensagem_indisponivel = None
            if cat == "Almoço":
                disp = funcionamento_semana and hora_almoco
                mensagem_indisponivel = mensagem_almoco
                
            l_aba.addWidget(AbaCategoriaPaginada(
                itens, disp, self.calc_total, self.cartoes_ativos, mensagem_indisponivel
            ))
            self.abas.addTab(aba, cat)
            
        layout_menu.addWidget(self.abas)
        layout_main.addWidget(frame_menu)
        
        frame_pag = QFrame()
        layout_pag = QVBoxLayout(frame_pag)
        layout_pag.setContentsMargins(20, 20, 20, 20)
        
        lbl_b3_titulo = QLabel("💳 PASSO 3: Confirmação e Pagamento")
        lbl_b3_titulo.setStyleSheet("font-size:18px; font-weight:800; color:#0f172a; border: none;")
        
        lbl_b3_sub = QLabel("Escolha a forma de pagamento e finalize seu pedido.")
        lbl_b3_sub.setStyleSheet("font-size:13px; color:#64748b; font-weight: 500; border: none; margin-bottom: 8px;")
        
        layout_pag.addWidget(lbl_b3_titulo)
        layout_pag.addWidget(lbl_b3_sub)
        
        self.lbl_total = QLabel("Total: R$ 0.00")
        self.lbl_total.setStyleSheet("""
            font-size: 30px; font-weight: 900; color: #16a34a; 
            background: #f0fdf4; padding: 15px; border-radius: 10px; border: 1px solid #bbf7d0;
        """)
        self.lbl_total.setAlignment(Qt.AlignCenter)
        layout_pag.addWidget(self.lbl_total)
        
        layout_formas = QHBoxLayout()
        layout_formas.setSpacing(12)
        
        self.grupo_pag = QButtonGroup(self)
        self.formas = ["💵 Dinheiro", "💳 Cartão", "📱 PIX"]
        for i, f in enumerate(self.formas):
            btn = QPushButton(f)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px; font-weight: bold; padding: 16px;
                    background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 10px; color: #334155;
                }
                QPushButton:checked {
                    background: #2563eb; border: 2px solid #1d4ed8; color: white;
                }
            """)
            if i == 0: btn.setChecked(True)
            self.grupo_pag.addButton(btn, i)
            layout_formas.addWidget(btn)
            
        layout_pag.addLayout(layout_formas)
        
        btn_finalizar = QPushButton("CONFIRMAR E FINALIZAR PEDIDO")
        btn_finalizar.setStyleSheet("""
            QPushButton {
                background: #16a34a; color: white; font-size: 20px; font-weight: 900;
                padding: 18px; border-radius: 10px; border: none; margin-top: 10px;
            }
            QPushButton:hover { background: #15803d; }
            QPushButton:pressed { background: #166534; }
        """)
        btn_finalizar.clicked.connect(self.finalizar)
        layout_pag.addWidget(btn_finalizar)
        
        layout_main.addWidget(frame_pag)
        
        scroll.setWidget(widget_main)
        self.setCentralWidget(scroll)

    def digitar(self, t):
        txt = self.input_nome.text()
        if t in ['⌫', '⌫ Apagar']: self.input_nome.setText(txt[:-1])
        elif t == 'Limpar': self.input_nome.clear()
        elif t == ' Espaço ': self.input_nome.setText(txt + ' ')
        else: self.input_nome.setText(txt + t)

    def calc_total(self):
        total = sum(c.preco for c in self.cartoes_ativos if c.checkbox.isChecked())
        self.lbl_total.setText(f"Total: R$ {total:.2f}")
        return total

    def finalizar(self):
        nome = self.input_nome.text().strip()
        if not nome: return QMessageBox.warning(self, "Aviso", "Por favor, digite o seu nome no Passo 1.")
        
        itens = [c.nome for c in self.cartoes_ativos if c.checkbox.isChecked()]
        if not itens: return QMessageBox.warning(self, "Aviso", "Por favor, selecione pelo menos um produto no Passo 2.")
        
        total = self.calc_total()
        pagamento = self.formas[self.grupo_pag.checkedId()].split()[-1]
        
        if pagamento == "PIX" and DialogoPix(total, self).exec() != QDialog.Accepted: return
            
        con = sqlite3.connect("sistema_restaurante_pt.db")
        cur = con.cursor()
        cur.execute("INSERT INTO pedidos (nome_cliente, pratos, valor_total, pagamento, data_hora) VALUES (?, ?, ?, ?, ?)", 
                    (nome, " | ".join(itens), total, pagamento, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        con.commit()
        id_ped = cur.lastrowid
        con.close()
        
        pdf_path = gerar_ticket_pdf(id_ped, nome, " | ".join(itens), pagamento, total)
        abrir_arquivo_pdf(pdf_path)
        QMessageBox.information(self, "Pedido Confirmado!", f"Obrigado, {nome}!\nSeu pedido #{id_ped} foi registrado com sucesso.")
        
        self.input_nome.clear()
        for c in self.cartoes_ativos: c.checkbox.setChecked(False)

class DialogoCadastrarAdmin(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Novo Administrador")
        self.setFixedSize(350, 260)
        self.setStyleSheet("background-color: #f8fafc;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        titulo = QLabel("<h3>Novo Administrador</h3>")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("color: #0f172a;")
        
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Novo Usuário")
        self.input_usuario.setStyleSheet("font-size: 14px; padding: 10px; background: white; border: 1px solid #cbd5e1; border-radius: 6px;")
        
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Senha")
        self.input_senha.setEchoMode(QLineEdit.Password)
        self.input_senha.setStyleSheet("font-size: 14px; padding: 10px; background: white; border: 1px solid #cbd5e1; border-radius: 6px;")
        
        btn_salvar = QPushButton("Cadastrar")
        btn_salvar.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; font-size: 14px; padding: 10px; border-radius: 6px;")
        btn_salvar.clicked.connect(self.salvar_admin)
        
        layout.addWidget(titulo)
        layout.addWidget(self.input_usuario)
        layout.addWidget(self.input_senha)
        layout.addWidget(btn_salvar)
        
    def salvar_admin(self):
        usuario = self.input_usuario.text().strip()
        senha = self.input_senha.text().strip()
        
        if not usuario or not senha:
            return QMessageBox.warning(self, "Aviso", "Preencha todos os campos!")
            
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        
        try:
            conexao = sqlite3.connect("sistema_restaurante_pt.db")
            cursor = conexao.cursor()
            cursor.execute("INSERT INTO administradores (usuario, senha) VALUES (?, ?)", (usuario, senha_hash))
            conexao.commit()
            conexao.close()
            QMessageBox.information(self, "Sucesso", "Administrador cadastrado com sucesso!")
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Erro", "Este nome de usuário já existe.")

class WidgetLoginAdmin(QWidget):
    def __init__(self, callback_sucesso):
        super().__init__()
        layout = QVBoxLayout()
        titulo = QLabel("<h2>Login do Administrador</h2>")
        titulo.setAlignment(Qt.AlignCenter)
        
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuário")
        self.input_usuario.setStyleSheet("font-size: 14px; padding: 10px; background: white; border: 1px solid #cbd5e1; border-radius: 6px;")
        
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Senha")
        self.input_senha.setEchoMode(QLineEdit.Password)
        self.input_senha.setStyleSheet("font-size: 14px; padding: 10px; background: white; border: 1px solid #cbd5e1; border-radius: 6px;")
        
        btn_login = QPushButton("Entrar no Painel")
        btn_login.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 6px;")
        btn_login.clicked.connect(self.processar_login)
        
        btn_cadastrar = QPushButton("➕ Cadastrar Novo Administrador")
        btn_cadastrar.setStyleSheet("background-color: #64748b; color: white; font-weight: bold; font-size: 13px; padding: 10px; border-radius: 6px;")
        btn_cadastrar.clicked.connect(self.abrir_cadastro)
        
        layout.addWidget(titulo)
        layout.addWidget(self.input_usuario)
        layout.addWidget(self.input_senha)
        layout.addWidget(btn_login)
        layout.addWidget(btn_cadastrar)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        self.setLayout(layout)
        self.callback_sucesso = callback_sucesso

    def processar_login(self):
        usuario, senha = self.input_usuario.text().strip(), self.input_senha.text().strip()
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        
        conexao = sqlite3.connect("sistema_restaurante_pt.db")
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM administradores WHERE usuario = ? AND senha = ?", (usuario, senha_hash))
        resultado = cursor.fetchone()
        conexao.close()
        
        if resultado: 
            self.input_usuario.clear()
            self.input_senha.clear()
            self.callback_sucesso()
        else: 
            QMessageBox.warning(self, "Falha", "Usuário ou senha incorretos.")
            
    def abrir_cadastro(self):
        dialogo = DialogoCadastrarAdmin(self)
        dialogo.exec()

class WidgetPainelAdmin(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.abas = QTabWidget()
        self.abas.setStyleSheet("QTabBar::tab { padding: 10px 16px; font-weight: bold; }")

        self.aba_pendentes = QWidget()
        layout_pendentes = QVBoxLayout()
        self.tabela_pendentes = QTableWidget()
        self.tabela_pendentes.setColumnCount(6)
        self.tabela_pendentes.setHorizontalHeaderLabels(["ID", "Cliente", "Itens", "Total (R$)", "Pagamento", "Data/Hora"])
        self.tabela_pendentes.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_pendentes.setStyleSheet("alternate-background-color: #f2f2f2; background-color: white;")
        self.tabela_pendentes.setAlternatingRowColors(True)

        btn_chamar = QPushButton("📢 Chamar Cliente (Marcar como Entregue)")
        btn_chamar.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_chamar.clicked.connect(self.chamar_cliente)

        layout_pendentes.addWidget(self.tabela_pendentes)
        layout_pendentes.addWidget(btn_chamar)
        self.aba_pendentes.setLayout(layout_pendentes)


        self.aba_entregues = QWidget()
        layout_entregues = QVBoxLayout()
        self.tabela_entregues = QTableWidget()
        self.tabela_entregues.setColumnCount(6)
        self.tabela_entregues.setHorizontalHeaderLabels(["ID", "Cliente", "Itens", "Total (R$)", "Pagamento", "Data/Hora"])
        self.tabela_entregues.setStyleSheet("alternate-background-color: #f2f2f2; background-color: white;")
        self.tabela_entregues.setAlternatingRowColors(True)

        layout_entregues.addWidget(self.tabela_entregues)
        self.aba_entregues.setLayout(layout_entregues)

        self.aba_financeiro = QWidget()
        layout_financeiro = QVBoxLayout(self.aba_financeiro)
        layout_financeiro.setContentsMargins(12, 12, 12, 12)
        layout_financeiro.setSpacing(12)

        titulo_financeiro = QLabel(f"💰 Controle Financeiro - {NOME_ESTABELECIMENTO}")
        titulo_financeiro.setStyleSheet("font-size:22px; font-weight:900; color:#0f172a;")
        titulo_financeiro.setAlignment(Qt.AlignCenter)
        layout_financeiro.addWidget(titulo_financeiro)

        resumo = QHBoxLayout()
        self.lbl_receitas = QLabel("Receitas: R$ 0,00")
        self.lbl_despesas = QLabel("Despesas: R$ 0,00")
        self.lbl_saldo = QLabel("Saldo: R$ 0,00")

        for lbl, bg, fg in [
            (self.lbl_receitas, "#f0fdf4", "#15803d"),
            (self.lbl_despesas, "#fef2f2", "#b91c1c"),
            (self.lbl_saldo, "#eff6ff", "#1d4ed8")
        ]:
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"font-size:18px; font-weight:900; padding:14px; "
                f"background:{bg}; color:{fg}; border:1px solid #e2e8f0; border-radius:10px;"
            )
            resumo.addWidget(lbl)
        layout_financeiro.addLayout(resumo)

        frame_despesa = QFrame()
        frame_despesa.setStyleSheet("QFrame { background:white; border:1px solid #e2e8f0; border-radius:10px; }")
        form = QHBoxLayout(frame_despesa)
        form.setContentsMargins(10, 10, 10, 10)
        form.setSpacing(8)

        self.input_despesa = QLineEdit()
        self.input_despesa.setPlaceholderText("Descrição da despesa (ex.: compra de bebidas)")
        self.input_despesa.setStyleSheet("font-size:14px; padding:9px; border:1px solid #cbd5e1; border-radius:6px; background:white;")

        self.input_categoria = QLineEdit()
        self.input_categoria.setPlaceholderText("Categoria")
        self.input_categoria.setStyleSheet("font-size:14px; padding:9px; border:1px solid #cbd5e1; border-radius:6px; background:white;")

        self.input_valor_despesa = QLineEdit()
        self.input_valor_despesa.setPlaceholderText("Valor (R$)")
        self.input_valor_despesa.setStyleSheet("font-size:14px; padding:9px; border:1px solid #cbd5e1; border-radius:6px; background:white;")

        btn_adicionar_despesa = QPushButton("➕ Adicionar Despesa")
        btn_adicionar_despesa.setStyleSheet("background:#dc2626; color:white; font-weight:bold; padding:10px 14px; border-radius:6px;")
        btn_adicionar_despesa.clicked.connect(self.adicionar_despesa)

        form.addWidget(self.input_despesa, 3)
        form.addWidget(self.input_categoria, 1)
        form.addWidget(self.input_valor_despesa, 1)
        form.addWidget(btn_adicionar_despesa)
        layout_financeiro.addWidget(frame_despesa)

        self.abas_financeiras = QTabWidget()

        aba_receitas = QWidget()
        layout_receitas = QVBoxLayout(aba_receitas)
        self.tabela_receitas = QTableWidget()
        self.tabela_receitas.setColumnCount(6)
        self.tabela_receitas.setHorizontalHeaderLabels(["ID", "Cliente", "Itens", "Valor (R$)", "Pagamento", "Data/Hora"])
        self.tabela_receitas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_receitas.setAlternatingRowColors(True)
        self.tabela_receitas.setStyleSheet("alternate-background-color: #f2f2f2; background-color: white;")
        layout_receitas.addWidget(self.tabela_receitas)

        aba_despesas = QWidget()
        layout_despesas = QVBoxLayout(aba_despesas)
        self.tabela_despesas = QTableWidget()
        self.tabela_despesas.setColumnCount(5)
        self.tabela_despesas.setHorizontalHeaderLabels(["ID", "Descrição", "Categoria", "Valor (R$)", "Data/Hora"])
        self.tabela_despesas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_despesas.setAlternatingRowColors(True)
        self.tabela_despesas.setStyleSheet("alternate-background-color: #f2f2f2; background-color: white;")
        layout_despesas.addWidget(self.tabela_despesas)

        btn_excluir_despesa = QPushButton("🗑️ Excluir Despesa Selecionada")
        btn_excluir_despesa.setStyleSheet("background:#64748b; color:white; font-weight:bold; padding:10px; border-radius:6px;")
        btn_excluir_despesa.clicked.connect(self.excluir_despesa)
        layout_despesas.addWidget(btn_excluir_despesa)

        self.abas_financeiras.addTab(aba_receitas, "📈 Receitas")
        self.abas_financeiras.addTab(aba_despesas, "📉 Despesas")
        layout_financeiro.addWidget(self.abas_financeiras)

        self.abas.addTab(self.aba_pendentes, "Pendentes")
        self.abas.addTab(self.aba_entregues, "Entregues")
        self.abas.addTab(self.aba_financeiro, "💰 Financeiro")

        botoes = QHBoxLayout()
        btn_atualizar = QPushButton("🔄 Atualizar Listas")
        btn_atualizar.setStyleSheet("padding:10px; font-weight:bold; border-radius:4px; background-color:#bdc3c7; font-size:14px;")
        btn_atualizar.clicked.connect(self.atualizar_tudo)

        botoes.addStretch()
        botoes.addWidget(btn_atualizar)
        botoes.addStretch()

        cabecalho = QLabel("<h2>Gerenciamento de Pedidos</h2>")
        cabecalho.setAlignment(Qt.AlignCenter)
        layout.addWidget(cabecalho)
        layout.addWidget(self.abas)
        layout.addLayout(botoes)
        self.setLayout(layout)
        self.carregar_pedidos()
        self.carregar_financeiro()

    def atualizar_tudo(self):
        self.carregar_pedidos()
        self.carregar_financeiro()

    def carregar_pedidos(self):
        conexao = sqlite3.connect("sistema_restaurante_pt.db")
        cursor = conexao.cursor()

        def preencher_tabela(tabela, status):
            cursor.execute(
                "SELECT id, nome_cliente, pratos, valor_total, pagamento, data_hora "
                "FROM pedidos WHERE status = ? ORDER BY id DESC", (status,)
            )
            linhas = cursor.fetchall()
            tabela.setRowCount(len(linhas))
            for i_linha, linha in enumerate(linhas):
                for i_col, dado in enumerate(linha):
                    if i_col == 3:
                        tabela.setItem(i_linha, i_col, QTableWidgetItem(f"{float(dado):.2f}"))
                    else:
                        tabela.setItem(i_linha, i_col, QTableWidgetItem(str(dado)))
            tabela.resizeColumnsToContents()

        preencher_tabela(self.tabela_pendentes, 'Pendente')
        preencher_tabela(self.tabela_entregues, 'Entregue')
        conexao.close()

    def carregar_financeiro(self):
        conexao = sqlite3.connect("sistema_restaurante_pt.db")
        cursor = conexao.cursor()

        cursor.execute("SELECT id, nome_cliente, pratos, valor_total, pagamento, data_hora FROM pedidos ORDER BY id DESC")
        receitas = cursor.fetchall()
        self.tabela_receitas.setRowCount(len(receitas))
        total_receitas = 0.0

        for i_linha, linha in enumerate(receitas):
            for i_col, dado in enumerate(linha):
                if i_col == 3:
                    valor = float(dado)
                    total_receitas += valor
                    self.tabela_receitas.setItem(i_linha, i_col, QTableWidgetItem(f"{valor:.2f}"))
                else:
                    self.tabela_receitas.setItem(i_linha, i_col, QTableWidgetItem(str(dado)))
        self.tabela_receitas.resizeColumnsToContents()

        cursor.execute("SELECT id, descricao, categoria, valor, data_hora FROM despesas ORDER BY id DESC")
        despesas = cursor.fetchall()
        self.tabela_despesas.setRowCount(len(despesas))
        total_despesas = 0.0

        for i_linha, linha in enumerate(despesas):
            for i_col, dado in enumerate(linha):
                if i_col == 3:
                    valor = float(dado)
                    total_despesas += valor
                    self.tabela_despesas.setItem(i_linha, i_col, QTableWidgetItem(f"{valor:.2f}"))
                else:
                    self.tabela_despesas.setItem(i_linha, i_col, QTableWidgetItem(str(dado)))
        self.tabela_despesas.resizeColumnsToContents()

        saldo = total_receitas - total_despesas
        self.lbl_receitas.setText(f"Receitas: R$ {total_receitas:.2f}".replace('.', ','))
        self.lbl_despesas.setText(f"Despesas: R$ {total_despesas:.2f}".replace('.', ','))
        self.lbl_saldo.setText(f"Saldo: R$ {saldo:.2f}".replace('.', ','))
        conexao.close()

    def adicionar_despesa(self):
        descricao = self.input_despesa.text().strip()
        categoria = self.input_categoria.text().strip()
        texto_valor = self.input_valor_despesa.text().strip().replace(',', '.')

        if not descricao or not categoria or not texto_valor:
            return QMessageBox.warning(self, "Aviso", "Preencha descrição, categoria e valor da despesa.")

        try:
            valor = float(texto_valor)
        except ValueError:
            return QMessageBox.warning(self, "Aviso", "Digite um valor válido. Exemplo: 150,00")

        if valor <= 0:
            return QMessageBox.warning(self, "Aviso", "O valor da despesa deve ser maior que zero.")

        conexao = sqlite3.connect("sistema_restaurante_pt.db")
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO despesas (descricao, categoria, valor, data_hora) VALUES (?, ?, ?, ?)",
            (descricao, categoria, valor, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conexao.commit()
        conexao.close()

        self.input_despesa.clear()
        self.input_categoria.clear()
        self.input_valor_despesa.clear()
        self.carregar_financeiro()
        QMessageBox.information(self, "Sucesso", "Despesa registrada com sucesso!")

    def excluir_despesa(self):
        linha = self.tabela_despesas.currentRow()
        if linha < 0:
            return QMessageBox.warning(self, "Aviso", "Selecione uma despesa para excluir.")

        id_despesa = self.tabela_despesas.item(linha, 0).text()
        descricao = self.tabela_despesas.item(linha, 1).text()

        resposta = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Deseja realmente excluir a despesa:\n{descricao}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if resposta != QMessageBox.Yes:
            return

        conexao = sqlite3.connect("sistema_restaurante_pt.db")
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM despesas WHERE id = ?", (id_despesa,))
        conexao.commit()
        conexao.close()

        self.carregar_financeiro()
        QMessageBox.information(self, "Sucesso", "Despesa excluída com sucesso!")

    def chamar_cliente(self):
        linha_selecionada = self.tabela_pendentes.currentRow()
        if linha_selecionada < 0:
            return QMessageBox.warning(self, "Aviso", "Selecione um pedido pendente.")

        id_pedido = self.tabela_pendentes.item(linha_selecionada, 0).text()
        nome_cliente = self.tabela_pendentes.item(linha_selecionada, 1).text()

        conexao = sqlite3.connect("sistema_restaurante_pt.db")
        cursor = conexao.cursor()
        cursor.execute("UPDATE pedidos SET status = 'Entregue' WHERE id = ?", (id_pedido,))
        conexao.commit()
        conexao.close()

        self.carregar_pedidos()
        QMessageBox.information(self, "Chamada", f"CHAMANDO CLIENTE:\n{nome_cliente}\nPedido #{id_pedido}")


class JanelaAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Painel Administrativo - Caixa")
        self.resize(1100, 750)
        self.setStyleSheet("background-color: #ecf0f1;")
        self.widget_empilhado = QStackedWidget()
        
        self.widget_login = WidgetLoginAdmin(self.mostrar_painel)
        self.widget_painel = WidgetPainelAdmin()
        
        self.widget_empilhado.addWidget(self.widget_login)
        self.widget_empilhado.addWidget(self.widget_painel)
        self.setCentralWidget(self.widget_empilhado)
        
    def mostrar_painel(self):
        self.widget_painel.carregar_pedidos()
        self.widget_empilhado.setCurrentIndex(1)


if __name__ == "__main__":
    iniciar_bd()
    app = QApplication(sys.argv)
    

    janela_cliente = JanelaCliente()
    janela_admin = JanelaAdmin()
    
    janela_cliente.show()
    janela_admin.show()
    
    sys.exit(app.exec())