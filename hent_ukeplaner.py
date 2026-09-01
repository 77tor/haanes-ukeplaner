import datetime
import json
import requests
from bs4 import BeautifulSoup

# Riktige URL-er til trinnene på Hånes skole
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Finn inneværende uketall
dagens_dato = datetime.date.today()
innevaarende_uke = dagens_dato.isocalendar()[1]
print(f"Søker etter ukeplaner for uke {innevaarende_uke}...\n")

resultater = {}

for trinn, url in TRINN_URLER.items():
    try:
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        funnet_url = None
        
        # Finn alle lenker
        for a in soup.find_all('a', href=True):
            href = a['href']
            tekst = a.get_text(strip=True)
            kombinert = f"{tekst} {href}".lower()
            
            is_pdf = '.pdf' in href.lower() or '/fil/' in href.lower()
            
            # Matcher format som: "uke 36", "uke-36", "uke36", "arbeidsplan uke 36" osv.
            har_riktig_uke = (
                f"uke {innevaarende_uke}" in kombinert or 
                f"uke-{innevaarende_uke}" in kombinert or 
                f"uke{innevaarende_uke}" in kombinert
            )
            
            if is_pdf and har_riktig_uke:
                funnet_url = href if href.startswith('http') else f"https://www.minskole.no{href}"
                break

        resultater[trinn] = {
            "uke": innevaarende_uke,
            "pdf_url": funnet_url,
            "status": "OK" if funnet_url else f"Ingen ukeplan funnet for uke {innevaarende_uke}"
        }
        
        print(f"{trinn}. trinn: {'Funnet -> ' + funnet_url if funnet_url else 'Ikke funnet'}")

    except Exception as e:
        resultater[trinn] = {"uke": innevaarende_uke, "pdf_url": None, "status": f"Feil: {e}"}
        print(f"{trinn}. trinn: Feil ved henting ({e})")

# Lagre data til ukeplaner.json
with open('ukeplaner.json', 'w', encoding='utf-8') as f:
    json.dump(resultater, f, ensure_ascii=False, indent=2)

print("\nFerdig! Genererte 'ukeplaner.json'.")
