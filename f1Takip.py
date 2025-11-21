import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import random
import base64
import os

def get_local_img(file_path):
    """
    Yerel PNG dosyasını okur ve HTML için Base64 formatına çevirir.
    """
    # 1. Dosya var mı kontrol et
    if not os.path.exists(file_path):
        # Dosya yoksa internetten varsayılan gri kask resmini döndür
        return "https://media.formula1.com/d_driver_fallback_image.png"
    
    # 2. Dosyayı oku ve şifrele
    with open(file_path, "rb") as f:
        data = f.read()
        encoded = base64.b64encode(data).decode()
    
    # 3. PNG formatı olarak döndür
    return f"data:image/png;base64,{encoded}"


# --- 1. SAYFA VE CSS AYARLARI ---
st.set_page_config(page_title="F1 Standings", layout="centered", page_icon="🏎️")

st.markdown("""
<style>
    /* Genel Arkaplan */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* --- TAB (SEKME) TASARIMI --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #0e0e0e;
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1c1c1c;
        border-radius: 5px;
        color: #fff;
        font-weight: bold;
        flex: 1; /* Eşit genişlik */
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF1801 !important;
        color: white !important;
    }

    /* --- KART TASARIMI (PİLOT VE MARKA) --- */
    details > summary { list-style: none; outline: none; }
    details > summary::-webkit-details-marker { display: none; }

    .card-row {
        background-color: #121214;
        border-radius: 8px;
        padding: 12px 15px;
        display: flex;
        align-items: center;
        border-left-width: 5px;
        border-left-style: solid;
        transition: background 0.2s;
        cursor: pointer;
        margin-bottom: 5px;
    }
    .card-row:hover { background-color: #1f1f1f; }

    .pos-num { font-size: 20px; font-weight: bold; color: #fff; width: 35px; text-align: center; margin-right: 10px; }
    
    .avatar { 
        width: 45px; height: 45px; 
        border-radius: 50%; 
        object-fit: cover; 
        margin-right: 15px; 
        border: 1px solid #333; 
        background: #222;
    }
    
    .info-box { flex-grow: 1; }
    .main-name { font-size: 16px; font-weight: bold; color: #fff; text-transform: uppercase; }
    .sub-name { font-size: 12px; color: #888; }
    
    .points-box { text-align: right; }
    .pts-val { font-size: 18px; font-weight: bold; color: #fff; }
    .pts-lbl { font-size: 10px; color: #666; }

    /* DETAY ALANI (PİLOTLAR İÇİN) */
    details[open] .details-panel { animation: slideDown 0.3s ease-out forwards; }
    
    .details-panel {
        background-color: #0f0f0f;
        border: 1px solid #222;
        border-top: none;
        padding: 15px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-around;
        border-radius: 0 0 8px 8px;
        opacity: 0; 
    }
    
    @keyframes slideDown {
        0% { opacity: 0; transform: translateY(-10px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    .stat-box {
        text-align: center;
        background: #1a1a1a;
        padding: 8px 10px;
        border-radius: 8px;
        border: 1px solid #333;
        min-width: 80px;
    }
    .stat-val { font-size: 16px; font-weight: bold; color: #fff; }
    .stat-lbl { font-size: 10px; color: #888; text-transform: uppercase; }

    /* --- TAKVİM TASARIMI --- */
    .calendar-card {
        background-color: #121214;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        border-left: 5px solid #333;
    }
    .cal-date {
        background: #222;
        padding: 5px 10px;
        border-radius: 5px;
        text-align: center;
        margin-right: 15px;
        min-width: 60px;
    }
    .cal-day { font-size: 18px; font-weight: bold; color: #fff; }
    .cal-month { font-size: 10px; color: #aaa; text-transform: uppercase; }
    
    .cal-info { flex-grow: 1; }
    .cal-race { font-size: 15px; font-weight: bold; color: #fff; }
    .cal-circuit { font-size: 11px; color: #888; }
    
    .cal-countdown {
        text-align: right;
        background: #1a1a1a;
        padding: 5px 10px;
        border-radius: 5px;
        border: 1px solid #333;
    }
    .count-val { font-size: 16px; font-weight: bold; color: #FF1801; }
    .count-lbl { font-size: 9px; color: #aaa; }
    
    /* Next Race Highlight */
    .next-race { border-left-color: #FF1801 !important; background-color: #1a1a1c; }

</style>
""", unsafe_allow_html=True)

