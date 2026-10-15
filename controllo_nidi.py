import io
import os
import requests
import pdfplumber
from bs4 import BeautifulSoup

CODICE = "NID-45718-2026"

URL = "https://www.comune.torino.it/schede-informative/graduatoria-nidi-dinfanzia-comunali-convenzione-sezioni-primavera-convenzione"

NIDI_DA_CONTROLLARE = [
    "Il Cerchio",
    "Peter Pan",
    "Gianni Rodari"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def invia_telegram(messaggio):

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        raise Exception("TELEGRAM_BOT_TOKEN mancante")

    if not chat_id:
        raise Exception("TELEGRAM_CHAT_ID mancante")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    risposta = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": messaggio
        },
        timeout=120
    )

    print(risposta.text)
    risposta.raise_for_status()


def trova_pdf():

    r = requests.get(
        URL,
        headers=HEADERS,
        timeout=120
    )

    r.raise_for_status()

    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )

    pdf_trovati = {}

    for li in soup.find_all("li"):

        testo_completo = li.get_text(
            " ",
            strip=True
        )

        for nido in NIDI_DA_CONTROLLARE:

            if nido.lower() in testo_completo.lower():

                for link in li.find_all(
                    "a",
                    href=True
                ):

                    testo_link = link.get_text(
                        " ",
                        strip=True
                    )

                    if "tempo lungo" in testo_link.lower():

                        href = link["href"]

                        if href.startswith("/"):

                            href = (
                                "https://www.comune.torino.it"
                                + href
                            )

                        pdf_trovati[nido] = href

                        print(
                            f"PDF trovato: {nido}"
                        )
                        
   return pdf_trovati


def cerca_codice_in_pdf(url_pdf):

    print(f"Scarico: {url_pdf}")

    r = requests.get(
        url_pdf,
        headers=HEADERS,
        timeout=120
    )

    r.raise_for_status()

    contenuto = io.BytesIO(r.content)

    with pdfplumber.open(contenuto) as pdf:

        testo = ""

        for pagina in pdf.pages:

            testo += (
                pagina.extract_text()
                or ""
            )

            testo += "\n"

    if CODICE not in testo:
        return None

    righe = testo.splitlines()

    for riga in righe:

        if CODICE in riga:

            campi = riga.split()

            if len(campi) > 0:

                return {
                    "posizione": campi[0],
                    "riga": riga.strip()
                }

    return None


def crea_messaggio(pdfs):

    messaggio = (
        "📋 Graduatorie Nidi Torino\n\n"
        f"Codice: {CODICE}\n\n"
    )

    for nido, url_pdf in pdfs.items():

        risultato = cerca_codice_in_pdf(
            url_pdf
        )

        if risultato:

            messaggio += (
                f"✅ {nido}: "
                f"posizione "
                f"{risultato['posizione']}\n"
            )

        else:

            messaggio += (
                f"❌ {nido}: "
                f"codice non trovato\n"
            )

    return messaggio


def main():

    print(
        "Controllo graduatorie in corso..."
    )

    pdfs = trova_pdf()

    if not pdfs:

        invia_telegram(
            "⚠️ Nessun PDF trovato."
        )

        return

    messaggio = crea_messaggio(
        pdfs
    )

    print(messaggio)

    invia_telegram(
        messaggio
    )

    print(
        "Messaggio Telegram inviato."
    )


if __name__ == "__main__":
    main()
