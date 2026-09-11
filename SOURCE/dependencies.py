import subprocess
import sys
from pathlib import Path


def install_requirements(requirements_file: str = "requirements.txt") -> None:
    """
    Verifica e installa automaticamente le dipendenze mancanti.
    Esegue una disinstallazione preventiva per evitare conflitti DLL su Windows.
    """
    print("[INFO] Verifica delle dipendenze in corso...")
    
    try:
        import PySide6
        import asn1crypto
        print("[INFO] Tutte le dipendenze sono già soddisfatte.")
        return
    except ImportError:
        print("[WARN] Dipendenze mancanti. Avvio della pulizia e installazione automatica...")
        
    try:
        # 1. Disinstalla eventuali versioni corrotte o parziali per evitare conflitti DLL
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "PySide6", "PySide6-Essentials", "PySide6-Addons"],
            capture_output=True,
            text=True
        )

        # 2. Reinstalla pulitamente usando --user (non richiede privilegi di amministratore)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "-r", requirements_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("\n[ERRORE] Impossibile installare le dipendenze automaticamente.")
            print("--- DETTAGLI ERRORI DI PIP ---")
            print(result.stderr)
            print("------------------------------")
            sys.exit(1)
            
        print("[INFO] Installazione completata con successo.")
        
    except Exception as e:
        print(f"[ERRORE] Impossibile eseguire pip: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_requirements()