# --- 2. VERİ TANIMLARI ---

TEAM_COLORS = {
    "Red Bull": "#3671C6", "Mercedes": "#27F4D2", "Ferrari": "#E80020",
    "McLaren": "#FF8000", "Aston Martin": "#229971", "Alpine": "#0093CC",
    "Williams": "#64C4FF", "RB": "#6692FF", "Sauber": "#52E252", "Haas": "#B6BABD"
}

DRIVER_IMGS = {
    "max_verstappen": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png",
    "perez": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/S/SERPER01_Sergio_Perez/serper01.png",
    "hamilton": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png",
    "russell": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png",
    "leclerc": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png",
    "sainz": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CARSAI01_Carlos_Sainz/carsai01.png",
    "norris": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png",
    "piastri": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png",
    "alonso": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/F/FERALO01_Fernando_Alonso/feralo01.png",
    "stroll": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANSTR01_Lance_Stroll/lanstr01.png",
    "gasly": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png",
    "ocon": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/E/ESTOCO01_Esteban_Ocon/estoco01.png",
    "albon": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/A/ALEALB01_Alexander_Albon/alealb01.png",
    "tsunoda": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/Y/YUKTSU01_Yuki_Tsunoda/yuktsu01.png",
    "hulkenberg": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/N/NICHUL01_Nico_Hulkenberg/nichul01.png",
    "bottas": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/V/VALBOT01_Valtteri_Bottas/valbot01.png",
    "zhou": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GUAZHO01_Guanyu_Zhou/guazho01.png",
    "magnussen": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/K/KEVMAG01_Kevin_Magnussen/kevmag01.png",
    "colapinto": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/F/FRACOL01_Franco_Colapinto/fracol01.png",
    "bearman": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OLIBEA01_Oliver_Bearman/olibea01.png",
    "lawson": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LIALAW01_Liam_Lawson/lialaw01.png"
}

TEAM_LOGOS = {
    "McLaren": get_local_img("mclarenlogo.png"),
    "Red Bull": get_local_img("rblogo.png"),
    "Ferrari": get_local_img("ferrari.png"),
    "Mercedes": get_local_img("merclogo.png"),
    "Aston Martin": get_local_img("astonlogo.png"),
    "Alpine": get_local_img("alpinelogo.png"),
    "Williams": get_local_img("williamslogo.png"),
    "RB": get_local_img("racingblogo.png"),
    "Sauber": get_local_img("kicklogo.png"),
    "Haas": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Logo_Haas_F1.png/100px-Logo_Haas_F1.png"
}

def get_img(driver_id):
    for k, v in DRIVER_IMGS.items():
        if k in driver_id.lower() or driver_id.lower() in k: return v
    return "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/driver_fallback_image.png"

def get_team_color(team_name):
    for k, v in TEAM_COLORS.items():
        if k in team_name: return v
    return "#333"

def get_team_logo(team_name):
    for k, v in TEAM_LOGOS.items():
        if k in team_name: return v
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/F1_chequered_flag.svg/100px-F1_chequered_flag.svg.png"

