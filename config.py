# config.py
# Konfiguracija aplikacije za praćenje vijesti (press clipping)

# Ključne riječi koje pratimo. Za svaku riječ se automatski generiše
# Google News RSS pretraga (glavni izvor vijesti) - ne treba ručno
# dodavati portale za ovo, dešava se automatski u fetcher.py.
# Provjera nije osjetljiva na velika/mala slova.
KEYWORDS = [
    "Jahorina",
    "Olimpijski centar Jahorina",
]

# Dodatne varijacije/sinonimi ključnih riječi - pretražuju se kao zasebni
# Google News upiti (pored KEYWORDS) da se proširi pokrivenost pretrage.
# Pronađeni članci se i dalje označavaju (taguju) prema tome koja riječ iz
# KEYWORDS liste se pojavljuje u naslovu/tekstu - varijacije samo šire mrežu
# pretrage, ne dodaju nove kategorije.
KEYWORD_VARIATIONS = [
    "OC Jahorina",
    "Olimpijski centar Jahorina",
    "Jahorina olympic",
    "Jahorina skijanje",
    "Jahorina turizam",
    "žičara Jahorina",
    "skijanje Jahorina 2026",
    "Jahorina zimovanje",
    "Jahorina ljetovanje",
    "Jahorina smještaj",
    "Jahorina vremenska prognoza",
    "Jahorina koncert",
    "Jahorina cijene skipasa",
    "Jahorina staze",
]

# Google News RSS parametri (jezik / region pretrage)
GOOGLE_NEWS_HL = "sr"     # jezik
GOOGLE_NEWS_GL = "BA"     # region
GOOGLE_NEWS_CEID = "BA:sr"

# Dodatni, klasični RSS feedovi portala koji se provjeravaju kao dopuna
# Google News pretrazi (svaki članak sa ovih feedova se provjerava na
# prisustvo bilo koje ključne riječi iz KEYWORDS liste).
# NAPOMENA: portali povremeno mijenjaju adrese svojih RSS feedova - ako
# neki feed prestane da vraća rezultate, provjerite/ažurirajte adresu
# direktno na sajtu portala (obično se traži link "RSS" u podnožju sajta).
EXTRA_FEEDS = [
    {"name": "Klix.ba", "url": "https://www.klix.ba/rss"},
    {"name": "N1 BiH", "url": "https://ba.n1info.com/feed/"},
    {"name": "B92", "url": "https://www.b92.net/rss/b92/info"},
    {"name": "Index.hr", "url": "https://www.index.hr/rss/vijesti"},
    {"name": "Glas Srpske", "url": "https://www.glassrpske.com/rss"},
    {"name": "Radio Sarajevo", "url": "https://www.radiosarajevo.ba/rss"},
    {"name": "Avaz", "url": "https://avaz.ba/rss"},
    {"name": "Vijesti.me", "url": "https://www.vijesti.me/rss"},
    {"name": "24sata.hr", "url": "https://www.24sata.hr/feeds/aktualno.xml"},
    # RTS ne objavljuje RSS na adresi sa njihove /page/rss stranice - stvarni
    # XML endpoint pronađen provjerom te stranice je ispod.
    {"name": "RTS", "url": "https://www.rts.rs/page/stories/sr/rss.html"},
]

# Portali koji su probani ali NISU prošli provjeru (ne vraćaju validan RSS/XML)
# - ostavljeno kao napomena, ne koristi se u aplikaciji:
#   Nezavisne novine (https://www.nezavisne.com/rss - vraća HTML stranicu)
#   CDM (https://www.cdm.me/feed - blokirano Cloudflare zaštitom, HTTP 403)
#   Blic (https://www.blic.rs/rss/najnovije-vesti - vraća HTML stranicu)
#   Index.hr/rss/najnovije (HTTP 404 - portal već pokriven preko drugog feeda gore)
#   Jutarnji list (https://www.jutarnji.hr/rss - HTTP 404)

# Koliko često (u satima) se automatski provjeravaju feedovi u pozadini
CHECK_INTERVAL_HOURS = 2

# Koliko često (u satima) se automatski provjerava YouTube (odvojeno i rjeđe
# od RSS/Google News provjere, zbog dnevne kvote YouTube Data API-ja - 6
# provjera dnevno uz ~1600 units po provjeri ostaje ispod limita od 10.000).
YOUTUBE_CHECK_INTERVAL_HOURS = 4

# U koji sat (0-23) se jednom dnevno pokreće "duboka" pretraga Google News-a
# sa "when:30d" modifikatorom, koja hvata starije članke (do 30 dana unazad)
# koje redovna provjera možda nije uhvatila.
DEEP_CHECK_HOUR = 3

# Putanja do SQLite baze podataka
DATABASE_PATH = "clippings.db"
