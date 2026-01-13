import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Kaizen Mentörlük | YKTS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

SHEET_ID = "1cGpD0BfwiaEBxZ4S-tO-K6Zh3G6DT_kJ3yqcx_Us-8s"

# --- RENK PALETİ & TASARIM ---
NEON_RED = "#FF0033"
NEON_BLUE = "#00F0FF"
NEON_GREEN = "#00FF66"
NEON_ORANGE = "#FF9900"
NEON_PURPLE = "#CC00FF"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #050505; }}
    [data-testid="stSidebar"] {{ background-color: #000000; border-right: 1px solid #222; }}
    
    /* Kart Tasarımı */
    .metric-card {{
        background-color: #111; padding: 20px; border-radius: 10px;
        border: 1px solid #333; text-align: center;
        transition: transform 0.2s;
    }}
    .metric-card:hover {{ transform: scale(1.02); border-color: {NEON_RED}; }}
    
    h1, h2, h3 {{ color: white !important; font-family: 'Segoe UI', sans-serif; font-weight: 700; }}
    .highlight {{ color: {NEON_RED}; }}
    
    /* Butonlar */
    .stButton>button {{
        background: #1a1a1a; color: white; border: 1px solid #333; border-radius: 8px;
    }}
    .stButton>button:hover {{ border-color: {NEON_RED}; color: {NEON_RED}; }}
    
    /* Checkbox */
    .stCheckbox label {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
@st.cache_resource
def baglanti_kur():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        try:
            credentials = Credentials.from_service_account_file("secrets.json", scopes=SCOPES)
        except FileNotFoundError:
            st.error("HATA: Secrets bulunamadı!"); st.stop()
    return gspread.authorize(credentials)

def get_data(sheet_name):
    client = baglanti_kur()
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(sheet_name)
    return worksheet, pd.DataFrame(worksheet.get_all_records())

def safe_float(val):
    try: return float(val)
    except: return 0.0

# --- SAYFA MODÜLLERİ ---

def dashboard_page(user):
    st.markdown(f"# 👋 Hoşgeldin, <span class='highlight'>{user['name']}</span>", unsafe_allow_html=True)
    
    # 1. YKS GERİ SAYIM
    yks_date = datetime(2026, 6, 20) # Tahmini Tarih
    today = datetime.now()
    kalan = yks_date - today
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color:{NEON_RED}; font-size: 3em; margin:0;">{kalan.days}</h2>
            <p style="color:#aaa;">YKS'ye Kalan Gün</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Bugünün Özeti
    ws_tasks, df_tasks = get_data("tasks")
    today_str = today.strftime("%Y-%m-%d")
    user_tasks = df_tasks[(df_tasks['username'] == user['username']) & (df_tasks['date'] == today_str)]
    
    completed_count = len(user_tasks[user_tasks['is_completed'] == "TRUE"])
    total_count = len(user_tasks)
    
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color:{NEON_BLUE}; font-size: 3em; margin:0;">{completed_count}/{total_count}</h2>
            <p style="color:#aaa;">Bugünkü Görevler</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
         # Hızlı Ekleme Butonları
        st.info("🚀 Hızlı İşlemler")
        with st.expander("⏱️ Süre Ekle"):
            sure = st.number_input("Dakika", 0, 600, 60)
            if st.button("Kaydet (Süre)"):
                try:
                    ws_log, _ = get_data("study_log")
                    ws_log.append_row([today_str, user['username'], sure, "Genel"])
                    st.toast("✅ Süre Eklendi!")
                except: st.error("Hata")
                
        with st.expander("📌 Görev Ekle"):
            gorev = st.text_input("Görev")
            if st.button("Kaydet (Görev)"):
                try:
                    ws_t, _ = get_data("tasks")
                    ws_t.append_row([today_str, user['username'], gorev, "FALSE", today.strftime("%A")])
                    st.toast("✅ Görev Eklendi!")
                    time.sleep(1); st.rerun()
                except: st.error("Hata")

def weekly_plan_page(user):
    st.header("📅 Haftalık Planlayıcı")
    
    # Hafta Seçimi (Basit mantık: Bu haftanın Pazartesisini bul)
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    
    # Kullanıcı geçmiş haftaları görmek isterse diye bir tarih seçici
    selected_date = st.date_input("Hafta Başlangıcını Seç", start_of_week)
    monday = selected_date - timedelta(days=selected_date.weekday()) # Seçilen günün Pazartesi'sini bul
    
    st.caption(f"Görüntülenen Hafta: {monday.strftime('%d.%m')} - {(monday+timedelta(days=6)).strftime('%d.%m')}")
    st.divider()

    # Verileri Çek
    ws_tasks, df_tasks = get_data("tasks")
    df_user = df_tasks[df_tasks['username'] == user['username']]
    
    cols = st.columns(7)
    days_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    for i, day_name in enumerate(days_tr):
        current_day_date = (monday + timedelta(days=i)).strftime("%Y-%m-%d")
        
        with cols[i]:
            st.markdown(f"<div style='text-align:center; color:{NEON_ORANGE}; font-weight:bold; margin-bottom:10px;'>{day_name}<br><span style='font-size:0.8em; color:#666'>{current_day_date[5:]}</span></div>", unsafe_allow_html=True)
            
            # O güne ait görevleri filtrele
            day_tasks = df_user[df_user['date'] == current_day_date]
            
            # Görev Listesi
            if not day_tasks.empty:
                for idx, row in day_tasks.iterrows():
                    # Checkbox durumu (Emoji ile gösterim daha şık ve hızlı)
                    is_done = str(row['is_completed']).upper() == "TRUE"
                    status_icon = "✅" if is_done else "⬜"
                    st.markdown(f"<div style='font-size:0.9em; padding:5px; background:#111; margin-bottom:5px; border-radius:5px;'>{status_icon} {row['task']}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center; color:#333;'>-</div>", unsafe_allow_html=True)
            
            # O Güne Yeni Görev Ekleme Butonu
            with st.popover("➕"):
                new_task = st.text_input(f"{day_name} Görevi", key=f"t_{i}")
                if st.button("Ekle", key=f"b_{i}"):
                    ws_tasks.append_row([current_day_date, user['username'], new_task, "FALSE", day_name])
                    st.rerun()

def study_timer_page(user):
    st.header("⏳ Odaklanma Modu")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.markdown("### Kronometre")
        if 'start_time' not in st.session_state: st.session_state['start_time'] = None
        
        if st.button("▶️ BAŞLAT", use_container_width=True):
            st.session_state['start_time'] = time.time()
            
        if st.button("⏹️ BİTİR & KAYDET", use_container_width=True):
            if st.session_state['start_time']:
                end = time.time()
                duration = int((end - st.session_state['start_time']) / 60)
                st.session_state['start_time'] = None
                
                # Kaydet
                try:
                    ws_log, _ = get_data("study_log")
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    ws_log.append_row([today_str, user['username'], duration, "Kronometre"])
                    st.success(f"👏 {duration} dakika çalışıldı ve kaydedildi!")
                except Exception as e: st.error(str(e))
            else:
                st.warning("Önce başlatmalısın.")
                
    with c2:
        st.markdown("### 📊 Çalışma Analizi")
        try:
            _, df_log = get_data("study_log")
            df_log['duration_minutes'] = pd.to_numeric(df_log['duration_minutes'])
            df_log['date'] = pd.to_datetime(df_log['date'])
            
            my_log = df_log[df_log['username'] == user['username']]
            daily_sum = my_log.groupby('date')['duration_minutes'].sum().reset_index()
            
            fig = px.bar(daily_sum, x='date', y='duration_minutes', title="Günlük Çalışma (Dk)", color_discrete_sequence=[NEON_GREEN])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)
        except: st.info("Henüz veri yok.")

def scores_page(user, alan):
    # (Eski grafik kodların buraya temizce taşındı)
    st.header("📈 Net Takibi")
    try:
        _, df_scores = get_data("scores")
        df = df_scores[df_scores['username'] == user['username']].copy()
        if df.empty:
            st.warning("Henüz deneme girmedin.")
            return

        # Veri Temizleme
        cols = ['toplam', 'ayt_toplam', 'tyt_mat', 'ayt_mat', 'tyt_turkce'] 
        for c in cols: 
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        
        df['date'] = pd.to_datetime(df['date'])
        df['label'] = df['date'].dt.strftime('%d.%m') + "<br>" + df['deneme_adi'].astype(str)
        df = df.sort_values('date')

        tab1, tab2 = st.tabs(["TYT", "AYT"])
        with tab1:
            fig = px.bar(df[df['toplam']>0], x='label', y='toplam', text='toplam', title="TYT Netleri", color_discrete_sequence=[NEON_RED])
            fig.update_traces(textposition='outside', textfont_color='white', cliponaxis=False)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), barmode='group', yaxis=dict(range=[0, 130]))
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            fig2 = px.bar(df[df['ayt_toplam']>0], x='label', y='ayt_toplam', text='ayt_toplam', title="AYT Netleri", color_discrete_sequence=[NEON_BLUE])
            fig2.update_traces(textposition='outside', textfont_color='white', cliponaxis=False)
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), barmode='group', yaxis=dict(range=[0, 90]))
            st.plotly_chart(fig2, use_container_width=True)

    except Exception as e: st.error(f"Hata: {e}")

