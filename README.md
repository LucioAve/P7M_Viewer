Documentazione essenziale per l'utilizzo e la compilazione.

P7M Viewer - Estrattore PDF CAdES
Applicazione desktop professionale per l'apertura rapida dei PDF contenuti all'interno di file .p7m (firma digitale CAdES).

Funzionalità
Drag & Drop: Trascina i file .p7m direttamente nell'interfaccia.
Apri file: Selezione classica tramite esplora risorse.
Estrazione locale: Nessun dato inviato a server esterni. Tutto il processo avviene in locale sfruttando analisi ASN.1.
Pulizia automatica: I PDF vengono salvati in una cartella temporanea che viene eliminata all'uscita dal programma.
Auto-Installazione: Se avvii lo script Python e mancano le librerie, il programma le installerà autonomamente tramite pip.
Requisiti
Python 3.11 o superiore
Windows 10 / Windows 11
Utilizzo come script Python
Apri il terminale nella cartella P7MViewer.
Esegui: python main.py
Compilazione in file .exe (PyInstaller)
Per creare un eseguibile stand-alone che non richiede l'installazione di Python:

Assicurati di avere PyInstaller installato: pip install pyinstaller
Dalla root del progetto, esegui il seguente comando:
pyinstaller --noconfirm --onedir --windowed --name "P7M Viewer" --add-data "requirements.txt;." main.py
(Nota: Ti consiglio di usare --onedir invece di --onefile per evitare lunghi tempi di avvio dovuti alla decompressione delle librerie crittografiche in memoria temporanea ad ogni esecuzione).

Troverai l'eseguibile dentro la cartella dist/P7M Viewer/P7M Viewer.exe.


---

#### 8. Cartella `assets/`
Crea la cartella vuota `assets/`. Se in futuro vorrai aggiungere un'icona (es. `icon.ico`), potrai importarla nel `main.py` aggiungendo:
`app.setWindowIcon(QIcon("assets/icon.ico"))` e indicando a PyInstaller di includerla con `--icon=assets/icon.ico`.

---

### Note di design implementative:
1. **Gestione del Multi-File e Threading**: Se trascini 5 file P7M contemporaneamente, l'applicazione crea 5 `QThread` indipendenti. Questo significa che l'interfaccia non si bloccherà mai ("Non risponde") e i PDF si apriranno uno dopo l'altro istantaneamente appena pronti.
2. **Validazione ASN.1 anziché Call esterne**: Invece di affidarmi a comandi di sistema o a librerie pesanti che richiedono OpenSSL, il parser legge l'albero binario del file p7m. Se l'albero non corrisponde allo standard `SignedData` o l'octet stream estratto non inizia con `%PDF-`, l'operazione viene abortita in modo sicuro restituendo un errore umano comprensibile.
3. **Bootstrapper**: Il modulo `dependencies.py` è stato posto *prima* dell'import di PySide6. Questo risolve un problema classico: non puoi mostrare una finestra Qt per dire "Installo le dipendenze" se Qt stesso manca. L'installer opera quindi in background testuale (del tutto invisibile se lanciato da `.exe` o doppio click su Windows) per poi far partire immediatamente dopo la GUI.

---

Applicazione desktop professionale per l'apertura rapida dei PDF contenuti all'interno di file `.p7m` (firma digitale CAdES).

## Funzionalità
- **Drag & Drop**: Trascina i file `.p7m` direttamente nell'interfaccia.
- **Apri file**: Selezione classica tramite esplora risorse.
- **Estrazione locale**: Nessun dato inviato a server esterni. Tutto il processo avviene in locale sfruttando analisi ASN.1.
- **Pulizia automatica**: I PDF vengono salvati in una cartella temporanea che viene eliminata all'uscita dal programma.
- **Auto-Installazione**: Se avvii lo script Python e mancano le librerie, il programma le installerà autonomamente tramite pip.

## Requisiti
- Python 3.11 o superiore
- Windows 10 / Windows 11

## Utilizzo come script Python
1. Apri il terminale nella cartella `P7MViewer`.
2. Esegui: `python main.py`

## Compilazione in file .exe (PyInstaller)

Per creare un eseguibile stand-alone che non richiede l'installazione di Python:

1. Assicurati di avere PyInstaller installato: `python -m pip install pyinstaller`
2. Dalla root del progetto, esegui il seguente comando:

```bash
python -m PyInstaller --noconfirm --onedir --windowed --name "P7M Viewer" --add-data "requirements.txt;." main.py