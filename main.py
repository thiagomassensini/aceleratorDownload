from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QLabel, QProgressBar, QTextEdit, QMessageBox
from PySide2.QtCore import QSize, QTimer
import os
import requests
import threading
import time
import sys

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.timer = QTimer(self)
        self.start_time = time.time()

        # Número de chunks a serem baixados simultaneamente
        self.num_threads = 8
        self.thread_progress = [0] * self.num_threads

        # Criando janela e atribuindo um titulo
        self.setWindowTitle("Acelerador de Download")
        self.setFixedSize(QSize(400, 400))

        # Criando caixa para digitar a URL
        self.url_edit = QLineEdit(self)
        self.url_edit.move(20, 20)
        self.url_edit.resize(360, 30)

        # Criando botão para download
        self.download_button = QPushButton("Download", self)
        self.download_button.move(20, 70)
        self.download_button.resize(100, 30)
        self.download_button.clicked.connect(lambda: self.download_file(url=self.url_edit.text()))

        # Mostrando a velocidade na frente do botão download


        # Criando barra de progresso
        self.progress_label = QLabel("Progresso", self)
        self.progress_label.move(20, 120)
        self.progress_label.resize(100, 30)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.move(20, 150)
        self.progress_bar.resize(360, 30)

        # Criando caixa de log
        self.log_box = QTextEdit(self)
        self.log_box.move(20, 190)
        self.log_box.resize(360, 200)
        self.log_box.setReadOnly(True)

    def download_file(self, url):
        self.download_button.setEnabled(False)  # Desabilitar o Botão após clickado
        # Tamanho do chunk (em bytes)
        chunk_size = 1024 * 1024 # 1MB

        # Obter o tamanho do arquivo
        r = requests.head(url)
        self.total_size = int(r.headers.get('Content-Length', 0))

        # Obter o nome do arquivo a partir da URL
        file_name = os.path.basename(url)

        # Dividir o arquivo em vários chunks
        chunk_ranges = []
        for i in range(self.num_threads):
            start_byte = i * (self.total_size // self.num_threads)
            end_byte = start_byte + (self.total_size // self.num_threads) - 1
            if i == self.num_threads - 1:
                end_byte = self.total_size - 1
            chunk_ranges.append((start_byte, end_byte))

        # Função que baixa um chunk específico do arquivo
        def download_chunk(start_byte, end_byte, url, filename):
            headers = {'Range': 'bytes={}-{}'.format(start_byte, end_byte)}
            r = requests.get(url, headers=headers, stream=True)
            if os.path.exists(filename):
                # Se o arquivo já existe, sair da função
                return
            # Acessar o arquivo de destino em modo append
            with open(filename, 'ab') as f:
                start_time = time.time()
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        # Atualizar o progresso do download
                        self.thread_progress[i] += len(chunk)  # atualizar variável de instância
                        # Atualizar a barra de progresso
                        QApplication.processEvents()
                        downloaded = sum(self.thread_progress)
                        progress_pct = 100 * downloaded / self.total_size
                        self.progress_bar.setValue(progress_pct)


        # Criar threads para baixar cada chunk
        threads = []
        self.thread_progress = [0] * self.num_threads
        for i in range(self.num_threads):
            start_byte, end_byte = chunk_ranges[i]
            t = threading.Thread(target=download_chunk, args=(start_byte, end_byte, url, 'part{}'.format(i)))
            t.start()
            threads.append(t)

        # Monitorar velocidade de download

        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000) # a cada 1 segundo
        while any(t.is_alive() for t in threads):
            QApplication.processEvents()
        self.timer.stop()

        # Concatenar as partes em um único arquivo
        print('Concatenando, aguarde')
        #self.log_box.append('Concatenando, aguarde')
        with open(file_name, 'wb') as f:
            for i in range(self.num_threads):
                QApplication.processEvents()
                filename = 'part{}'.format(i)
                #print('Concatenando part{}'.format(i))
                self.log_box.append('Concatenando part{}'.format(i))
                with open(filename, 'rb') as part_file:
                    f.write(part_file.read())

        # Verificar a integridade do arquivo pelo seu tamanho
        downloaded_size = sum(os.path.getsize('part{}'.format(i)) for i in range(self.num_threads))
        if downloaded_size == self.total_size:
            self.log_box.append("Download concluído com sucesso.")
            # Mostrar mensagem de conclusão de download
            QApplication.processEvents()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Download Concluído!")
            msg.setText("O download foi concluído com sucesso.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

            self.download_button.setEnabled(True)  # Habilitar o Botão após clickado
        else:
            self.log_box.append("Erro de download: o tamanho do arquivo baixado é diferente do tamanho esperado.")

        # Remover os arquivos de partes
        for i in range(self.num_threads):
            filename = 'part{}'.format(i)
            os.remove(filename)

    def update_progress(self):
        downloaded = sum(self.thread_progress)
        progress_pct = 100 * downloaded / self.total_size
        elapsed_time = time.time() - self.start_time
        download_speed = downloaded / elapsed_time / 1024 / 1024  # MB/s
        self.log_box.append(
            'Progresso: {:.2f}%, Velocidade de download: {:.2f} MB/s'.format(progress_pct, download_speed))
        self.progress_bar.setValue(progress_pct)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec_()