# --- 3. VERİ ÇEKME ---
def fetch_api(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except: return None

@st.cache_data(ttl=600)
def get_all_data():
    # 1. PİLOTLAR
    drivers = []
    d_data = fetch_api("https://api.jolpi.ca/ergast/f1/current/driverStandings.json")
    if d_data:
        standings = d_data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
        for s in standings:
            wins = int(s['wins'])
            # Demo veri (Gerçek API'de bu detaylar yok)
            podiums = wins + random.randint(0, 5) if wins > 0 else random.randint(0, 3)
            dnf = random.randint(0, 3)
            
            drivers.append({
                "pos": s['position'],
                "name": f"{s['Driver']['givenName']} {s['Driver']['familyName'].upper()}",
                "team": s['Constructors'][0]['name'],
                "points": s['points'],
                "wins": wins, "podiums": podiums, "dnf": dnf,
                "id": s['Driver']['driverId']
            })

    # 2. MARKALAR (Constructors)
    constructors = []
    c_data = fetch_api("https://api.jolpi.ca/ergast/f1/current/constructorStandings.json")
    if c_data:
        c_standings = c_data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
        for c in c_standings:
            constructors.append({
                "pos": c['position'],
                "name": c['Constructor']['name'],
                "points": c['points'],
                "wins": c['wins']
            })

    # 3. TAKVİM
    calendar = []
    cal_data = fetch_api("https://api.jolpi.ca/ergast/f1/current.json")
    if cal_data:
        races = cal_data['MRData']['RaceTable']['Races']
        now = datetime.now(pytz.timezone('Europe/Istanbul'))
        for r in races:
            time_str = r.get('time', '12:00:00Z')
            dt_str = f"{r['date']} {time_str}".replace("Z", "")
            try:
                r_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
                # Sadece gelecek yarışları al
                if r_dt > datetime.now(pytz.utc):
                    days_left = (r_dt - datetime.now(pytz.utc)).days
                    calendar.append({
                        "race": r['raceName'],
                        "circuit": r['Circuit']['circuitName'],
                        "date_obj": r_dt,
                        "day": r_dt.day,
                        "month": r_dt.strftime("%b"),
                        "days_left": days_left
                    })
            except: continue
            
    return drivers, constructors, calendar

# --- 4. ARAYÜZ OLUŞTURMA ---

drivers, constructors, calendar = get_all_data()

st.title("Formula 1 Standings & Calender")
st.divider()

# SEKMELERİ OLUŞTUR
tab_drivers, tab_constructors, tab_calendar = st.tabs(["DRIVERS", "CONSTRUCTOR", "SCHEDULE"])

# --- SEKME 1: PİLOTLAR (AKORDİYON) ---
with tab_drivers:
    if drivers:
        for d in drivers:
            color = get_team_color(d['team'])
            img = get_img(d['id'])
            
            st.markdown(f"""
            <details style="margin-bottom: 5px;">
                <summary class="card-row" style="border-left-color: {color};">
                    <div class="pos-num">{d['pos']}</div>
                    <img src="{img}" class="avatar">
                    <div class="info-box">
                        <div class="main-name">{d['name']}</div>
                        <div class="sub-name">{d['team']}</div>
                    </div>
                    <div class="points-box">
                        <div class="pts-val">{d['points']}</div>
                        <div class="pts-lbl">PTS</div>
                    </div>
                </summary>
                <div class="details-panel">
                    <div class="stat-box">
                        <div class="stat-val" style="color:#ffd700;">{d['wins']}</div>
                        <div class="stat-lbl">Galibiyet</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-val" style="color:#c0c0c0;">{d['podiums']}</div>
                        <div class="stat-lbl">Podyum</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-val" style="color:#ff4d4d;">{d['dnf']}</div>
                        <div class="stat-lbl">DNF</div>
                    </div>
                </div>
            </details>
            """, unsafe_allow_html=True)
    else:
        st.info("Veri yükleniyor...")

# --- SEKME 2: MARKALAR (SADE KART) ---
with tab_constructors:
    if constructors:
        for c in constructors:
            color = get_team_color(c['name'])
            logo = get_team_logo(c['name'])
            
            st.markdown(f"""
            <div class="card-row" style="border-left-color: {color}; cursor: default;">
                <div class="pos-num">{c['pos']}</div>
                <img src="{logo}" class="avatar" style="border-radius: 5px; width: 60px; object-fit: contain; background: transparent; border: none;">
                <div class="info-box">
                    <div class="main-name">{c['name']}</div>
                    <div class="sub-name">{c['wins']} Galibiyet</div>
                </div>
                <div class="points-box">
                    <div class="pts-val">{c['points']}</div>
                    <div class="pts-lbl">PTS</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Markalar verisi bulunamadı.")

# --- SEKME 3: TAKVİM ---
with tab_calendar:
    if calendar:
        # İlk sıradaki (en yakın) yarış mı kontrolü için index kullanacağız
        for idx, race in enumerate(calendar):
            is_next = idx == 0
            extra_class = "next-race" if is_next else ""
            countdown_html = f'<div class="count-val">{race["days_left"]}</div><div class="count-lbl">GÜN KALDI</div>' if is_next else f'<div class="count-val" style="color:#fff;">{race["days_left"]}</div><div class="count-lbl">GÜN</div>'
            
            st.markdown(f"""
            <div class="calendar-card {extra_class}">
                <div class="cal-date">
                    <div class="cal-day">{race['day']}</div>
                    <div class="cal-month">{race['month']}</div>
                </div>
                <div class="cal-info">
                    <div class="cal-race">{race['race']}</div>
                    <div class="cal-circuit">{race['circuit']}</div>
                </div>
                <div class="cal-countdown">
                    {countdown_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("Bu sezon için planlanmış başka yarış görünmüyor!")
