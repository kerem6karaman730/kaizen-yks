import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from datetime import datetime
import plotly.express as px

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Kaizen Mentörlük | YKTS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

SHEET_ID = "1cGpD0BfwiaEBxZ4S-tO-K6Zh3G6DT_kJ3yqcx_Us-8s"

# --- NEON RENK PALETİ ---
NEON_RED = "#FF0033"
NEON_BLUE = "#00F0FF"
NEON_GREEN = "#00FF66"
NEON_ORANGE = "#FF9900"
NEON_PURPLE = "#CC00FF"
NEON_YELLOW = "#FFD600"

# --- CSS TASARIM ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #050505; }}
    [data-testid="stSidebar"] {{ background-color: #000000; border-right: 1px solid #222; }}
    .stMetric {{
        background-color: #111; padding: 15px; border-radius: 12px;
        border: 1px solid #333; border-left: 6px solid {NEON_RED};
        box-shadow: 0 0 10px rgba(255, 0, 51, 0.2);
    }}
    [data-testid="InputInstructions"] {{ display: none !important; }}
    small {{ display: none !important; }}
    .stNumberInput div[data-baseweb="input"], .stTextInput div[data-baseweb="input"], .stSelectbox div[data-baseweb="select"] {{
        background-color: #111; color: white; border: 1px solid #333;
    }}
    h1, h2, h3 {{ color: {NEON_RED} !important; font-family: 'Segoe UI', sans-serif; font-weight: 800; }}
    .stButton>button {{
        background: linear-gradient(45deg, #C8102E, #FF0033); color: white; border: none; font-weight: bold;
    }}
    .stButton>button:hover {{ box-shadow: 0 0 15px {NEON_RED}; transform: scale(1.02); }}
    .js-plotly-plot .plotly .modebar {{ display: none !important; }}
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

def create_neon_chart(df, x_col, y_col, title, color_hex, exam_limit):
    df['label'] = df['date_str'] + "<br>" + df['deneme_adi'].fillna('')
    y_view_max = exam_limit * 1.1
    fig = px.bar(df, x='label', y=y_col, text=y_col, title=title, color_discrete_sequence=[color_hex])
    fig.update_traces(textposition='outside', texttemplate='%{text:.2f}', textfont_size=14, textfont_color='white', textfont_weight='bold', marker_line_width=0, opacity=1.0, cliponaxis=False)
    fig.update_layout(
        barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"),
        xaxis=dict(showgrid=False, title="", type='category'),
        yaxis=dict(showgrid=True, gridcolor='#222', title="", range=[0, y_view_max], dtick=5),
        margin=dict(t=50, b=20, l=20, r=20), height=350, showlegend=False
    )
    return fig

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_info' not in st.session_state: st.session_state['user_info'] = {}

# ==========================================
# GİRİŞ EKRANI
# ==========================================
if not st.session_state['logged_in']:
    st.write(""); st.write("")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f"<h1 style='text-align: center; margin-top:20px; font-size: 3.5em;'>KAIZEN</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #fff; opacity:0.7; letter-spacing: 2px;'>YÜKSEK PERFORMANS SİSTEMİ</p>", unsafe_allow_html=True)
        st.divider()
        with st.form("login"):
            u = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adınızı giriniz")
            p = st.text_input("Şifre", type="password", placeholder="Şifrenizi giriniz")
            if st.form_submit_button("SİSTEME GİRİŞ", use_container_width=True):
                try:
                    with st.spinner("🚀 Bağlanılıyor..."):
                        ws, df_u = get_data("users")
                        # Kullanıcıyı bul
                        user = df_u[(df_u['username'] == u) & (df_u['password'].astype(str) == p)]
                        if not user.empty:
                            st.session_state['logged_in'] = True
                            st.session_state['user_info'] = user.iloc[0].to_dict()
                            st.success("Giriş Başarılı!"); time.sleep(0.5); st.rerun()
                        else: st.error("Hatalı bilgiler.")
                except Exception as e: st.error(f"Hata: {e}")

# ==========================================
# ANA DASHBOARD
# ==========================================
else:
    user = st.session_state['user_info']
    aktif_kullanici = user['username']
    kullanici_rolu = user.get('role', 'student') # Rolü al
    alan = user.get('alan', 'SAY')
    
    with st.sidebar:
        st.markdown(f"<h2 style='text-align: center; margin-top: 20px;'>{user['name']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; background:#111; padding:5px; border-radius:5px; border:1px solid {NEON_RED}; color:{NEON_RED}; font-weight:bold;'>{alan} MODU</div>", unsafe_allow_html=True)
        st.divider()
        
        # --- 👑 ADMIN PANELİ (Sadece Admin Görür) ---
        if kullanici_rolu == 'admin':
            with st.expander("👑 YÖNETİCİ PANELİ", expanded=False):
                st.caption("Yeni Öğrenci Ekle")
                with st.form("add_user_form"):
                    new_user = st.text_input("Kullanıcı Adı")
                    new_pass = st.text_input("Şifre")
                    new_name = st.text_input("Ad Soyad")
                    new_alan = st.selectbox("Alan", ["SAY", "EA", "SOZ", "DIL"])
                    
                    if st.form_submit_button("Öğrenciyi Kaydet"):
                        try:
                            ws_users, df_users = get_data("users")
                            if new_user in df_users['username'].values:
                                st.error("Bu kullanıcı adı zaten var!")
                            elif not new_user or not new_pass:
                                st.warning("Bilgiler boş olamaz!")
                            else:
                                # Yeni satır ekle: user, pass, name, role=student, alan
                                ws_users.append_row([new_user, new_pass, new_name, "student", new_alan])
                                st.success(f"✅ {new_name} eklendi!")
                                time.sleep(1); st.rerun()
                        except Exception as e: st.error(f"Hata: {e}")
            st.divider()
        # ---------------------------------------------

        with st.expander("➕ DENEME EKLE", expanded=True):
            tur = st.radio("Sınav Türü", ["TYT", "AYT"], horizontal=True)
            if tur == "TYT": st.caption("📘 TYT GİRİŞİ")
            else: st.caption(f"📕 AYT GİRİŞİ ({alan})")

            with st.form("entry_form"):
                c_date, c_name = st.columns([1, 1.5])
                with c_date: tarih = st.date_input("Tarih", datetime.now())
                with c_name: deneme_adi = st.text_input("Yayın Adı", placeholder="Örn: 345 - 2")
                st.divider()
                
                t_turk, t_mat, t_sos, t_fen = 0,0,0,0
                a_mat, a_fiz, a_kim, a_biyo = 0,0,0,0
                a_edeb, a_tar1, a_cog1, a_tar2, a_cog2, a_fel, a_din = 0,0,0,0,0,0,0

                if tur == "TYT":
                    r1c1, r1c2 = st.columns(2)
                    with r1c1: t_turk = st.number_input("Türkçe", 0.0, 40.0, step=0.25)
                    with r1c2: t_mat = st.number_input("Matematik", 0.0, 40.0, step=0.25)
                    r2c1, r2c2 = st.columns(2)
                    with r2c1: t_sos = st.number_input("Sosyal", 0.0, 20.0, step=0.25)
                    with r2c2: t_fen = st.number_input("Fen", 0.0, 20.0, step=0.25)
                else: 
                    if alan in ["SAY", "EA"]: a_mat = st.number_input("AYT Matematik", 0.0, 40.0, step=0.25)
                    if alan == "SAY":
                        c_fiz, c_kim, c_biyo = st.columns(3)
                        with c_fiz: a_fiz = st.number_input("Fizik", 0.0, 14.0, step=0.25)
                        with c_kim: a_kim = st.number_input("Kimya", 0.0, 13.0, step=0.25)
                        with c_biyo: a_biyo = st.number_input("Biyoloji", 0.0, 13.0, step=0.25)
                    elif alan == "EA":
                        a_edeb = st.number_input("Edebiyat", 0.0, 24.0, step=0.25)
                        c_t1, c_c1 = st.columns(2)
                        with c_t1: a_tar1 = st.number_input("Tarih-1", 0.0, 10.0, step=0.25)
                        with c_c1: a_cog1 = st.number_input("Coğ-1", 0.0, 6.0, step=0.25)
                    elif alan == "SOZ": pass 

                if st.form_submit_button("KAYDET", use_container_width=True):
                    try:
                        if not deneme_adi: deneme_adi = "Deneme"
                        ws_scores, _ = get_data("scores")
                        if tur == "TYT":
                            toplam_tyt = t_turk + t_mat + t_sos + t_fen
                            ws_scores.append_row([str(tarih), aktif_kullanici, t_turk, t_mat, t_sos, t_fen, toplam_tyt, 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0, 0.0, deneme_adi])
                            st.toast(f"✅ TYT Kaydedildi: {toplam_tyt}")
                        else:
                            toplam_ayt = a_mat + a_fiz + a_kim + a_biyo + a_edeb + a_tar1 + a_cog1 + a_tar2 + a_cog2 + a_fel + a_din
                            ws_scores.append_row([str(tarih), aktif_kullanici, 0.0,0.0,0.0,0.0, 0.0, a_mat, a_fiz, a_kim, a_biyo, a_edeb, a_tar1, a_cog1, a_tar2, a_cog2, a_fel, a_din, toplam_ayt, deneme_adi])
                            st.toast(f"✅ AYT Kaydedildi: {toplam_ayt}")
                        time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Kayıt Hatası: {e}")
        
        if st.button("ÇIKIŞ YAP", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

    try:
        ws, df_scores = get_data("scores")
        df = df_scores[df_scores['username'] == aktif_kullanici].copy()
        
        if not df.empty:
            cols = ['toplam', 'ayt_toplam', 'tyt_turkce', 'tyt_mat', 'tyt_fen', 'tyt_sosyal',
                    'ayt_mat', 'ayt_fiz', 'ayt_kim', 'ayt_biyo', 'ayt_edeb', 'ayt_tar1', 'ayt_cog1']
            for c in cols: 
                if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            df['date'] = pd.to_datetime(df['date'])
            df['date_str'] = df['date'].dt.strftime('%d.%m')
            df = df.sort_values(by='date')
            if 'deneme_adi' not in df.columns: df['deneme_adi'] = ""

            df_tyt = df[df['toplam'] > 0].copy()
            df_ayt = df[df['ayt_toplam'] > 0].copy()

            tab_tyt, tab_ayt = st.tabs(["📘 TYT PERFORMANS", "📕 AYT PERFORMANS"])
            
            with tab_tyt:
                if not df_tyt.empty:
                    son = df_tyt.iloc[-1]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("TOPLAM", f"{son['toplam']:.2f}"); c2.metric("MATEMATİK", f"{son['tyt_mat']:.2f}")
                    c3.metric("TÜRKÇE", f"{son['tyt_turkce']:.2f}"); c4.metric("FEN", f"{son['tyt_fen']:.2f}")
                    st.markdown("### 📈 Genel Gelişim")
                    st.plotly_chart(create_neon_chart(df_tyt, 'date_str', 'toplam', "", NEON_RED, exam_limit=120), use_container_width=True)
                    st.markdown("### 🔬 Branş Analizi")
                    tc1, tc2 = st.columns(2)
                    with tc1: st.plotly_chart(create_neon_chart(df_tyt, 'date_str', 'tyt_mat', "Matematik", NEON_BLUE, exam_limit=40), use_container_width=True)
                    with tc2: st.plotly_chart(create_neon_chart(df_tyt, 'date_str', 'tyt_turkce', "Türkçe", NEON_RED, exam_limit=40), use_container_width=True)
                    tc3, tc4 = st.columns(2)
                    with tc3: st.plotly_chart(create_neon_chart(df_tyt, 'date_str', 'tyt_fen', "Fen", NEON_GREEN, exam_limit=20), use_container_width=True)
                    with tc4: st.plotly_chart(create_neon_chart(df_tyt, 'date_str', 'tyt_sosyal', "Sosyal", NEON_ORANGE, exam_limit=20), use_container_width=True)
                else: st.info("TYT verisi yok.")

            with tab_ayt:
                if not df_ayt.empty:
                    son = df_ayt.iloc[-1]
                    ac1, ac2, ac3, ac4 = st.columns(4)
                    ac1.metric("AYT TOPLAM", f"{son['ayt_toplam']:.2f}")
                    if alan == "SAY":
                        ac2.metric("MATEMATİK", f"{son['ayt_mat']:.2f}"); ac3.metric("FEN", f"{son['ayt_fiz']+son['ayt_kim']+son['ayt_biyo']:.2f}")
                    elif alan == "EA":
                        ac2.metric("MATEMATİK", f"{son['ayt_mat']:.2f}"); ac3.metric("EDB-SOS", f"{son['ayt_edeb']+son['ayt_tar1']+son['ayt_cog1']:.2f}")
                    st.markdown("### 📈 Genel Gelişim")
                    st.plotly_chart(create_neon_chart(df_ayt, 'date_str', 'ayt_toplam', "", NEON_RED, exam_limit=80), use_container_width=True)
                    st.markdown("### 🔬 Branş Analizi")
                    if alan == "SAY":
                        sc1, sc2 = st.columns(2)
                        with sc1: st.plotly_chart(create_neon_chart(df_ayt, 'date_str', 'ayt_mat', "Matematik", NEON_BLUE, exam_limit=40), use_container_width=True)
                        with sc2: st.plotly_chart(create_neon_chart(df_ayt, 'date_str', 'ayt_fiz', "Fizik", NEON_YELLOW, exam_limit=14), use_container_width=True)
                        sc3, sc4 = st.columns(2)
                        with sc3: st.plotly_chart(create_neon_chart(df_ayt, 'date_str', 'ayt_kim', "Kimya", NEON_PURPLE, exam_limit=13), use_container_width=True)
                        with sc4: st.plotly_chart(create_neon_chart(df_ayt, 'date_str', 'ayt_biyo', "Biyoloji", NEON_GREEN, exam_limit=13), use_container_width=True)
                    elif alan == "EA":
                        sc1, sc2 = st.columns(2)
                        with sc1: st.plotly_chart(create_neon_chart(df_ayt, 'date_str', 'ayt_mat', "Matematik", NEON_BLUE, exam_limit=40), use_container_width=True)
                        with sc2: st.plotly_chart(create_neon_chart(df_ayt, 'date_str', 'ayt_edeb', "Edebiyat", NEON_PURPLE, exam_limit=24), use_container_width=True)
                        sc3, sc4 = st.columns(2)
                        with sc3: st.plotly_chart(create_neon_chart(df_ayt, 'date_str', 'ayt_tar1', "Tarih-1", NEON_ORANGE, exam_limit=10), use_container_width=True)
                        with sc4: st.plotly_chart(create_neon_chart(df_ayt, 'date_str', 'ayt_cog1', "Coğrafya-1", NEON_GREEN, exam_limit=6), use_container_width=True)
        else: st.info("Veri yok.")
    except Exception as e: st.error(f"Hata: {e}")