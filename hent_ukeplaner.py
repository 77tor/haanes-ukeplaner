import datetime
import json
import re
import requests
from bs4 import BeautifulSoup

TRINN_URLER = {
    "1": "https://www.minskole.no/haanes/seksjon/22360",
    "2": "https://www.minskole.no/haanes/seksjon/22362",
    "3": "https://www.minskole.no/haanes/seksjon/22363",
    "4": "https://www.minskole.no/haanes/seksjon/22493",
    "5": "https://www.minskole.no/haanes/seksjon/22494",
    "6": "https://www.minskole.no/haanes/seksjon/22495",
    "7": "https://www.minskole.no/haanes/seksjon/22496"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

dagens_dato = datetime.date.today()
innevaarende_uke = dagens_dato.isocalendar()[1]

# Håndter at forrige uke ved uke 1 er uke 52 (eller 53)
if innevaarende_uke == 1:
    forrige_uke = 52
else:
    forrige_uke = innevaarende_uke - 1

print(f"Dato: {dagens_dato}")
print(f"Søker etter ukeplaner for uke {innevaarende_uke} (reserve: uke {forrige_uke})...\n")

resultater = {}

for trinn, url in TRINN_URLER.items():
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        funnet_url = None
        funnet_uke = innevaarende_uke
        reserve_url = None
        forste_pdf_url = None

        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            tekst = a.get_text(strip=True)
            kombinert = f"{tekst} {href}".lower()
            
            # Utvidet sjekk for om det er en fil/PDF på MinSkole
            is_pdf = any(ext in href.lower() for ext in ['.pdf', '/fil/', 'file=', 'download', '/portals/'])
            
            if not is_pdf:
                continue

            # Bygg full URL
            if href.startswith('http'):
                full_url = href
            elif href.startswith('/'):
                full_url = f"https://www.minskole.no{href}"
            else:
                full_url = f"https://www.minskole.no/{href}"
            
            # Lagre aller første dokumentlenke som nødløsning
            if not forste_pdf_url:
                forste_pdf_url = full_url

            # RegEx for ukenummer (fanger "uke 5", "u5", "uke_05", "u-5" osv.)
            pattern_denne = rf"(uke|u)[\s\-_]*0?{innevaarende_uke}\b"
            pattern_forrige = rf"(uke|u)[\s\-_]*0?{forrige_uke}\b"

            if re.search(pattern_denne, kombinert):
                funnet_url = full_url
                funnet_uke = innevaarende_uke
                break
            elif re.search(pattern_forrige, kombinert) and not reserve_url:
                reserve_url = full_url

        # Fallback 1: Forrige ukes ukeplan
        if not funnet_url and reserve_url:
            funnet_url = reserve_url
            funnet_uke = forrige_uke

        # Fallback 2: Nyeste PDF/fil på siden
        if not funnet_url and forste_pdf_url:
            funnet_url = forste_pdf_url
            funnet_uke = innevaarende_uke

        resultater[trinn] = {
            "uke": funnet_uke,
            "pdf_url": funnet_url,
            "status": "OK" if funnet_url else "Ingen ukeplan funnet"
        }

        if funnet_url:
            print(f"{trinn}. trinn: Funnet (Uke {funnet_uke}) -> {funnet_url}")
        else:
            print(f"{trinn}. trinn: Ikke funnet (Ingen relevante lenker)")

    except Exception as e:
        resultater[trinn] = {"uke": innevaarende_uke, "pdf_url": None, "status": f"Feil: {e}"}
        print(f"{trinn}. trinn: Feil ved henting ({e})")

# Lagre filen
with open('ukeplaner.json', 'w', encoding='utf-8') as f:
    json.dump(resultater, f, ensure_ascii=False, indent=2)

print("\nFerdig! Genererte 'ukeplaner.json'.")
