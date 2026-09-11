import shutil
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QAction, QIcon, QPixmap, QPainter, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFrame, QLabel, QStatusBar, QFileDialog, QMessageBox
)

from extractor import P7MExtractor, P7MExtractionError
from utils import open_file_with_default_app, TempManager


class Worker(QThread):
    """Thread in background per non bloccare la GUI durante l'estrazione."""
    finished = Signal(Path)
    error = Signal(str, str)
    status_update = Signal(str)

    def __init__(self, p7m_path: Path, temp_dir: Path) -> None:
        super().__init__()
        self.p7m_path = p7m_path
        self.temp_dir = temp_dir

    def run(self) -> None:
        try:
            self.status_update.emit(f"Estrazione in corso: {self.p7m_path.name}...")
            pdf_path = P7MExtractor.extract_pdf(self.p7m_path, self.temp_dir)
            self.finished.emit(pdf_path)
        except P7MExtractionError as e:
            self.error.emit(self.p7m_path.name, str(e))
        except Exception as e:
            self.error.emit(self.p7m_path.name, f"Errore imprevisto: {str(e)}")


class DropZone(QFrame):
    """Area personalizzata per il Drag & Drop."""
    files_dropped = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAcceptDrops(True)  # Fix Drag & Drop
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.label_icon = QLabel("📄")
        self.label_icon.setFont(QFont("Segoe UI Emoji", 48))
        self.label_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label_text = QLabel("Trascina qui i file P7M")
        self.label_text.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_subtext = QLabel("oppure utilizza il pulsante sottostante")
        self.label_subtext.setFont(QFont("Segoe UI", 10))
        self.label_subtext.setStyleSheet("color: gray;")
        self.label_subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(self.label_icon)
        layout.addWidget(self.label_text)
        layout.addWidget(self.label_subtext)
        layout.addStretch()

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            DropZone {
                background-color: #f8f9fa;
                border: 2px dashed #ced4da;
                border-radius: 15px;
                margin: 20px;
            }
            DropZone:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                DropZone {
                    background-color: #dbe4ff;
                    border: 2px dashed #4263eb;
                    border-radius: 15px;
                    margin: 20px;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._apply_style()

    def dropEvent(self, event: QDropEvent) -> None:
        self._apply_style()
        urls: List[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".p7m":
                urls.append(path)
        
        if urls:
            self.files_dropped.emit(urls)
        else:
            QMessageBox.warning(self, "Formato non supportato", "Per favore trascina solo file con estensione .p7m")


class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione."""

    def __init__(self, temp_manager: TempManager) -> None:
        super().__init__()
        self.temp_manager = temp_manager
        self.workers: List[Worker] = []
        self.setWindowTitle("P7M Viewer - Estrattore PDF CAdES")
        self.resize(600, 450)
        
        self._set_app_icon() # Imposta l'icona emoji
        self._setup_ui()
        self._apply_theme()

    def _set_app_icon(self) -> None:
        """Crea un'icona partendo da un emoji e la imposta per la finestra."""
        # Crea un'immagine quadrata trasparente di 64x64 pixel
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        
        # Disegna l'emoji al centro dell'immagine
        painter = QPainter(pixmap)
        painter.setFont(QFont("Segoe UI Emoji", 48))
        painter.drawText(0, 0, 64, 64, Qt.AlignmentFlag.AlignCenter, "📩")
        painter.end()
        
        # Applica l'immagine come icona della finestra
        self.setWindowIcon(QIcon(pixmap))

    def _setup_ui(self) -> None:
        self.setAcceptDrops(True)  # Fix Drag & Drop
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- AGGIUNTA: Scritta in cima ---
        self.credit_label = QLabel("creata da L. A.")
        self.credit_label.setFont(QFont("Segoe UI", 9))
        self.credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.credit_label.setStyleSheet("color: #adb5bd; padding: 5px; border: none;")
        main_layout.addWidget(self.credit_label)
        # ---------------------------------

        # Drop Zone
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.process_files)
        main_layout.addWidget(self.drop_zone)

        # Pulsante Apri File
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_open = QPushButton("Apri file...")
        self.btn_open.setFixedSize(200, 40)
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_file_dialog)
        btn_layout.addWidget(self.btn_open)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

        # Barra di stato
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto")

    def _apply_theme(self) -> None:
        """Applica uno stile moderno e pulito (Tema chiaro)."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #4263eb;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b5bdb;
            }
            QPushButton:pressed {
                background-color: #364fc7;
            }
            QStatusBar {
                background-color: #f1f3f5;
                color: #495057;
                font-size: 12px;
                border-top: 1px solid #dee2e6;
            }
        """)

    def open_file_dialog(self) -> None:
        """Apre la finestra di dialogo per la selezione dei file."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleziona file P7M", "", "File Firmati (*.p7m)"
        )
        if files:
            paths = [Path(f) for f in files]
            self.process_files(paths)

    def process_files(self, p7m_files: List[Path]) -> None:
        """Gestisce l'elenco dei file ricevuti (da Drop o da Dialog)."""
        if not self.temp_manager.temp_dir:
            self.status_bar.showMessage("Errore: Cartella temporanea non inizializzata.")
            return

        for file_path in p7m_files:
            # Creiamo un worker per ogni file per mantenere la GUI reattiva
            worker = Worker(file_path, self.temp_manager.temp_dir)
            worker.finished.connect(self.on_extraction_success)
            worker.error.connect(self.on_extraction_error)
            worker.status_update.connect(self.status_bar.showMessage)
            
            self.workers.append(worker)
            worker.start()

    def on_extraction_success(self, pdf_path: Path) -> None:
        """Callback di successo: apre il PDF estratto."""
        try:
            open_file_with_default_app(pdf_path)
            self.status_bar.showMessage(f"Aperto con successo: {pdf_path.name}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Errore di apertura", str(e))
            self.status_bar.showMessage(f"Errore apertura per {pdf_path.name}")

    def on_extraction_error(self, filename: str, error_msg: str) -> None:
        """Callback di errore: mostra un messaggio all'utente."""
        self.status_bar.showMessage(f"Errore per {filename}")
        QMessageBox.critical(
            self, 
            f"Errore: {filename}", 
            f"Impossibile estrarre il PDF.\n\nMotivo:\n{error_msg}"
        )

    def closeEvent(self, event) -> None:
        """Garantisce che i thread finiscano e che i file temporanei vengano cancellati."""
        # Attendiamo la fine dei work in corso
        for worker in self.workers:
            if worker.isRunning():
                worker.wait(1000) # Attende max 1 secondo per thread
        
        # Pulizia finale
        self.temp_manager.cleanup()
        event.accept()