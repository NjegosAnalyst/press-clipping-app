# Press Clipping App

Web aplikacija za praćenje vijesti sa portala (RSS feedova) po ključnim riječima. Aplikacija svaka 2 sata automatski provjerava sve feedove, pronalazi članke koji sadrže praćene ključne riječi i čuva ih u lokalnu SQLite bazu. Sve pronađene članke možete pregledati, filtrirati i izvesti u Excel.

## Šta vam je potrebno

- Python 3.9 ili noviji (provjerite sa `python3 --version`)
- Internet konekcija (za čitanje RSS feedova)

## Instalacija (radi se samo jednom)

1. Otvorite terminal i pozicionirajte se u folder aplikacije:

   ```bash
   cd press-clipping-app
   ```

2. Kreirajte virtuelno okruženje (preporučeno, ne obavezno):

   ```bash
   python3 -m venv venv
   source venv/bin/activate       # na Windowsu: venv\Scripts\activate
   ```

3. Instalirajte potrebne pakete:

   ```bash
   pip install -r requirements.txt
   ```

## Podešavanje portala i ključnih riječi

Otvorite fajl `config.py` i izmijenite:

- **`RSS_FEEDS`** — listu portala koje pratite. Za svaki portal upišite naziv i adresu njegovog RSS feeda:

  ```python
  RSS_FEEDS = [
      {"name": "Naziv portala", "url": "https://portal.ba/rss"},
      {"name": "Drugi portal", "url": "https://drugiportal.ba/feed"},
  ]
  ```

  RSS adresu portala obično nađete tako što na sajtu portala potražite link "RSS" (često u podnožju sajta) ili probate dodati `/rss`, `/feed` ili `/rss.xml` na adresu sajta.

- **`KEYWORDS`** — listu ključnih riječi koje pratite (npr. "Jahorina", "Olimpijski centar Jahorina", "Pahulja").

- **`CHECK_INTERVAL_HOURS`** — koliko često (u satima) se feedovi automatski provjeravaju. Podrazumijevano je `2`.

Nakon izmjene `config.py`, sačuvajte fajl — nije potrebno ništa dodatno instalirati.

## Pokretanje aplikacije

```bash
python3 app.py
```

U terminalu ćete vidjeti poruku da je server pokrenut na adresi `http://127.0.0.1:5000`. Otvorite tu adresu u browseru.

Prilikom prvog pokretanja baza (`clippings.db`) i tabele se automatski kreiraju — ne treba ništa ručno podešavati.

Aplikacija radi u pozadini: čim je pokrenuta, svaka 2 sata (ili interval koji ste podesili) automatski provjerava sve feedove dok terminal/proces ostaje otvoren. Za trenutnu provjeru bez čekanja, kliknite dugme **"Provjeri sada"** na vrhu stranice.

Da zaustavite aplikaciju, u terminalu pritisnite `Ctrl + C`.

## Korišćenje dashboard-a

- **Filteri** — možete filtrirati članke po izvoru (portalu), po ključnoj riječi i po datumskom opsegu (od–do). Klik na "Filtriraj" primjenjuje filtere, "Poništi" ih briše.
- **Izvezi u Excel** — dugme izvozi trenutno prikazane (filtrirane) članke u `.xlsx` fajl koji se odmah preuzima na računar.
- **Provjeri sada** — odmah pokreće provjeru svih feedova, bez čekanja na automatski raspored od 2 sata.

## Napomene

- Baza podataka je fajl `clippings.db` u folderu aplikacije — možete je kopirati/backupovati kao običan fajl.
- Isti članak se neće duplirati u bazi ako se pronađe više puta na istom feedu.
- Ako neki portal nema ispravan RSS feed ili je privremeno nedostupan, aplikacija tu grešku samo ispisuje u terminalu i nastavlja sa ostalim portalima — provjera se neće prekinuti.
- Za rad u produkciji (npr. 24/7 na serveru) preporučuje se pokretanje aplikacije preko procesnog menadžera (npr. `systemd`, `pm2`, ili `screen`/`tmux`) umjesto direktno iz terminala, kao i isključivanje `debug` moda u `app.py`.
