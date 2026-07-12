import streamlit as st
import pandas as pd
from io import StringIO
import os
import random
from datetime import datetime, timedelta
import requests
import base64
import re

try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except ModuleNotFoundError:
    PLOTLY_OK = False

st.set_page_config(page_title="Kupony Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 10% 0%, rgba(56, 189, 248, .13), transparent 30%),
            radial-gradient(circle at 92% 15%, rgba(129, 140, 248, .12), transparent 26%),
            #0b1220;
        color: #e7eefb;
    }
    [data-testid="stHeader"] { background: rgba(11, 18, 32, .72); }
    .block-container { max-width: 1240px; padding-top: 8.9rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: #f8fbff !important; letter-spacing: -.02em; }
    h2 { margin-top: 1.7rem !important; padding-bottom: .45rem; border-bottom: 1px solid rgba(148, 163, 184, .18); }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(26,39,64,.94), rgba(16,27,46,.94));
        border: 1px solid rgba(100, 116, 139, .28);
        border-radius: 15px; padding: 15px 16px; min-height: 112px;
        box-shadow: 0 10px 24px rgba(0,0,0,.16);
    }
    [data-testid="stMetricLabel"] { color: #aebed5 !important; font-size: .84rem; }
    [data-testid="stMetricValue"] { color: #f8fbff !important; font-weight: 700; }
    [data-testid="stDataFrame"] { border: 1px solid rgba(100,116,139,.25); border-radius: 13px; overflow: hidden; }
    [data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important; border-color: rgba(100,116,139,.25) !important;
        background: rgba(18, 28, 46, .72);
    }
    [data-testid="stExpander"] {
        border: 1px solid rgba(96,165,250,.42) !important;
        background: linear-gradient(135deg, rgba(20,40,70,.96), rgba(34,32,77,.90)) !important;
        box-shadow: 0 10px 26px rgba(0,0,0,.16);
        margin: .7rem 0 1.15rem;
    }
    @keyframes decisionPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(250, 204, 21, .45), 0 10px 26px rgba(0,0,0,.18); transform: translateY(0); }
        50% { box-shadow: 0 0 0 7px rgba(250, 204, 21, 0), 0 0 28px rgba(250, 204, 21, .30), 0 12px 28px rgba(0,0,0,.23); transform: translateY(-1px); }
    }
    [data-testid="stExpander"] {
        animation: decisionPulse 2.25s ease-in-out infinite;
        border: 1px solid rgba(250,204,21,.95) !important;
        background: linear-gradient(105deg, #7c2d12, #9a3412 48%, #78350f) !important;
    }
    [data-testid="stExpander"] summary { padding: .55rem .65rem; font-size: 1.06rem; font-weight: 800; color: #fff7d6 !important; letter-spacing: .01em; }
    [data-testid="stExpander"] summary:hover { color: #ffffff !important; }
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] { color: #e7eefb; }
    @media (max-width: 640px) {
      [data-testid="stExpander"] summary { font-size: .98rem; line-height: 1.4; }
    }
    .stButton > button {
        border-radius: 10px; border: 1px solid rgba(56,189,248,.55); color: #eaf8ff;
        background: linear-gradient(135deg, #0369a1, #2563eb); font-weight: 600;
    }
    .stButton > button:hover { border-color: #7dd3fc; background: linear-gradient(135deg, #0284c7, #4f46e5); }
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(129,140,248,.42); }
        50% { box-shadow: 0 0 18px 3px rgba(129,140,248,.25); }
        100% { box-shadow: 0 0 0 0 rgba(129,140,248,.42); }
    }
    .kupon-open { animation: pulseGlow 2.4s infinite; border-radius: 14px; }
    .hero-card {
        position: relative; overflow: hidden; padding: 28px 30px; border-radius: 20px;
        background: linear-gradient(125deg, rgba(18,33,57,.98), rgba(25,38,74,.93));
        border: 1px solid rgba(96,165,250,.30); box-shadow: 0 18px 48px rgba(0,0,0,.24);
    }
    .hero-card:after { content: ''; position: absolute; width: 260px; height: 260px; right: -85px; top: -130px; border-radius: 50%; background: rgba(56,189,248,.13); filter: blur(3px); }
    .hero-kicker { color:#7dd3fc; font-size:.75rem; letter-spacing:1.6px; font-weight:700; }
    .hero-title { color:#f8fbff; font-size:2.45rem; font-weight:800; margin:7px 0 7px; }
    .hero-title span { background: linear-gradient(90deg,#7dd3fc,#a5b4fc); -webkit-background-clip:text; color:transparent; }
    .hero-copy { color:#c6d4e9; max-width:760px; line-height:1.65; margin:0; }
    .version-pill { display:inline-block; margin-left:8px; color:#dbeafe; background:rgba(59,130,246,.18); border:1px solid rgba(96,165,250,.42); border-radius:999px; padding:6px 10px; font-size:.74rem; font-weight:800; letter-spacing:.7px; vertical-align:middle; }
    .live-pill { display:inline-block; margin-top:16px; color:#bbf7d0; background:rgba(34,197,94,.13); border:1px solid rgba(34,197,94,.31); border-radius:999px; padding:6px 11px; font-size:.78rem; font-weight:700; letter-spacing:.5px; }
    .top-nav { position:fixed; top:64px; left:50%; transform:translateX(-50%); z-index:99999; width:min(1220px, calc(100% - 24px)); display:flex; gap:8px; overflow-x:auto; padding:8px 10px 10px; scrollbar-width:thin; background:rgba(8,16,30,.91); border:1px solid rgba(96,165,250,.24); border-radius:14px; box-shadow:0 10px 28px rgba(0,0,0,.28); }
    .top-nav a { flex:0 0 auto; text-decoration:none; color:#cfe4ff; background:rgba(20,35,58,.82); border:1px solid rgba(96,165,250,.34); border-radius:999px; padding:8px 12px; font-size:.81rem; font-weight:700; transition:.18s; }
    .top-nav a:hover { color:#fff; border-color:#7dd3fc; background:rgba(30,58,100,.95); transform:translateY(-1px); }
    .top-nav .nav-primary { color:#ecfdf5; background:linear-gradient(135deg,#047857,#0f766e); border-color:rgba(110,231,183,.62); }
    .section-anchor { display:block; height:1px; visibility:hidden; scroll-margin-top:132px; }
    @media (max-width: 640px) {
      .block-container { padding: 8.2rem .75rem 2rem; }
      .hero-card { padding: 22px 20px; border-radius: 16px; }
      .hero-title { font-size: 2rem; }
      .top-nav { top:52px; width:calc(100% - 16px); gap:7px; padding:7px 8px; border-radius:12px; }
      .top-nav a { padding:7px 10px; font-size:.75rem; }
    }
    </style>
    <nav class='top-nav' aria-label='Nawigacja panelu'>
      <a href='#home'>⌂ Home</a><a href='#statystyki'>📊 Statystyki</a><a href='#typy'>🎯 Typy</a><a href='#wyniki-live'>🔴 Wyniki live</a>
      <a href='#kalkulatory'>🧮 Kalkulatory</a><a href='#archiwum'>🗂 Archiwum</a><a class='nav-primary' href='#dodaj-typ'>✚ Dodaj typ</a>
    </nav>
    <span id='home' class='section-anchor'></span>
    <div class='hero-card'>
        <div class='hero-kicker'>⚖️ INTELIGENTNY PANEL WERDYKTÓW</div>
        <div class='hero-title'>Sędzia <span>AI</span><span class='version-pill'>v27</span></div>
        <p class='hero-copy'><b>Sędzia szuka typów i eliminuje złe decyzje.</b><br>
        Samodzielna analiza, dyscyplina banku i transparentne rozliczenia — w jednym miejscu.</p>
        <div class='live-pill'>● SYSTEM AKTYWNY</div>
    </div>
    """,
    unsafe_allow_html=True
)

with st.expander("🧠 KLIKNIJ I ZOBACZ, JAK SĘDZIA PODEJMUJE DECYZJE  •  Research. Nauka na wynikach. Ewolucja zasad."):
    st.markdown(
        "**Sędzia AI samodzielnie szuka wartościowych typów.** Przed każdym werdyktem prowadzi wielowarstwowy research: analizuje statystyki, formę, kontekst meczu, kursy i value, newsy, składy, absencje oraz sygnały z mediów społecznościowych, lokalnych źródeł, X, Reddita i forów kibicowskich.\n\n"
        "Każdy rozliczony kupon trafia do jego pamięci operacyjnej. Sędzia porównuje własny werdykt z przebiegiem meczu, rozpoznaje błędy analizy i błędy wykonawcze, a następnie aktualizuje profile lig, filtry oraz zasady działania. Nowe reguły najpierw przechodzą test, a później są zostawiane, korygowane albo usuwane.\n\n"
        "**Sędzia nie szuka większej liczby typów — szuka lepszych decyzji. Z każdym rozliczeniem jego system staje się trudniejszy do oszukania przez przypadek.**"
    )


MIESIACE_PL = {1:"Styczeń",2:"Luty",3:"Marzec",4:"Kwiecień",5:"Maj",6:"Czerwiec",
               7:"Lipiec",8:"Sierpień",9:"Wrzesień",10:"Październik",11:"Listopad",12:"Grudzień"}

def github_get(path):
    token = st.secrets["GITHUB_TOKEN"]
    repo = "Maruha3000/kupony-dashboard"
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        file_data = r.json()
        content = base64.b64decode(file_data["content"]).decode("utf-8")
        return content, file_data["sha"]
    return None, None

def github_put(path, content_str, sha, message):
    token = st.secrets["GITHUB_TOKEN"]
    repo = "Maruha3000/kupony-dashboard"
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    payload = {"message": message, "content": encoded}
    if sha:
        payload["sha"] = sha
    return requests.put(url, headers=headers, json=payload)

def rozbij_rynek(rynek, sport="", mecz=""):
    import re
    raw = " ".join(str(rynek or "").strip().split()); low = raw.lower().replace(",", ".")
    m = re.search(r"\b(over|under)\s*(\d+(?:[.,]\d+)?)", raw, re.I)
    if m:
        opis = f"{m.group(1).capitalize()} {m.group(2).replace(',', '.')}"
        if "set" in low: return "Sety — suma meczu", opis + " sety"
        if "gem" in low: return "Gemy — suma meczu", opis + " gemów"
        if "pkt" in low or "punkt" in low: return "Punkty — suma meczu", opis + " pkt"
        if "hokej" in str(sport).lower() or "60min" in low: return "Gole — suma meczu (hokej)", opis + " goli"
        return "Gole — suma meczu", opis + " goli"
    if "btts" in low: return "BTTS", "Tak" if "yes" in low or "tak" in low else "Nie"
    if "handicap" in low or re.search(r"(?<!\d)[+-]\d+(?:[.,]\d+)?$", low): return "Handicap", re.sub(r"(?i)\b(handicap|hcp)\b", "", raw).strip()
    if any(x in low for x in [" ml", "wygrywa", "to win", "zwycięzca", "1x2"]): return "Zwycięzca meczu", re.sub(r"(?i)\s*(ml|to win|wygrywa)", "", raw).strip()
    if "win to nil" in low: return "Wygrana do zera", raw
    if "double chance" in low: return "Podwójna szansa", raw.split()[-1]
    return "Inne", raw

def dodaj_pola_rynku(df):
    df = df.copy()
    p = df.apply(lambda r: rozbij_rynek(r.get("Rynek", ""), str(r.get("Sport", "")), r.get("Mecz", "")), axis=1)
    df["Kategoria rynku"] = [x[0] for x in p]
    df["Typ / selekcja"] = [x[1] for x in p]
    return df

def normalizuj_rynek(wartosc): return str(wartosc)
def normalizuj_kolumne_rynku(df, kolumna): return df.copy()

# --- Jednorazowa migracja kwot: skala x100 ---
SKALA_KWOT = 100

def przeskaluj_stawki_x100(df, kolumna="Stawka"):
    """Skaluje stare stawki (0.50/1.00) do 50/100; nowe stawki nie są mnożone ponownie."""
    if kolumna not in df.columns or df.empty:
        return df.copy(), False
    wynik = df.copy()
    liczby = pd.to_numeric(wynik[kolumna].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    # Stare zapisy miały stawki najwyżej kilka GBP; nowe są od 50 GBP wzwyż.
    do_zmiany = liczby.notna() & (liczby > 0) & (liczby < 10)
    if not do_zmiany.any():
        return wynik, False
    liczby.loc[do_zmiany] = liczby.loc[do_zmiany] * SKALA_KWOT
    wynik[kolumna] = liczby.where(liczby.notna(), wynik[kolumna])
    return wynik, True

# --- Wyniki piłki nożnej: football-data.org ---
def _nazwa_do_porownania(nazwa):
    tekst = str(nazwa or "").lower()
    tekst = tekst.translate(str.maketrans("ąćęłńóśźż", "acelnoszz"))
    return set(re.findall(r"[a-z0-9]+", tekst))

def _podziel_mecz(mecz):
    return re.split(r"\s+(?:vs|v|-)\s+", str(mecz), maxsplit=1, flags=re.I)

@st.cache_data(ttl=60, show_spinner=False)
def pobierz_mecze_pilki(data_iso, token):
    url = "https://api.football-data.org/v4/matches"
    response = requests.get(url, headers={"X-Auth-Token": token}, params={"date": data_iso}, timeout=12)
    response.raise_for_status()
    return response.json().get("matches", [])

def znajdz_wynik_dla_kuponu(mecz_kuponu, mecze_api):
    strony = _podziel_mecz(mecz_kuponu)
    if len(strony) != 2: return None
    a, b = _nazwa_do_porownania(strony[0]), _nazwa_do_porownania(strony[1])
    if not a or not b: return None
    for mecz in mecze_api:
        home = _nazwa_do_porownania(mecz.get("homeTeam", {}).get("name", ""))
        away = _nazwa_do_porownania(mecz.get("awayTeam", {}).get("name", ""))
        direct = len(a & home) > 0 and len(b & away) > 0
        reversed_order = len(a & away) > 0 and len(b & home) > 0
        if direct or reversed_order: return mecz
    return None

def opis_statusu_meczu(mecz):
    status = mecz.get("status", "SCHEDULED")
    minute = mecz.get("minute")
    mapa = {"IN_PLAY":"🔴 W grze", "PAUSED":"⏸ Przerwa", "TIMED":"🕒 Zaplanowany", "SCHEDULED":"🕒 Zaplanowany", "FINISHED":"🏁 Zakończony", "POSTPONED":"⚠️ Przełożony", "CANCELLED":"⚠️ Odwołany", "SUSPENDED":"⚠️ Przerwany"}
    wynik = mapa.get(status, status)
    return f"{wynik} ({minute}')" if status == "IN_PLAY" and minute is not None else wynik

@st.cache_data(ttl=60, show_spinner=False)
def pobierz_mecze_tenisa(data_iso):
    url = "https://www.thesportsdb.com/api/v1/json/123/eventsday.php"
    response = requests.get(url, params={"d": data_iso, "s": "Tennis"}, timeout=12)
    response.raise_for_status()
    return response.json().get("events", []) or []

def _podobny_token(tokeny_a, tokeny_b):
    # Obsługuje polskie znaki i odmiany bez końcowej litery, np. Nosková / Noskova.
    for a in tokeny_a:
        for b in tokeny_b:
            if a == b or (len(a) >= 5 and len(b) >= 5 and (a.startswith(b[:5]) or b.startswith(a[:5]))):
                return True
    return False

def znajdz_wynik_tenisa(mecz_kuponu, mecze_api):
    strony = _podziel_mecz(mecz_kuponu)
    if len(strony) != 2: return None
    a, b = _nazwa_do_porownania(strony[0]), _nazwa_do_porownania(strony[1])
    for mecz in mecze_api:
        nazwa = _nazwa_do_porownania(mecz.get("strEvent", ""))
        if a and b and _podobny_token(a, nazwa) and _podobny_token(b, nazwa):
            return mecz
    return None


status_dnia_placeholder = st.empty()
licznik_placeholder = st.empty()
ostatni_werdykt_placeholder = st.empty()

st.markdown(
    """
    <div style='background: linear-gradient(90deg, #1c1f26, #232838); border:1px dashed #4a90e2;
                border-radius:10px; padding:12px 18px; margin:10px 0 6px 0; text-align:center;'>
        <span style='font-size:0.92rem; color:#9fc2ec;'>
            🔧 <b>Sąd w budowie:</b> wkrótce będziesz mógł zadać Sędziemu własne pytanie i otrzymać werdykt na żywo — Sędzia już się do tego szykuje.
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

col_zapytaj1, col_zapytaj2 = st.columns([4, 1])
col_zapytaj1.text_input(
    "Zapytaj Sędziego",
    placeholder="np. Czy warto obstawić Over 2.5 w meczu X vs Y?",
    disabled=True,
    label_visibility="collapsed"
)
col_zapytaj2.button("Zapytaj", disabled=True, use_container_width=True)
st.caption("🔒 Funkcja pytań do Sędziego jest jeszcze w budowie.")
st.divider()

czerwiec_data = """Data,Sport,Rozgrywki,Mecz,Rynek,Pewnosc,Stawka,Kurs,Godzina,Status
03.06.2026,Pilka,Friendly,Poland vs Nigeria,Over 2.5 goli,Ryzykowny,0.50,2.00,19:45,WYGRANA
03.06.2026,Tenis,ATP Roland Garros,Berrettini vs Arnaldi,Berrettini to win,Ryzykowny,0.50,1.50,19:15,PRZEGRANA
03.06.2026,Hokej,NHL SCF G2,Vegas vs Carolina,Carolina ML,Ryzykowny,0.50,1.95,01:00,WYGRANA
04.06.2026,Pilka,Friendly,France vs Ivory Coast,BTTS Yes,Ryzykowny,0.50,1.92,20:10,WYGRANA
04.06.2026,Tenis,WTA Roland Garros,Shnaider vs Chwalinska,Chwalinska to win,Ryzykowny,0.50,2.47,15:00,WYGRANA
04.06.2026,Tenis,WTA Roland Garros,Kostyuk vs Andreeva,Kostyuk to win,Ryzykowny,0.50,1.78,11:00,PRZEGRANA
05.06.2026,Tenis,ATP Roland Garros,Zverev vs Mensik,Mensik Set Hcp 1.5,Ryzykowny,0.50,2.25,13:30,PRZEGRANA
05.06.2026,Tenis,ATP Roland Garros,Arnaldi vs Cobolli,Over 3.5 sety,Ryzykowny,0.50,1.65,19:00,VOIDED
05.06.2026,Koszykowka,NBA Finals G2,Spurs vs Knicks,Under 215.5 pkt,Ryzykowny,0.50,1.80,01:30,WYGRANA
06.06.2026,Hokej,NHL SCF G3,Carolina vs Vegas,Vegas ML,Ryzykowny,0.50,1.91,01:00,WYGRANA
07.06.2026,Tenis,ATP Roland Garros finał,Zverev vs Cobolli,Over 36.5 gemów,Ryzykowny,0.50,1.83,14:00,WYGRANA
07.06.2026,Hokej,NHL SCF G4,Carolina vs Vegas,Over 5.5 goli,Ryzykowny,0.50,1.85,01:00,WYGRANA
07.06.2026,Koszykowka,NBA Finals G3,Spurs vs Knicks,Under 215.5 pkt,Ryzykowny,0.50,1.91,01:30,PRZEGRANA
14.06.2026,Pilka,MS 2026 Gr F,Netherlands vs Japan,Under 2.5 goli,Ryzykowna,0.50,1.79,21:00,PRZEGRANA
14.06.2026,Hokej,NHL SCF G6,Carolina @ Vegas,Under 5.5 goli,Ryzykowna,0.50,2.10,01:00,WYGRANA
15.06.2026,Pilka,MS 2026 Gr G,Belgia - Egipt,Under 2.5 goli,Ryzykowna,0.50,1.80,21:00,WYGRANA
16.06.2026,Pilka,MS 2026 Gr J,Argentyna - Algieria,Under 2.5 goli,Ryzykowna,0.50,1.90,02:00,PRZEGRANA
17.06.2026,Pilka,MS 2026 Gr L,Anglia - Chorwacja,England Win To Nil,Ryzykowna,0.50,2.70,wieczorem,PRZEGRANA
19.06.2026,Pilka,MS 2026 Gr C,Scotland vs Morocco,Morocco Wygrywa,Sredni,1.00,1.67,23:00,WYGRANA
20.06.2026,Pilka,MS 2026 Gr E,Germany vs Ivory Coast,BTTS Yes,Sredni,1.00,1.67,21:00,WYGRANA
21.06.2026,Pilka,MS 2026 Gr G,Belgium vs Iran,Over 2.5,Sredni,1.00,1.79,20:00,PRZEGRANA
22.06.2026,Pilka,MS Gr J,Argentina vs Austria,BTTS Yes,Sredni,1.00,1.90,18:00,PRZEGRANA
22.06.2026,Pilka,MS Gr I,France vs Iraq,France -2.5,Ryzykowny,0.50,1.76,22:00,WYGRANA
22.06.2026,Pilka,MS Gr I,Norway vs Senegal,Over 2.5,Sredni,1.00,1.85,01:00,WYGRANA
23.06.2026,Pilka,MS R32,Portugal vs Uzbekistan,Over 2.5,-,0.00,0,-,SKIP
23.06.2026,Pilka,MS R32,England vs Ghana,BTTS Yes,Ryzykowny,0.50,1.83,-,PRZEGRANA
26.06.2026,Pilka,MS Gr I,Norway vs France,Over 2.5,Sredni,1.00,1.50,20:00,WYGRANA
27.06.2026,Pilka,MS Gr K MD3,Colombia vs Portugal,Over 2.5,Ryzykowny,0.50,2.05,00:30,PRZEGRANA
28.06.2026,Pilka,MS R32,South Africa vs Canada,Under 2.5,Ryzykowny,0.50,1.72,20:00,WYGRANA
29.06.2026,Pilka,MS R32,Germany vs Paraguay,Under 2.5,Sredni,1.00,2.05,21:30,WYGRANA
30.06.2026,Pilka,MS R32,Ivory Coast vs Norway,Over 2.5,Sredni,1.00,1.80,18:00,WYGRANA
"""

lipiec_data = """Data,Sport,Rozgrywki,Mecz,Rynek,Pewnosc,Stawka,Kurs,Godzina,Status
01.07.2026,Pilka,MS 2026 R32,England vs DR Congo,England -1.5,Ryzykowny,0.50,1.89,17:00,PRZEGRANA
01.07.2026,Pilka,MS 2026 R32,Belgium vs Senegal,Belgium ML,Sredni,1.00,2.10,21:00,WYGRANA
01.07.2026,Pilka,MS 2026 R32,Belgium vs Senegal,BTTS Yes,Sredni,1.00,1.80,21:00,WYGRANA
01.07.2026,Pilka,MS 2026 R32,USA vs Bosnia & Herz.,Under 2.5 gole,Ryzykowny,0.50,2.08,01:00 (2.VII),WYGRANA
02.07.2026,Pilka,MS 2026 R32,Spain vs Austria,Under 2.5 gole,Sredni,1.00,1.80,20:00,PRZEGRANA
03.07.2026,Pilka,MS 2026 R32,Switzerland vs Algeria,BTTS Yes,Sredni,1.00,1.80,04:00 (3.VII),PRZEGRANA
03.07.2026,Pilka,MS 2026 R32,Australia vs Egypt,BTTS Yes,Ryzykowny,0.50,2.00,19:00 (3.VII),WYGRANA
04.07.2026,Pilka,MS 2026 R32,Colombia vs Ghana,Over 2.5,Sredni,1.00,1.90,01:30 (4.VII),PRZEGRANA
05.07.2026,Pilka,MS 2026 R16,Canada vs Morocco,Under 2.5 gole,Ryzykowny,0.50,1.75,18:00,PRZEGRANA
05.07.2026,Pilka,MS 2026 R16,Paraguay vs France,France -1.5,Sredni,1.00,1.62,22:00,PRZEGRANA
05.07.2026,Pilka,Friendly/MS,Brazil vs Norway,Over 2.5 gole,Sredni,1.00,1.73,20:00,WYGRANA
05.07.2026,Pilka,Friendly/MS,Mexico vs England,Under 1.5 gole,Ryzykowny,0.50,2.85,01:00 (06.07),PRZEGRANA
"""

df_czerwiec = pd.read_csv(StringIO(czerwiec_data))
df_czerwiec["Analiza"] = ""
df_czerwiec = normalizuj_kolumne_rynku(df_czerwiec, "Rynek")
df_czerwiec, _ = przeskaluj_stawki_x100(df_czerwiec)

df_lipiec = pd.read_csv(StringIO(lipiec_data))
df_lipiec["Analiza"] = ""
df_lipiec = normalizuj_kolumne_rynku(df_lipiec, "Rynek")
df_lipiec, _ = przeskaluj_stawki_x100(df_lipiec)

content, sha_a = github_get("analizy.csv")
if content:
    df_analizy = pd.read_csv(StringIO(content))
else:
    df_analizy = pd.DataFrame(columns=["data","sport","mecz","rynek","pewnosc","stawka","kurs","wynik","analiza"])
    sha_a = None

arch_cols = ["Data","Sport","Rozgrywki","Mecz","Rynek","Pewnosc","Stawka","Kurs","Godzina","Status","Analiza"]
content_arch, sha_arch = github_get("archiwum.csv")
if content_arch:
    df_archiwum = pd.read_csv(StringIO(content_arch))
else:
    df_archiwum = pd.DataFrame(columns=arch_cols)
    sha_arch = None

# Ujednolicenie działa dla danych z GitHub zanim trafią do archiwum,
# rankingu rynków, statystyk i wykresów.
df_analizy = normalizuj_kolumne_rynku(df_analizy, "rynek")
df_archiwum = normalizuj_kolumne_rynku(df_archiwum, "Rynek")
df_analizy, analizy_przeskalowane = przeskaluj_stawki_x100(df_analizy, "stawka")
df_archiwum, archiwum_przeskalowane = przeskaluj_stawki_x100(df_archiwum, "Stawka")

# Zapis następuje tylko raz, gdy wykryto starą skalę 0.50/1.00.
if analizy_przeskalowane:
    bufor = StringIO(); df_analizy.to_csv(bufor, index=False)
    github_put("analizy.csv", bufor.getvalue(), sha_a, "Migracja stawek x100")
if archiwum_przeskalowane:
    bufor = StringIO(); df_archiwum.to_csv(bufor, index=False)
    github_put("archiwum.csv", bufor.getvalue(), sha_arch, "Migracja stawek x100")
if analizy_przeskalowane or archiwum_przeskalowane:
    st.info("Kwoty historyczne zostały jednorazowo przeskalowane x100 i zapisane w repozytorium danych.")

if len(df_analizy) > 0:
    df_analizy["data_dt"] = pd.to_datetime(df_analizy["data"], format="%Y-%m-%d", errors="coerce")
    df_analizy = df_analizy.sort_values("data_dt", ascending=False).reset_index(drop=True)

    top6_idx = df_analizy.index[:6].tolist()
    open_idx = df_analizy.index[df_analizy["wynik"] == "OPEN"].tolist()
    keep_idx = sorted(set(top6_idx) | set(open_idx))
    move_idx = [i for i in df_analizy.index if i not in keep_idx]

    if len(move_idx) > 0:
        do_przeniesienia = df_analizy.loc[move_idx].copy()
        nowe_wiersze = []
        for _, row in do_przeniesienia.iterrows():
            data_fmt = row["data_dt"].strftime("%d.%m.%Y") if pd.notna(row["data_dt"]) else row["data"]
            nowe_wiersze.append({
                "Data": data_fmt, "Sport": row["sport"], "Rozgrywki": "",
                "Mecz": row["mecz"], "Rynek": row["rynek"], "Pewnosc": row["pewnosc"],
                "Stawka": row["stawka"], "Kurs": row["kurs"], "Godzina": "-",
                "Status": row["wynik"], "Analiza": row.get("analiza", "")
            })
        df_archiwum = pd.concat([df_archiwum, pd.DataFrame(nowe_wiersze)], ignore_index=True)
        df_analizy = df_analizy.loc[keep_idx].reset_index(drop=True)

        buf1 = StringIO(); df_archiwum.to_csv(buf1, index=False)
        github_put("archiwum.csv", buf1.getvalue(), sha_arch, "Auto-archiwizacja starych typow")

        df_analizy_zapis = df_analizy.drop(columns=["data_dt"])
        buf2 = StringIO(); df_analizy_zapis.to_csv(buf2, index=False)
        github_put("analizy.csv", buf2.getvalue(), sha_a, "Usunieto zarchiwizowane typy")

    df_analizy = df_analizy.drop(columns=["data_dt"])

# Dane zapisane na stałe: historyczne miesiące oraz archiwum GitHub.
df_archiwum_full = pd.concat([df_czerwiec, df_lipiec, df_archiwum], ignore_index=True, sort=False)
df_archiwum_full["Data_dt"] = pd.to_datetime(
    df_archiwum_full["Data"], format="%d.%m.%Y", errors="coerce"
)

# Rozliczone kupony z analizy pozostają w ostatnich 6 na stronie głównej,
# ale od razu są doliczane do statystyk, wykresów i widoku archiwum.
df_biezace_rozliczone = df_analizy[
    df_analizy["wynik"].isin(["WYGRANA", "PRZEGRANA"])
].copy()

if not df_biezace_rozliczone.empty:
    df_biezace_rozliczone["Data_dt"] = pd.to_datetime(
        df_biezace_rozliczone["data"], format="%Y-%m-%d", errors="coerce"
    )
    df_biezace_rozliczone = pd.DataFrame({
        "Data": df_biezace_rozliczone["Data_dt"].dt.strftime("%d.%m.%Y"),
        "Sport": df_biezace_rozliczone["sport"],
        "Rozgrywki": "",
        "Mecz": df_biezace_rozliczone["mecz"],
        "Rynek": df_biezace_rozliczone["rynek"],
        "Pewnosc": df_biezace_rozliczone["pewnosc"],
        "Stawka": pd.to_numeric(df_biezace_rozliczone["stawka"], errors="coerce").fillna(0),
        "Kurs": pd.to_numeric(df_biezace_rozliczone["kurs"], errors="coerce").fillna(0),
        "Godzina": "-",
        "Status": df_biezace_rozliczone["wynik"],
        "Analiza": df_biezace_rozliczone["analiza"],
        "Data_dt": df_biezace_rozliczone["Data_dt"],
    })
else:
    df_biezace_rozliczone = pd.DataFrame(columns=df_archiwum_full.columns)

# Tabela raportowa nie jest zapisywana do GitHub. Dzięki temu ten sam kupon
# nie zostanie zdublowany, gdy później automatycznie trafi do archiwum.csv.
df_raport_full = pd.concat(
    [df_archiwum_full, df_biezace_rozliczone], ignore_index=True, sort=False
)
df_raport_full["Stawka"] = pd.to_numeric(df_raport_full["Stawka"], errors="coerce").fillna(0)
df_raport_full["Kurs"] = pd.to_numeric(df_raport_full["Kurs"], errors="coerce").fillna(0)
df_raport_full = dodaj_pola_rynku(df_raport_full)

# --- Dane pomocnicze do sekcji "żywych" ---
rozliczone_all = df_raport_full[
    df_raport_full["Status"].isin(["WYGRANA", "PRZEGRANA"])
].copy()

# Nagłówek statusu dnia (ostatnie 24h)
dzis_ts = pd.Timestamp(datetime.today().date())
ostatnie_24h = rozliczone_all[rozliczone_all["Data_dt"] >= dzis_ts - timedelta(days=1)]
w24 = (ostatnie_24h["Status"] == "WYGRANA").sum()
p24 = (ostatnie_24h["Status"] == "PRZEGRANA").sum()

if len(ostatnie_24h) == 0:
    status_txt, status_kolor, status_emoji = "Sędzia czeka na rozstrzygnięcia", "#4a4a1e", "⏳"
elif w24 > p24:
    status_txt, status_kolor, status_emoji = "Sędzia w dobrej formie", "#1e5e2e", "🟢"
elif w24 < p24:
    status_txt, status_kolor, status_emoji = "Sędzia dziś czujny na błędy", "#6e1e1e", "🔴"
else:
    status_txt, status_kolor, status_emoji = "Sędzia na neutralnym kursie", "#4a4a1e", "🟡"

status_dnia_placeholder.markdown(
    f"""
    <div style='background:linear-gradient(135deg, {status_kolor}, #172554); border:1px solid rgba(255,255,255,.12); padding:14px 18px; border-radius:14px;
                text-align:center; margin-bottom:10px; color:white; font-weight:600; font-size:1.05rem;'>
        {status_emoji} {status_txt} — ostatnie 24h: {w24} wygrane / {p24} przegrane
    </div>
    """,
    unsafe_allow_html=True
)

# Licznik dni działania i liczba werdyktów
if rozliczone_all["Data_dt"].notna().any():
    pierwsza_data = rozliczone_all["Data_dt"].min()
    dni_dzialania = max((dzis_ts - pierwsza_data).days, 0)
else:
    dni_dzialania = 0
liczba_werdyktow = len(rozliczone_all)

licznik_placeholder.caption(
    f"⚖️ Sędzia AI działa od {dni_dzialania} dni i wydał {liczba_werdyktow} werdyktów."
)

def koloruj_status(val):
    if val == "WYGRANA":
        return "background-color: #1e5e2e; color: white;"
    elif val == "PRZEGRANA":
        return "background-color: #6e1e1e; color: white;"
    elif val == "OPEN":
        return "background-color: #4a4a1e; color: white;"
    else:
        return "background-color: #3a3a3a; color: white;"

STATUS_KOLOR = {
    "WYGRANA": "#1e5e2e",
    "PRZEGRANA": "#6e1e1e",
    "OPEN": "#4a4a1e",
}

# --- Sekcja: Ostatni werdykt (wyróżniona karta) ---
if len(df_analizy) > 0:
    ow = df_analizy.sort_values("data", ascending=False).iloc[0]
    ow_kolor = STATUS_KOLOR.get(ow["wynik"], "#3a3a3a")
    ow_pulse_class = "kupon-open" if ow["wynik"] == "OPEN" else ""
    ostatni_werdykt_placeholder.markdown(
        f"""
        <div class="{ow_pulse_class}" style='background:linear-gradient(135deg,#16243b,#111c30); border:1px solid rgba(100,116,139,.32);
                    border-left:6px solid {ow_kolor}; border-radius:12px; padding:18px 22px;
                    margin-bottom:14px;'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                <span style='font-size:0.85rem; color:#8a8a8a; text-transform:uppercase; letter-spacing:1px;'>
                    ⚖️ Ostatni werdykt
                </span>
                <span style='background-color:{ow_kolor}; color:white; padding:4px 12px;
                              border-radius:6px; font-weight:600; font-size:0.85rem;'>{ow["wynik"]}</span>
            </div>
            <p style='font-size:1.2rem; font-weight:700; margin:0 0 4px 0; color:#f0f0f0;'>{ow["mecz"]}</p>
            <p style='font-size:0.9rem; color:#b0b0b0; margin:0 0 10px 0;'>{ow["data"]} — {ow["sport"]}</p>
            <p style='font-size:0.95rem; margin:0; color:#e0e0e0;'>
                <b>Rynek:</b> {ow["rynek"]} &nbsp;|&nbsp; <b>Pewność:</b> {ow["pewnosc"]} &nbsp;|&nbsp;
                <b>Stawka:</b> £{ow["stawka"]} &nbsp;|&nbsp; <b>Kurs:</b> {ow["kurs"]}
            </p>
            {"<p style='font-size:0.9rem; font-style:italic; color:#cfcfcf; margin-top:10px;'>" + str(ow.get("analiza","")) + "</p>" if str(ow.get("analiza","")).strip() else ""}
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<span id='statystyki' class='section-anchor'></span>", unsafe_allow_html=True)
st.subheader("📊 Statystyki")
st.caption("Szybki obraz skuteczności i wyniku w wybranym przedziale czasu.")
zakres_wyboru = st.selectbox("Przedział czasowy", ["Ostatnie 7 dni", "Ostatni miesiąc", "Cały okres"], index=2)

dzis = pd.Timestamp(datetime.today().date())
if zakres_wyboru == "Ostatnie 7 dni":
    data_od = dzis - timedelta(days=7)
elif zakres_wyboru == "Ostatni miesiąc":
    data_od = dzis - timedelta(days=30)
else:
    data_od = None

if data_od is not None:
    df_stats = df_raport_full[df_raport_full["Data_dt"] >= data_od].copy()
else:
    df_stats = df_raport_full.copy()

wygrane = df_stats[df_stats["Status"] == "WYGRANA"]
przegrane = df_stats[df_stats["Status"] == "PRZEGRANA"]
rozliczone = df_stats[df_stats["Status"].isin(["WYGRANA", "PRZEGRANA"])]

zysk = (wygrane["Stawka"] * wygrane["Kurs"]).sum() - wygrane["Stawka"].sum() - przegrane["Stawka"].sum()
suma_stawek = rozliczone["Stawka"].sum()
yield_pct = (zysk / suma_stawek * 100) if suma_stawek > 0 else 0
sredni_kurs = rozliczone["Kurs"].mean() if len(rozliczone) > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Liczba kuponów", len(df_stats))
win_rate = len(wygrane) / (len(wygrane) + len(przegrane)) * 100 if (len(wygrane) + len(przegrane)) > 0 else 0
col2.metric("Win rate", f"{win_rate:.0f}%")
col3.metric("Suma stawek", f"£{suma_stawek:.2f}")
col4.metric("Zysk / strata netto", f"£{zysk:+.2f}")
col5.metric("Yield (ROI)", f"{yield_pct:+.1f}%")

st.caption(f"Średni kurs zagranych kuponów: {sredni_kurs:.2f}")

# --- Odznaki / mikro-osiągnięcia ---
odznaki = []
if liczba_werdyktow >= 10:
    odznaki.append("🏅 10+ rozliczonych kuponów")
if liczba_werdyktow >= 50:
    odznaki.append("🏅 50+ rozliczonych kuponów")
if liczba_werdyktow >= 100:
    odznaki.append("🏅 100+ rozliczonych kuponów")

if len(rozliczone_all) > 0:
    seria_rozliczonych = rozliczone_all.sort_values("Data_dt")["Status"].tolist()
    najdluzsza_wygrana, biezaca_wygrana = 0, 0
    for s in seria_rozliczonych:
        if s == "WYGRANA":
            biezaca_wygrana += 1
            najdluzsza_wygrana = max(najdluzsza_wygrana, biezaca_wygrana)
        else:
            biezaca_wygrana = 0
    if najdluzsza_wygrana >= 3:
        odznaki.append("🎯 Seria 3+ wygranych z rzędu")
    if najdluzsza_wygrana >= 5:
        odznaki.append("🎯 Seria 5+ wygranych z rzędu")

    biezaca_seria, biezacy_status = 0, None
    for s in reversed(seria_rozliczonych):
        if biezacy_status is None:
            biezacy_status = s
            biezaca_seria = 1
        elif s == biezacy_status:
            biezaca_seria += 1
        else:
            break
else:
    biezaca_seria, biezacy_status = 0, None

if yield_pct > 0 and suma_stawek > 0:
    odznaki.append("📈 Dodatni yield w wybranym okresie")

if odznaki:
    st.markdown("**Odznaki:** " + "  ".join(
        f"<span style='background-color:#2a2f3a; padding:4px 10px; border-radius:14px; margin-right:6px; font-size:0.85rem;'>{o}</span>"
        for o in odznaki
    ), unsafe_allow_html=True)

if biezacy_status and biezaca_seria >= 2:
    seria_emoji = "🔥" if biezacy_status == "WYGRANA" else "⚠️"
    seria_slowo = "wygranych" if biezacy_status == "WYGRANA" else "przegranych"
    st.caption(f"{seria_emoji} Aktualna seria: {biezaca_seria} {seria_slowo} z rzędu")

st.divider()

# --- Ranking najlepszych rynków ---
st.subheader("🏆 Ranking rynków")
st.caption("Najskuteczniejsze rynki na podstawie rozliczonych kuponów.")
if len(rozliczone_all) > 0:
    ranking = rozliczone_all.groupby(["Sport", "Kategoria rynku"]).agg(
        Kupony=("Status", "count"), Wygrane=("Status", lambda x: (x == "WYGRANA").sum())
    ).reset_index()
    ranking["Rynek"] = ranking["Sport"] + " — " + ranking["Kategoria rynku"]
    ranking = ranking[ranking["Kupony"] >= 2].copy()
    ranking["Win rate %"] = (ranking["Wygrane"] / ranking["Kupony"] * 100).round(0)
    ranking = ranking.sort_values("Win rate %", ascending=False)

    if len(ranking) > 0:
        st.dataframe(ranking, use_container_width=True, hide_index=True)
        st.caption("Wykres pokazuje rynki z minimum 2 rozliczonymi kuponami.")
        ranking_chart = ranking.set_index("Rynek")[["Win rate %"]]
        st.bar_chart(ranking_chart, color="#4a90e2")
    else:
        st.info("Za mało danych, aby zbudować ranking rynków (min. 2 kupony na rynek).")
else:
    st.info("Brak rozliczonych kuponów do zbudowania rankingu.")

st.divider()

# --- Wykres trendu zysku w czasie ---
st.subheader("📈 Trend zysku Sędziego")
st.caption("Wynik narastająco — każdy rozliczony kupon ma znaczenie.")
if len(rozliczone_all) > 0:
    df_trend = rozliczone_all.sort_values("Data_dt").copy()
    df_trend["PL"] = df_trend.apply(
        lambda r: (r["Stawka"] * r["Kurs"] - r["Stawka"]) if r["Status"] == "WYGRANA" else -r["Stawka"],
        axis=1
    )
    df_trend["Kumulatywny zysk GBP"] = df_trend["PL"].cumsum()
    trend_chart = df_trend.groupby("Data_dt", as_index=True)["Kumulatywny zysk GBP"].last().to_frame()
    st.caption("Skumulowany zysk po każdym dniu z rozliczonym kuponem.")
    st.line_chart(trend_chart, color="#4a90e2")
else:
    st.info("Brak rozliczonych kuponów do zbudowania wykresu trendu.")

st.divider()

st.markdown("<span id='typy' class='section-anchor'></span>", unsafe_allow_html=True)
st.subheader("🎯 Najnowsze typy")
st.caption("Widoczne: 6 najnowszych typów + wszystkie ze statusem OPEN. Starsze rozliczone trafiają do archiwum.")

if len(df_analizy) > 0:
    for _, row in df_analizy.sort_values("data", ascending=False).iterrows():
        kolor = STATUS_KOLOR.get(row["wynik"], "#3a3a3a")
        if row["wynik"] == "OPEN":
            st.markdown('<div class="kupon-open">', unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{row['mecz']}**")
                st.caption(f"{row['data']} — {row['sport']}")
            with c2:
                st.markdown(
                    f"<div style='background-color:{kolor};color:white;padding:4px 10px;"
                    f"border-radius:6px;text-align:center;font-weight:600;'>{row['wynik']}</div>",
                    unsafe_allow_html=True
                )

            st.markdown(
                f"**Rynek:** {row['rynek']}  \n"
                f"**Pewność:** {row['pewnosc']}  \n"
                f"**Stawka:** £{row['stawka']}  |  **Kurs:** {row['kurs']}"
            )

            if str(row.get("analiza", "")).strip():
                st.markdown(f"_{row['analiza']}_")
        if row["wynik"] == "OPEN":
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Brak zapisanych analiz — dodaj pierwszy typ poniżej.")

st.divider()
st.markdown("<span id='wyniki-live' class='section-anchor'></span>", unsafe_allow_html=True)
st.subheader("🔴 Wyniki live")
st.caption("Piłka: football-data.org. Tenis: TheSportsDB (bezpłatne dane terminarza i rezultatów). Odświeżanie co 60 sekund.")

@st.fragment(run_every=60)
def panel_wynikow_live():
    otwarte_pilka = df_analizy[(df_analizy["wynik"] == "OPEN") & (df_analizy["sport"].str.lower() == "pilka")].copy()
    otwarte_tenis = df_analizy[(df_analizy["wynik"] == "OPEN") & (df_analizy["sport"].str.lower() == "tenis")].copy()
    if otwarte_pilka.empty and otwarte_tenis.empty:
        st.info("Brak otwartych kuponów piłkarskich ani tenisowych do śledzenia."); return
    if st.button("↻ Odśwież teraz", key="odswiez_wyniki_live"):
        pobierz_mecze_pilki.clear(); pobierz_mecze_tenisa.clear()
    dzis_api = datetime.utcnow().strftime("%Y-%m-%d")
    if not otwarte_pilka.empty:
        st.markdown("#### ⚽ Piłka nożna")
        if "FOOTBALL_DATA_API_KEY" not in st.secrets: st.warning("Brakuje FOOTBALL_DATA_API_KEY w Secrets Streamlit.")
        else:
            try: mecze_api = pobierz_mecze_pilki(dzis_api, st.secrets["FOOTBALL_DATA_API_KEY"])
            except requests.RequestException as blad: st.error(f"Nie udało się pobrać wyników piłki: {blad}"); mecze_api=[]
            for _, kupon in otwarte_pilka.iterrows():
                mecz = znajdz_wynik_dla_kuponu(kupon["mecz"], mecze_api)
                if mecz is None: st.warning(f"{kupon['mecz']} — nie znaleziono dziś w football-data.org."); continue
                score=mecz.get("score",{}).get("fullTime",{}); hs=score.get("home") if score.get("home") is not None else "–"; aw=score.get("away") if score.get("away") is not None else "–"
                try: start_txt=pd.to_datetime(mecz.get("utcDate"),utc=True).tz_convert("Europe/London").strftime("%d.%m.%Y, %H:%M BST")
                except Exception: start_txt="brak danych"
                st.markdown(f"**{mecz['homeTeam']['name']} {hs}:{aw} {mecz['awayTeam']['name']}**")
                st.caption(f"Start: {start_txt} · {opis_statusu_meczu(mecz)} · Kupon: {kupon['rynek']}")
    if not otwarte_tenis.empty:
        st.markdown("#### 🎾 Tenis")
        try: mecze_tenisa=pobierz_mecze_tenisa(dzis_api)
        except requests.RequestException as blad: st.error(f"Nie udało się pobrać danych tenisa: {blad}"); mecze_tenisa=[]
        for _, kupon in otwarte_tenis.iterrows():
            mecz=znajdz_wynik_tenisa(kupon["mecz"],mecze_tenisa)
            if mecz is None: st.warning(f"{kupon['mecz']} — nie znaleziono dziś w TheSportsDB."); continue
            hs=mecz.get("intHomeScore"); aw=mecz.get("intAwayScore"); wynik=f"{hs}:{aw}" if hs is not None and aw is not None else "– : –"
            start_raw=mecz.get("strTimestamp") or f"{mecz.get('dateEvent','')}T{mecz.get('strTime','')}"
            try: start_txt=pd.to_datetime(start_raw).tz_localize("Europe/London").strftime("%d.%m.%Y, %H:%M BST")
            except Exception: start_txt=mecz.get("strTime") or "brak danych"
            status=mecz.get("strStatus") or ("🏁 Zakończony" if hs is not None else "🕒 Zaplanowany / brak statusu live")
            st.markdown(f"**{mecz.get('strEvent', kupon['mecz'])} — {wynik}**")
            st.caption(f"Turniej: {mecz.get('strLeague','brak danych')} · Start: {start_txt} · {status} · Kupon: {kupon['rynek']}")
    st.caption(f"Ostatnia aktualizacja panelu: {datetime.now().strftime('%H:%M:%S')}")

panel_wynikow_live()

st.divider()
st.markdown("<span id='kalkulatory' class='section-anchor'></span>", unsafe_allow_html=True)
st.subheader("Kalkulatory")
st.caption("Narzędzia pomocnicze do kontroli stawki i obliczeń. Kalkulator Kelly pokazuje wynik matematyczny; stosuj ostrożny ułamek stawki.")

col_bank_calc, col_x_calc, col_kelly_calc = st.columns(3)

with col_bank_calc:
    st.markdown("### 💰 Bezpieczna stawka")
    st.write("Podaj aktualny bank, aby przeliczyć stawkę proporcjonalnie do ustalonej skali.")
    bank_bazowy = 2800.0
    stawki_bazowe = {"Pewny": 150.0, "Sredni": 100.0, "Ryzykowny": 50.0}
    bank_uzytkownika = st.number_input("Twój aktualny bank (GBP)", min_value=1.0, value=2800.0, step=50.0, key="bank_uzytkownika_input")
    pewnosc_bank_input = st.selectbox("Poziom pewności zakładu", ["Pewny", "Sredni", "Ryzykowny"], key="pewnosc_bank_select")

    wspolczynnik = bank_uzytkownika / bank_bazowy
    stawka_rekomendowana = round(stawki_bazowe[pewnosc_bank_input] * wspolczynnik, 2)
    procent_banku = (stawka_rekomendowana / bank_uzytkownika) * 100
    st.metric("Rekomendowana stawka", f"{stawka_rekomendowana:.2f} GBP")
    st.caption(f"To {procent_banku:.1f}% banku przy poziomie: {pewnosc_bank_input}.")

with col_x_calc:
    st.markdown("### 🧮 Kalkulator X")
    st.caption("Wzory: C = (A + B) / 2 oraz X = 100 / C.")
    calc_col1, calc_col2 = st.columns(2)
    with calc_col1:
        a = st.number_input("A", value=0.0, step=0.1, key="calc_a")
    with calc_col2:
        b = st.number_input("B", value=0.0, step=0.1, key="calc_b")
    c = (a + b) / 2
    st.metric("C (średnia A i B)", f"{c:.2f}")
    if c > 0:
        st.success(f"X = {100 / c:.4f}")
    elif c == 0:
        st.info("Wpisz wartości A i B większe od 0, aby obliczyć X.")
    else:
        st.error("C musi być większe od 0.")

with col_kelly_calc:
    st.markdown("### 📐 Kalkulator Kelly")
    st.caption("Wzór: f = (p × kurs - 1) / (kurs - 1). Ujemny wynik oznacza brak dodatniej przewagi.")
    kelly_bank = st.number_input("Bank do Kelly (GBP)", min_value=1.0, value=2800.0, step=50.0, key="kelly_bank_input")
    kelly_kurs = st.number_input("Kurs dziesiętny", min_value=1.01, value=2.00, step=0.01, format="%.2f", key="kelly_odds_input")
    kelly_prawdopodobienstwo = st.number_input("Szacowane prawdopodobieństwo (%)", min_value=0.0, max_value=100.0, value=55.0, step=1.0, key="kelly_probability_input")
    kelly_ulamek = st.selectbox("Ułamek stawki Kelly", ["1/4 Kelly", "1/2 Kelly", "Pełny Kelly"], index=0, key="kelly_fraction_select")
    mnoznik_kelly = {"1/4 Kelly": 0.25, "1/2 Kelly": 0.50, "Pełny Kelly": 1.0}[kelly_ulamek]
    p = kelly_prawdopodobienstwo / 100
    pelny_kelly = (p * kelly_kurs - 1) / (kelly_kurs - 1)
    procent_kelly = max(0.0, pelny_kelly) * mnoznik_kelly * 100
    stawka_kelly = kelly_bank * procent_kelly / 100
    if pelny_kelly > 0:
        st.metric("Stawka Kelly", f"{stawka_kelly:.2f} GBP", f"{procent_kelly:.2f}% banku")
        st.caption(f"Pełny Kelly: {pelny_kelly * 100:.2f}% banku; wybrano: {kelly_ulamek}.")
    else:
        st.metric("Stawka Kelly", "0.00 GBP", "Brak dodatniej przewagi")
        st.warning("Przy tych danych wzór Kelly nie rekomenduje stawki.")

st.divider()
st.markdown("<span id='archiwum' class='section-anchor'></span>", unsafe_allow_html=True)
st.subheader("Archiwum kuponów")

df_raport_full["MiesiacRok"] = df_raport_full["Data_dt"].apply(
    lambda d: f"{MIESIACE_PL[d.month]} {d.year}" if pd.notna(d) else "Nieznana data"
)
dostepne_miesiace = df_raport_full.sort_values("Data_dt", ascending=False)["MiesiacRok"].unique().tolist()

if len(dostepne_miesiace) > 0:
    wybrany_miesiac = st.selectbox("Wybierz miesiąc", dostepne_miesiace)
    df_miesiac = df_raport_full[df_raport_full["MiesiacRok"] == wybrany_miesiac].copy()
    kolumny_archiwum = ["Data", "Sport", "Rozgrywki", "Mecz", "Kategoria rynku", "Typ / selekcja", "Pewnosc", "Stawka", "Kurs", "Godzina", "Status", "Analiza"]
    df_miesiac = df_miesiac[[c for c in kolumny_archiwum if c in df_miesiac.columns]]

    c1, c2 = st.columns(2)
    sport_filter = c1.multiselect("Sport", options=df_miesiac["Sport"].unique(), default=df_miesiac["Sport"].unique())
    status_filter = c2.multiselect("Status", options=df_miesiac["Status"].unique(), default=df_miesiac["Status"].unique())

    df_filtered = df_miesiac[df_miesiac["Sport"].isin(sport_filter) & df_miesiac["Status"].isin(status_filter)]

    st.dataframe(
        df_filtered.style.map(koloruj_status, subset=["Status"]),
        use_container_width=True
    )
else:
    st.info("Brak danych archiwalnych.")

st.divider()
st.subheader("🔒 Zmień status kuponu")
st.caption("Zmiana statusu wymaga podania kodu PIN. Dotyczy typów widocznych w sekcji 'Najnowsze typy'.")

if len(df_analizy) > 0:
    opcje_meczow = df_analizy.apply(
        lambda row: f"{row['data']} | {row['mecz']} | {row['rynek']} (aktualny status: {row['wynik']})",
        axis=1
    ).tolist()

    wybrany_mecz = st.selectbox("Wybierz kupon do zmiany", opcje_meczow)
    nowy_status = st.selectbox("Nowy status", ["OPEN", "WYGRANA", "PRZEGRANA"])
    pin_input = st.text_input("Kod PIN", type="password", max_chars=4, key="pin_status")

    if st.button("Zapisz zmianę"):
        if pin_input != st.secrets["APP_PIN"]:
            st.error("Nieprawidłowy kod PIN. Zmiana nie została zapisana.")
        else:
            wybrany_idx = opcje_meczow.index(wybrany_mecz)
            wybrany_row = df_analizy.iloc[wybrany_idx]

            content_now, sha_now = github_get("analizy.csv")
            df_now = pd.read_csv(StringIO(content_now)) if content_now else df_analizy.copy()
            df_now = normalizuj_kolumne_rynku(df_now, "rynek")

            mask = (
                (df_now["data"] == wybrany_row["data"]) &
                (df_now["mecz"] == wybrany_row["mecz"]) &
                (df_now["rynek"] == wybrany_row["rynek"]) &
                (df_now["stawka"].astype(str) == str(wybrany_row["stawka"])) &
                (df_now["kurs"].astype(str) == str(wybrany_row["kurs"]))
            )

            if mask.sum() == 0:
                st.error("Nie znaleziono tego kuponu w pliku na GitHubie. Odśwież stronę i spróbuj ponownie.")
            else:
                df_now.loc[mask, "wynik"] = nowy_status
                buf = StringIO(); df_now.to_csv(buf, index=False)
                r2 = github_put("analizy.csv", buf.getvalue(), sha_now, f"Zmieniono status: {wybrany_mecz} -> {nowy_status}")

                if r2.status_code in [200, 201]:
                    st.success(f"Status zaktualizowany na: {nowy_status}. Trwa aktualizacja danych...")
                    if nowy_status == "WYGRANA":
                        st.balloons()
                    st.rerun()
                else:
                    st.error(f"Błąd zapisu do GitHub: {r2.status_code} — {r2.text}")
else:
    st.info("Brak kuponów do edycji.")

st.divider()
st.markdown("<span id='dodaj-typ' class='section-anchor'></span>", unsafe_allow_html=True)
st.subheader("Dodaj typ")
st.caption("Wybierz kategorię rynku pasującą do sportu. Archiwum zapisuje kategorię i selekcję osobno.")
rynki = {"Pilka":["Zwycięzca meczu","Gole — suma meczu","BTTS","Handicap","Podwójna szansa","Inne"], "Tenis":["Zwycięzca meczu","Sety — suma meczu","Gemy — suma meczu","Handicap","Inne"], "Koszykowka":["Zwycięzca meczu","Punkty — suma meczu","Handicap","Inne"], "Hokej":["Zwycięzca meczu","Gole — suma meczu (hokej)","Handicap","Inne"]}
sporty=["Pilka","Tenis","Hokej","Koszykowka","Siatkowka","Baseball","Rugby","Snooker","Darts","MMA/Boks","Inne"]
a,b=st.columns(2); data_input=a.date_input("Data meczu",value=datetime.today()); sport_input=b.selectbox("Sport",sporty)
a,b=st.columns(2); mecz_input=a.text_input("Mecz",placeholder="np. Barcelona vs Inter"); kategoria=b.selectbox("Kategoria rynku",rynki.get(sport_input,["Zwycięzca meczu","Handicap","Inne"]))
uczestnicy=[x.strip() for x in __import__("re").split(r"\s+(?:vs|v|-)\s+",mecz_input,maxsplit=1,flags=__import__("re").I)]
if "suma" in kategoria:
    a,b=st.columns(2); kierunek=a.selectbox("Kierunek",["Over","Under"]); linia=b.text_input("Linia",placeholder="np. 2.5 / 215.5 / 36.5")
    jednostka="pkt" if "Punkty" in kategoria else ("sety" if "Sety" in kategoria else ("gemów" if "Gemy" in kategoria else "goli")); selekcja=f"{kierunek} {linia} {jednostka}" if linia else ""
elif kategoria=="BTTS": selekcja=st.selectbox("Typ / selekcja",["Tak","Nie"])
elif kategoria=="Handicap":
    a,b=st.columns(2); strona=a.selectbox("Drużyna / zawodnik",uczestnicy if len(uczestnicy)==2 else ["Gospodarze","Goście"]); linia=b.text_input("Linia handicapu",placeholder="np. -1.5 albo +1.5"); selekcja=f"{strona} {linia}" if linia else ""
elif kategoria=="Zwycięzca meczu": selekcja=st.selectbox("Typ / selekcja",uczestnicy if len(uczestnicy)==2 else ["Gospodarze","Goście"])
elif kategoria=="Podwójna szansa": selekcja=st.selectbox("Typ / selekcja",["1X","X2","12"])
else: selekcja=st.text_input("Typ / selekcja")
a,b=st.columns(2); pewnosc=a.selectbox("Poziom pewności",["Pewny","Średni","Ryzykowny"]); stawka=b.number_input("Stawka GBP",min_value=0.0,step=50.0)
kurs=st.number_input("Kurs WH",min_value=1.0,step=.01); analiza=st.text_area("Twoja analiza (opis po ludzku)"); pin=st.text_input("Kod PIN",type="password",max_chars=4,key="pin_dodaj")
if st.button("Zapisz typ i analizę"):
    if pin != st.secrets["APP_PIN"]: st.error("Nieprawidłowy kod PIN.")
    elif not mecz_input or not selekcja or not analiza: st.error("Uzupełnij mecz, selekcję, wymaganą linię i analizę.")
    else:
        nowy=pd.DataFrame([{"data":data_input.strftime("%Y-%m-%d"),"sport":sport_input,"mecz":mecz_input,"rynek":f"{kategoria}: {selekcja}","pewnosc":pewnosc,"stawka":f"{stawka:.2f}","kurs":f"{kurs:.2f}","wynik":"OPEN","analiza":analiza.replace("\n"," ").strip()}])
        content_now,sha_now=github_get("analizy.csv"); df_now=pd.read_csv(StringIO(content_now)) if content_now else pd.DataFrame(columns=nowy.columns); df_now=pd.concat([df_now,nowy],ignore_index=True); buf=StringIO(); df_now.to_csv(buf,index=False); r=github_put("analizy.csv",buf.getvalue(),sha_now,f"Dodano typ: {mecz_input}")
        if r.status_code in [200,201]: st.success("Typ zapisany."); st.rerun()
        else: st.error(f"Błąd zapisu: {r.status_code}")



