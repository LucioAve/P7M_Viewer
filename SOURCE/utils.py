import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional


class TempManager:
    """Gestisce il ciclo di vita della cartella temporanea dell'applicazione."""

    def __init__(self) -> None:
        self.temp_dir: Optional[Path] = None

    def create(self) -> Path:
        """Crea una cartella temporanea unica."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="P7MViewer_"))
        return self.temp_dir

    def cleanup(self) -> None:
        """Elimina la cartella temporanea e tutto il suo contenuto."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"[WARN] Impossibile eliminare la cartella temporanea {self.temp_dir}: {e}")


def open_file_with_default_app(file_path: Path) -> None:
    """
    Apre un file utilizzando l'applicazione predefinita del sistema operativo.
    Su Windows utilizza os.startfile.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Il file da aprire non esiste: {file_path}")

    try:
        os.startfile(str(file_path))  # type: ignore # Specifico per Windows
    except Exception as e:
        raise OSError(f"Impossibile aprire il file con il visualizzatore predefinito: {e}")