# --- ANA UYGULAMA AKIŞI ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    # Basit Login Ekranı
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown(f"<h1 style='text-align:center; color:{NEON_RED}'>KAIZEN</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş"):
                _, df_u = get_data("users")
                user = df_u[(df_u['username'] == u) & (df_u['password'].astype(str) == p)]
                if not user.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Hatalı!")
else:
    # --- MENÜ SİSTEMİ (SIDEBAR) ---
    user = st.session_state['user_info']
    
    with st.sidebar:
        st.title("KAIZEN OS")
        st.markdown(f"👤 **{user['name']}**")
        st.markdown("---")
        
        menu = st.radio(
            "Menü", 
            ["🏠 Ana Sayfa", "📅 Haftalık Plan", "⏳ Odaklanma & Süre", "📈 Net Takip", "➕ Deneme Gir"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False; st.rerun()

    # --- SAYFA YÖNLENDİRME ---
    if menu == "🏠 Ana Sayfa":
        dashboard_page(user)
    elif menu == "📅 Haftalık Plan":
        weekly_plan_page(user)
    elif menu == "⏳ Odaklanma & Süre":
        study_timer_page(user)
    elif menu == "📈 Net Takip":
        scores_page(user, user.get('alan', 'SAY'))
    elif menu == "➕ Deneme Gir":
        # Hızlı Deneme Giriş Ekranı (Eski kodunun basitleştirilmiş hali)
        st.header("Deneme Ekle")
        with st.form("quick_score"):
            tarih = st.date_input("Tarih")
            ad = st.text_input("Yayın")
            tur = st.selectbox("Tür", ["TYT", "AYT"])
            net = st.number_input("Toplam Net", step=0.25)
            if st.form_submit_button("Kaydet"):
                ws_s, _ = get_data("scores")
                # Basit kayıt (Detaylı giriş için eski kodları buraya taşıyabiliriz)
                if tur == "TYT":
                    ws_s.append_row([str(tarih), user['username'], 0,0,0,0, net, 0,0,0,0,0,0,0,0,0,0,0, 0, ad])
                else:
                    ws_s.append_row([str(tarih), user['username'], 0,0,0,0, 0, 0,0,0,0,0,0,0,0,0,0,0, net, ad])
                st.success("Kaydedildi!")