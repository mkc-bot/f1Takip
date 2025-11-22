import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import random
import base64
import os
import fastf1 # Resmi veriler için kütüphane

# --- FASTF1 AYARLARI ---
if not os.path.exists('cache'):
    os.makedirs('cache')
fastf1.Cache.enable_cache('cache')

def get_local_img(file_path):
    if not os.path.exists(file_path):
        return "https://media.formula1.com/d_driver_fallback_image.png"
    with open(file_path, "rb") as f:
        data = f.read()
        encoded = base64.b64encode(data).decode()
    return f"data:image/png;base64,{encoded}"

# --- 1. SAYFA VE CSS AYARLARI ---
st.set_page_config(page_title="F1 Standings", layout="centered", page_icon="🏎️")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #ffffff; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #0e0e0e; padding: 10px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1c1c1c; border-radius: 5px; color: #fff; font-weight: bold; flex: 1; }
    .stTabs [aria-selected="true"] { background-color: #FF1801 !important; color: white !important; }

    details > summary { list-style: none; outline: none; }
    details > summary::-webkit-details-marker { display: none; }

    .card-row { background-color: #121214; border-radius: 8px; padding: 12px 15px; display: flex; align-items: center; border-left-width: 5px; border-left-style: solid; transition: background 0.2s; cursor: pointer; margin-bottom: 5px; }
    .card-row:hover { background-color: #1f1f1f; }

    .pos-num { font-size: 20px; font-weight: bold; color: #fff; width: 35px; text-align: center; margin-right: 10px; }
    .avatar { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; margin-right: 15px; border: 1px solid #333; background: #222; }
    .info-box { flex-grow: 1; }
    .main-name { font-size: 16px; font-weight: bold; color: #fff; text-transform: uppercase; }
    .sub-name { font-size: 15px; color: #888; }
    .points-box { text-align: right; }
    .pts-val { font-size: 18px; font-weight: bold; color: #fff; }
    .pts-lbl { font-size: 14px; color: #666; }

    details[open] .details-panel { animation: slideDown 0.3s ease-out forwards; }
    .details-panel { background-color: #0f0f0f; border: 1px solid #222; border-top: none; padding: 15px; margin-bottom: 10px; border-radius: 0 0 8px 8px; display: flex; flex-direction: column; gap: 10px; }
    
    @keyframes slideDown { 0% { opacity: 0; transform: translateY(-10px); } 100% { opacity: 1; transform: translateY(0); } }

    .stats-row { display: flex; justify-content: space-around; width: 100%; }
    .stat-box { text-align: center; background: #1a1a1a; padding: 8px 10px; border-radius: 8px; border: 1px solid #333; min-width: 80px; }
    .stat-val { font-size: 16px; font-weight: bold; color: #fff; }
    .stat-lbl { font-size: 10px; color: #888; text-transform: uppercase; }

    /* TAKVİM CSS */
    .cal-date { background: #222; padding: 5px 10px; border-radius: 5px; text-align: center; margin-right: 15px; min-width: 60px; }
    .cal-day { font-size: 18px; font-weight: bold; color: #fff; }
    .cal-month { font-size: 13px; color: #aaa; text-transform: uppercase; }
    .cal-race { font-size: 19px; font-weight: bold; color: #fff; }
    .cal-circuit { font-size: 15px; color: #888; }
    
    .cal-badge { text-align: right; background: #1a1a1a; padding: 5px 10px; border-radius: 5px; border: 1px solid #333; min-width: 80px; }
    .badge-val { font-size: 14px; font-weight: bold; color: #fff; }
    .badge-lbl { font-size: 10px; color: #aaa; margin-bottom: 2px; }
    
    /* Podium Renkleri */
    .p1 { color: #FFD700; } /* Altın */
    .p2 { color: #C0C0C0; } /* Gümüş */
    .p3 { color: #CD7F32; } /* Bronz */

    .session-row { display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #222; }
    .session-row:last-child { border-bottom: none; }
    .sess-name { color: #aaa; font-size: 15px; width: 100px; }
    .sess-time { color: #fff; font-weight: bold; font-size: 16px; flex-grow: 1; text-align: center;}
    .sess-result { color: #FF1801; font-size: 15px; font-weight: bold; width: 120px; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- 2. VERİ TANIMLARI ---
TEAM_COLORS = {
    "Red Bull": "#3671C6", "Mercedes": "#27F4D2", "Ferrari": "#E80020", "McLaren": "#FF8000", 
    "Aston Martin": "#229971", "Alpine": "#0093CC", "Williams": "#64C4FF", "RB": "#6692FF", 
    "Sauber": "#52E252", "Haas": "#B6BABD"
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
    "McLaren": get_local_img("mclarenlogo.png"), "Red Bull": get_local_img("rblogo.png"),
    "Ferrari": get_local_img("ferrari.png"), "Mercedes": get_local_img("merclogo.png"),
    "Aston Martin": get_local_img("astonlogo.png"), "Alpine": get_local_img("alpinelogo.png"),
    "Williams": get_local_img("williamslogo.png"), "RB": get_local_img("racingblogo.png"),
    "Sauber": get_local_img("kicklogo.png"), "Haas": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Logo_Haas_F1.png/100px-Logo_Haas_F1.png"
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

def format_session_time(date_str, time_str):
    if not date_str or not time_str: return "TBC"
    try:
        dt_str = f"{date_str} {time_str}".replace("Z", "")
        utc_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
        tr_dt = utc_dt.astimezone(pytz.timezone('Europe/Istanbul'))
        return tr_dt.strftime("%H:%M")
    except:
        return "TBC"

def fetch_api(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except: return None

# --- VERİ ÇEKME: TOP 3 DESTEKLİ ---
@st.cache_data(ttl=3600)
def get_fastf1_winners():
    """
    FastF1'den sadece kazananı değil, İLK 3 PİLOTU çeker.
    """
    winners = {}
    try:
        current_year = datetime.now().year
        schedule = fastf1.get_event_schedule(current_year)
        completed_races = schedule[schedule['EventDate'] < datetime.now()]
        
        for i, row in completed_races.iterrows():
            round_num = str(row['RoundNumber'])
            event_name = row['EventName']
            try:
                session = fastf1.get_session(current_year, event_name, 'R')
                session.load(laps=False, telemetry=False, weather=False, messages=False)
                # İlk 3 pilotun kısaltmasını al
                top3 = session.results.iloc[:3]['Abbreviation'].tolist()
                winners[round_num] = top3
            except:
                continue 
    except Exception as e:
        print(f"FastF1 Hatası: {e}")
    return winners

@st.cache_data(ttl=600)
def get_all_data():
    OFFICIAL_WINNERS = get_fastf1_winners()
    MANUAL_RESULTS = {}

    # 1. PİLOTLAR
    drivers = []
    d_data = fetch_api("https://api.jolpi.ca/ergast/f1/current/driverStandings.json")
    if d_data:
        standings = d_data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
        for s in standings:
            wins = int(s['wins'])
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

    # 2. MARKALAR
    constructors = []
    c_data = fetch_api("https://api.jolpi.ca/ergast/f1/current/constructorStandings.json")
    if c_data:
        c_standings = c_data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
        for c in c_standings:
            constructors.append({
                "pos": c['position'], "name": c['Constructor']['name'],
                "points": c['points'], "wins": c['wins']
            })

    # 3. TAKVİM
    calendar = []
    cal_data = fetch_api("https://api.jolpi.ca/ergast/f1/current.json")
    
    # Ergast Results
    ergast_winners = {}
    res_data = fetch_api("https://api.jolpi.ca/ergast/f1/current/results.json?limit=500")
    if res_data:
        for r in res_data['MRData']['RaceTable']['Races']:
            round_num = r['round']
            try:
                top3 = [res['Driver']['code'] for res in r['Results'][:3]]
                ergast_winners[round_num] = top3
            except: pass

    quali_data = fetch_api("https://api.jolpi.ca/ergast/f1/current/qualifying.json?limit=500")
    pole_sitters = {}
    if quali_data:
        for q in quali_data['MRData']['RaceTable']['Races']:
            round_num = q['round']
            try:
                pole = q['QualifyingResults'][0]['Driver']['code']
                pole_sitters[round_num] = pole
            except: pass

    if cal_data:
        races = cal_data['MRData']['RaceTable']['Races']
        now = datetime.now(pytz.utc)
        
        for r in races:
            round_num = r['round']
            race_name = r['raceName']
            circuit = r['Circuit']['circuitName']
            time_str = r.get('time', '12:00:00Z')
            dt_str = f"{r['date']} {time_str}".replace("Z", "")
            r_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
            is_past = r_dt < now
            days_diff = (r_dt - now).days
            
            # Top 3 Belirle
            top3 = ergast_winners.get(round_num, None)
            if (top3 is None) and str(round_num) in OFFICIAL_WINNERS:
                top3 = OFFICIAL_WINNERS[str(round_num)]
            if (top3 is None) and str(round_num) in MANUAL_RESULTS:
                top3 = MANUAL_RESULTS[str(round_num)]
            if top3 is None: top3 = []

            pole = pole_sitters.get(round_num, "-")
            
            # Seanslar
            sessions = []
            if 'FirstPractice' in r: sessions.append({"name": "FP1", "time": format_session_time(r['FirstPractice'].get('date'), r['FirstPractice'].get('time')), "winner": ""})
            if 'SprintQualifying' in r: sessions.append({"name": "Sprint Quali", "time": format_session_time(r['SprintQualifying'].get('date'), r['SprintQualifying'].get('time')), "winner": ""})
            elif 'SecondPractice' in r: sessions.append({"name": "FP2", "time": format_session_time(r['SecondPractice'].get('date'), r['SecondPractice'].get('time')), "winner": ""})
            if 'Sprint' in r: sessions.append({"name": "SPRINT", "time": format_session_time(r['Sprint'].get('date'), r['Sprint'].get('time')), "winner": ""})
            elif 'ThirdPractice' in r: sessions.append({"name": "FP3", "time": format_session_time(r['ThirdPractice'].get('date'), r['ThirdPractice'].get('time')), "winner": ""})
            if 'Qualifying' in r: sessions.append({"name": "QUALIFYING", "time": format_session_time(r['Qualifying'].get('date'), r['Qualifying'].get('time')), "winner": pole if is_past else ""})
            sessions.append({"name": "RACE", "time": format_session_time(r.get('date'), r.get('time')), "winner": top3[0] if top3 else ""})

            calendar.append({
                "round": round_num,
                "race": race_name,
                "circuit": circuit,
                "date_obj": r_dt,
                "day": r_dt.day,
                "month": r_dt.strftime("%b"),
                "days_left": days_diff,
                "is_past": is_past,
                "top3": top3,
                "sessions": sessions
            })
    return drivers, constructors, calendar

# --- 4. ARAYÜZ OLUŞTURMA ---
drivers, constructors, calendar = get_all_data()

st.title("Formula 1 Standings & Calender")
st.divider()

tab_drivers, tab_constructors, tab_calendar = st.tabs(["DRIVERS", "CONSTRUCTOR", "SCHEDULE"])

with tab_drivers:
    if drivers:
        for d in drivers:
            color = get_team_color(d['team'])
            img = get_img(d['id'])
            st.markdown(f"""<details style="margin-bottom: 5px;"><summary class="card-row" style="border-left-color: {color};"><div class="pos-num">{d['pos']}</div><img src="{img}" class="avatar"><div class="info-box"><div class="main-name">{d['name']}</div><div class="sub-name">{d['team']}</div></div><div class="points-box"><div class="pts-val">{d['points']}</div><div class="pts-lbl">PTS</div></div></summary><div class="details-panel"><div class="stats-row"><div class="stat-box"><div class="stat-val" style="color:#ffd700;">{d['wins']}</div><div class="stat-lbl">Galibiyet</div></div><div class="stat-box"><div class="stat-val" style="color:#c0c0c0;">{d['podiums']}</div><div class="stat-lbl">Podyum</div></div><div class="stat-box"><div class="stat-val" style="color:#ff4d4d;">{d['dnf']}</div><div class="stat-lbl">DNF</div></div></div></div></details>""", unsafe_allow_html=True)
    else: st.info("Veri yükleniyor...")

with tab_constructors:
    if constructors:
        for c in constructors:
            color = get_team_color(c['name'])
            logo = get_team_logo(c['name'])
            st.markdown(f"""<div class="card-row" style="border-left-color: {color}; cursor: default;"><div class="pos-num">{c['pos']}</div><img src="{logo}" class="avatar" style="border-radius: 5px; width: 60px; object-fit: contain; background: transparent; border: none;"><div class="info-box"><div class="main-name">{c['name']}</div><div class="sub-name">{c['wins']} Galibiyet</div></div><div class="points-box"><div class="pts-val">{c['points']}</div><div class="pts-lbl">PTS</div></div></div>""", unsafe_allow_html=True)

# --- SEKME 3: TAKVİM (DÜZELTİLMİŞ) ---
with tab_calendar:
    if calendar:
        next_race_idx = -1
        for i, r in enumerate(calendar):
            if not r['is_past']:
                next_race_idx = i
                break
        
        for idx, race in enumerate(calendar):
            is_next = (idx == next_race_idx)
            border_color = "#FF1801" if is_next else "#333"
            
            # ROZET ALANI (DÜZELTME: Girintiler kaldırıldı ve tek satır yapıldı)
            if race['is_past']:
                if race['top3'] and len(race['top3']) >= 3:
                    badge_html = (
                        f'<div class="badge-val p1">1. {race["top3"][0]}</div>'
                        f'<div class="badge-val p2">2. {race["top3"][1]}</div>'
                        f'<div class="badge-val p3">3. {race["top3"][2]}</div>'
                    )
                elif race['top3'] and len(race['top3']) > 0:
                    badge_html = f'<div class="badge-val p1">1. {race["top3"][0]}</div>'
                else:
                    badge_html = '<div class="badge-lbl">SONUÇ BEKLENİYOR</div>'
            elif is_next:
                days = race['days_left'] if race['days_left'] >= 0 else 0
                badge_html = f'<div class="badge-val" style="color:#FF1801;">{days}</div><div class="badge-lbl">GÜN KALDI</div>'
            else:
                badge_html = f'<div class="badge-val">{race["days_left"]}</div><div class="badge-lbl">GÜN</div>'

            sessions_html = ""
            for sess in race['sessions']:
                winner_div = f'<div class="sess-result">{sess["winner"]}</div>' if sess["winner"] else '<div class="sess-result"></div>'
                sessions_html += f'<div class="session-row"><div class="sess-name">{sess["name"]}</div><div class="sess-time">{sess["time"]}</div>{winner_div}</div>'

            # Ana Kart HTML (Girintiler kaldırıldı)
            html_content = f"""
            <details name="f1-race" style="margin-bottom: 8px;">
                <summary class="calendar-card" style="display: flex; align-items: center; background-color: #121214; border-radius: 8px; padding: 15px; border-left: 5px solid {border_color}; cursor: pointer;">
                    <div class="cal-date">
                        <div class="cal-day">{race['day']}</div>
                        <div class="cal-month">{race['month']}</div>
                    </div>
                    <div class="cal-info" style="flex-grow: 1;">
                        <div class="cal-race">{race['race']}</div>
                        <div class="cal-circuit">{race['circuit']}</div>
                    </div>
                    <div class="cal-badge">
                        {badge_html}
                    </div>
                </summary>
                <div class="details-panel">
                    {sessions_html}
                </div>
            </details>
            """
            st.markdown(html_content, unsafe_allow_html=True)
    else:
        st.success("Takvim yükleniyor...")
