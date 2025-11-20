import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- Sayfa Ayarları ---
st.set_page_config(page_title="F1 Kişisel Takip", layout="wide", page_icon="🏎️")

st.title("🏎️ Formula 1 - 2024/2025 Sezon Takibi")
st.markdown("Kendi geliştirdiğim, reklamsız ve ücretsiz F1 takip ekranı.")

# --- GÜNCELLENMİŞ Veri Çekme Fonksiyonları (Jolpica API - Daha Hızlı) ---
# Ergast yerine api.jolpi.ca kullanıyoruz, çünkü çok daha stabil.

def fetch_data(url):
    """Veri çekme işlemlerini yöneten yardımcı fonksiyon"""
    try:
        response = requests.get(url, timeout=10) # 10 saniye bekle, cevap gelmezse hata ver
        response.raise_for_status() # Hata varsa bildir
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Sunucuya bağlanılamadı: {e}")
        return None

@st.cache_data(ttl=3600)
def get_driver_standings():
    # URL Değiştirildi: Ergast -> Jolpica
    url = "https://api.jolpi.ca/ergast/f1/current/driverStandings.json"
    data = fetch_data(url)
    
    if not data: return pd.DataFrame() # Veri yoksa boş tablo dön

    standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
    
    drivers = []
    for item in standings:
        drivers.append({
            'Pozisyon': item['position'],
            'Pilot': f"{item['Driver']['givenName']} {item['Driver']['familyName']}",
            'Takım': item['Constructors'][0]['name'],
            'Puan': item['points'],
            'Galibiyet': item['wins']
        })
    return pd.DataFrame(drivers)

@st.cache_data(ttl=3600)
def get_constructor_standings():
    # URL Değiştirildi: Ergast -> Jolpica
    url = "https://api.jolpi.ca/ergast/f1/current/constructorStandings.json"
    data = fetch_data(url)

    if not data: return pd.DataFrame()

    standings = data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
    
    constructors = []
    for item in standings:
        constructors.append({
            'Pozisyon': item['position'],
            'Takım': item['Constructor']['name'],
            'Puan': item['points'],
            'Galibiyet': item['wins'],
            'Ülke': item['Constructor']['nationality']
        })
    return pd.DataFrame(constructors)

@st.cache_data(ttl=3600)
def get_calendar():
    # URL Değiştirildi: Ergast -> Jolpica
    url = "https://api.jolpi.ca/ergast/f1/current.json"
    data = fetch_data(url)

    if not data: return pd.DataFrame()

    races = data['MRData']['RaceTable']['Races']
    
    race_list = []
    today = datetime.today().date()
    
    for item in races:
        race_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        
        # Durum belirleme
        if race_date < today:
            status = "🏁 Tamamlandı"
        elif race_date == today:
            status = "🏎️ BUGÜN!"
        else:
            days_left = (race_date - today).days
            status = f"🟢 {days_left} Gün Kaldı"
        
        race_list.append({
            'Round': item['round'],
            'Yarış Adı': item['raceName'],
            'Pist': item['Circuit']['circuitName'],
            'Tarih': item['date'],
            'Saat (UTC)': item['time'] if 'time' in item else 'N/A',
            'Durum': status
        })
    return pd.DataFrame(race_list)

# --- Arayüz Tasarımı ---
tab1, tab2, tab3 = st.tabs(["🏆 Pilotlar", "🔧 Markalar", "📅 Takvim"])

with tab1:
    st.header("Pilotlar Şampiyonası")
    df_drivers = get_driver_standings()
    if not df_drivers.empty:
        st.dataframe(df_drivers, use_container_width=True, hide_index=True)

with tab2:
    st.header("Markalar Şampiyonası")
    df_constructors = get_constructor_standings()
    if not df_constructors.empty:
        st.dataframe(df_constructors, use_container_width=True, hide_index=True)

with tab3:
    st.header("Yarış Takvimi")
    df_calendar = get_calendar()
    if not df_calendar.empty:
        # Gelecek yarışları öne çıkar
        filter_upcoming = st.checkbox("Sadece Kalan Yarışları Göster", value=True)
        if filter_upcoming:
            # "Tamamlandı" olmayanları filtrele
            df_calendar = df_calendar[~df_calendar['Durum'].str.contains("Tamamlandı")]
            
        st.dataframe(df_calendar, use_container_width=True, hide_index=True)

# --- Alt Bilgi ---
st.divider()
st.caption("Veriler Jolpica-F1 (Open Source) API üzerinden sağlanmaktadır.")