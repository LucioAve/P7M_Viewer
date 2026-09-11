import sys
from pathlib import Path

# 1. Gestione automatica delle dipendenze
# Il controllo 'frozen' verifica se il programma è stato compilato in un .exe con PyInstaller.
# Se è un .exe, salta l'installazione perché le librerie sono già impacchettate all'interno.
if not getattr(sys, 'frozen', False):
    CURRENT_DIR = Path(__file__).parent
    REQ_FILE = str(CURRENT_DIR / "requirements.txt")
    from dependencies import install_requirements
    install_requirements(REQ_FILE)

# 2. Import dei moduli principali (ora sicuri che le librerie siano presenti)
from PySide6.QtWidgets import QApplication
from gui import MainWindow
from utils import TempManager


def main() -> None:
    # Crea l'istanza per la gestione della cartella temporanea
    temp_manager = TempManager()
    temp_dir = temp_manager.create()

    # Inizializza l'applicazione Qt
    app = QApplication(sys.argv)
    app.setApplicationName("P7M Viewer")

    # Inizializza la GUI passando il gestore dei file temporanei
    window = MainWindow(temp_manager)
    window.show()

    # Esegue il loop principale
    exit_code = app.exec()

    # La pulizia della cartella temporanea viene gestita dall'evento closeEvent di MainWindow
    sys.exit(exit_code)


if __name__ == "__main__":
    main()