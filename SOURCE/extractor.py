import os
from pathlib import Path
from typing import Optional

from asn1crypto import cms


class P7MExtractionError(Exception):
    """Eccezione base per gli errori di estrazione P7M."""
    pass


class P7MExtractor:
    """Classe responsabile dell'estrazione del contenuto PDF dai file P7M (CAdES)."""

    @staticmethod
    def extract_pdf(p7m_path: Path, output_dir: Path) -> Path:
        """
        Estrae il file PDF contenuto in un file P7M e lo salva in una cartella temporanea.
        
        Args:
            p7m_path: Il percorso del file .p7m di input.
            output_dir: La cartella temporanea dove salvare il PDF estratto.
            
        Returns:
            Il percorso del file PDF estratto.
            
        Raises:
            P7MExtractionError: Se il file non è valido, non contiene un PDF o è corrotto.
        """
        if not p7m_path.exists():
            raise P7MExtractionError(f"Il file non esiste: {p7m_path}")

        try:
            raw_data: bytes = p7m_path.read_bytes()
        except IOError as e:
            raise P7MExtractionError(f"Impossibile leggere il file: {e}")

        # Gestione del formato PEM (se il file è testuale)
        if b"-----BEGIN PKCS7-----" in raw_data:
            raw_data = P7MExtractor._pem_to_der(raw_data)

        try:
            # Parsing della struttura ASN.1 CMS/PKCS#7
            content_info = cms.ContentInfo.load(raw_data)
            
            # Verifica che sia un SignedData (tipico di CAdES)
            if content_info['content_type'].native != 'signed_data':
                raise P7MExtractionError("Il file non è un formato SignedData (CAdES) valido.")

            content_bytes: bytes = P7MExtractor._unwrap(content_info)

        except P7MExtractionError:
            raise
        except Exception as e:
            # Cattura errori di parsing ASN1
            raise P7MExtractionError(f"Errore nel parsing del file P7M. File corrotto o formato non supportato: {e}")

        # Verifica che il contenuto estratto sia effettivamente un PDF
        if not content_bytes.startswith(b'%PDF-'):
            raise P7MExtractionError("Il file P7M non contiene un documento PDF valido.")

        # Costruisce il percorso di output mantenendo il nome originale rimuovendo l'estensione p7m
        pdf_filename: str = p7m_path.stem + ".pdf"
        pdf_output_path: Path = output_dir / pdf_filename

        try:
            pdf_output_path.write_bytes(content_bytes)
        except IOError as e:
            raise P7MExtractionError(f"Impossibile scrivere il file temporaneo: {e}")

        return pdf_output_path

    # Limite di sicurezza sugli involucri annidati (firme multiple "a matrioska")
    MAX_NESTING: int = 10

    @staticmethod
    def _unwrap(content_info: cms.ContentInfo) -> bytes:
        """
        Estrae il contenuto da un SignedData, sbucciando eventuali P7M annidati
        (file firmati piu' volte in sequenza, es. nome.pdf.p7m.p7m).
        """
        for _ in range(P7MExtractor.MAX_NESTING):
            encap = content_info['content']['encap_content_info']
            content_bytes = encap['content'].native
            if content_bytes is None:
                raise P7MExtractionError(
                    "Firma detached: il P7M non contiene il documento (solo la firma).")

            # Il contenuto e' a sua volta un P7M? (DER inizia con SEQUENCE 0x30)
            if content_bytes[:1] == b'\x30':
                try:
                    inner = cms.ContentInfo.load(content_bytes)
                    if inner['content_type'].native == 'signed_data':
                        content_info = inner
                        continue
                except Exception:
                    pass  # non e' un CMS: lo restituiamo cosi' com'e'
            return content_bytes

        raise P7MExtractionError("Troppi livelli di firma annidati nel file P7M.")

    @staticmethod
    def _pem_to_der(pem_data: bytes) -> bytes:
        """Converte un certificato/contenuto PEM in formato DER (binario)."""
        lines = pem_data.decode('utf-8').splitlines()
        # Rimuove intestazioni e footer, e unisce le righe in un'unica stringa
        b64_data = "".join(line.strip() for line in lines if not line.startswith("-----"))
        import base64
        return base64.b64decode(b64_data)