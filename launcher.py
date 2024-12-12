import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QListWidget, QStatusBar, QHBoxLayout, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

class ScriptLauncher(QThread):
    script_executed = pyqtSignal(str, str)  # Emite dois sinais: mensagem e saída do script

    def __init__(self, file_queue):
        super().__init__()
        self.file_queue = file_queue

    def run(self):
        while not self.file_queue.empty():
            script_path = self.file_queue.get()
            try:
                self.launch_script(script_path)
            finally:
                self.file_queue.task_done()

    def launch_script(self, script_path):
        try:
            command = f'python -m streamlit run "{script_path}" --server.enableXsrfProtection false'
            process = subprocess.Popen(command, cwd=os.path.dirname(script_path), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            output = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    output.append(line.strip())
                    self.script_executed.emit(f"💬 Output: {line.strip()}", "\n".join(output))

            process.stdout.close()
            process.stderr.close()

            if process.returncode == 0:
                self.script_executed.emit(f"✅ Script executado: {script_path}", "\n".join(output))
            else:
                self.script_executed.emit(f"❌ Erro ao executar o script {script_path}", "\n".join(output))

        except Exception as e:
            self.script_executed.emit(f"❌ Erro ao executar {script_path}: {str(e)}", str(e))


class ScriptLauncherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Streamlit Script Launcher 3.0 Beta 🚀")
        self.setGeometry(300, 300, 800, 600)

        # Layout principal com Splitter para dividir as duas áreas
        self.main_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Vertical)

        # Frame 1: Área de drag-and-drop e lista de scripts
        self.top_frame = QWidget()
        self.top_layout = QVBoxLayout()

        # Título e instruções
        title_layout = QHBoxLayout()
        title_label = QLabel("Streamlit Script Launcher 3.0 Beta 🚀")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #FFD700;")
        title_layout.addWidget(title_label)
        self.top_layout.addLayout(title_layout)

        instruction_label = QLabel("📂 Arraste e solte arquivos Python aqui para executar no Streamlit.")
        instruction_label.setFont(QFont("Arial", 14))
        instruction_label.setStyleSheet("color: #BBBBBB; padding: 10px;")
        instruction_label.setAlignment(Qt.AlignCenter)
        self.top_layout.addWidget(instruction_label)

        # Área de Drag and Drop
        self.drop_area = QLabel("🚀 Arraste os scripts Python para cá")
        self.drop_area.setFont(QFont("Arial", 16, QFont.Bold))
        self.drop_area.setStyleSheet("""
            color: #FFD700;
            background-color: #444444;
            border: 3px dashed #FFD700;
            padding: 40px;
            border-radius: 12px;
            margin: 20px;
        """)
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.top_layout.addWidget(self.drop_area)

        # Lista de Scripts Processados
        self.script_list_widget = QListWidget()
        self.script_list_widget.setStyleSheet("""
            background-color: #333333;
            color: #FFD700;
            border-radius: 10px;
            padding: 15px;
        """)
        self.top_layout.addWidget(self.script_list_widget)

        # Barra de Status
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            background-color: #444444;
            color: #FFFFFF;
        """)
        self.top_layout.addWidget(self.status_bar)

        self.top_frame.setLayout(self.top_layout)

        # Frame 2: Área para exibir o output do console
        self.bottom_frame = QWidget()
        self.bottom_layout = QVBoxLayout()

        self.output_console = QTextEdit()
        self.output_console.setFont(QFont("Courier", 10))
        self.output_console.setStyleSheet("""
            background-color: #1E1E1E;
            color: #00FF00;
            border-radius: 10px;
            padding: 15px;
        """)
        self.output_console.setReadOnly(True)

        self.bottom_layout.addWidget(QLabel("📄 Logs de Execução:"))
        self.bottom_layout.addWidget(self.output_console)
        self.bottom_frame.setLayout(self.bottom_layout)

        # Adiciona os frames no splitter
        splitter.addWidget(self.top_frame)
        splitter.addWidget(self.bottom_frame)

        self.main_layout.addWidget(splitter)
        self.setLayout(self.main_layout)

        # Fila de scripts
        self.file_queue = Queue()

        # Inicializa a thread de execução de scripts
        self.script_launcher = None

        # Habilita Drag and Drop
        self.setAcceptDrops(True)

        # Estilos (Dark Mode com detalhes em amarelo)
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #FFD700;
            }
            QStatusBar {
                background-color: #333333;
                color: #FFD700;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile().endswith('.py')]
        for py_file in files:
            self.script_list_widget.addItem(f"📄 Enfileirado: {py_file}")
            self.file_queue.put(py_file)

        # Inicia a thread de execução se não estiver rodando
        if self.script_launcher is None or not self.script_launcher.isRunning():
            self.start_execution()

    def start_execution(self):
        self.script_launcher = ScriptLauncher(self.file_queue)
        self.script_launcher.script_executed.connect(self.update_logs)
        self.script_launcher.start()

    def update_logs(self, message, console_output):
        self.script_list_widget.addItem(message)
        self.output_console.setText(console_output)
        self.status_bar.showMessage(message, 5000)


if __name__ == "__main__":
    from queue import Queue

    app = QApplication(sys.argv)
    window = ScriptLauncherApp()
    window.show()
    sys.exit(app.exec_())
