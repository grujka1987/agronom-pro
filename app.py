import streamlit as st
import pdfplumber
from fpdf import FPDF
import pandas as pd

st.set_page_config(page_title="Agronom Pro v3.3", layout="wide")

st.title("🌱 Agronom Pro - Kornišon v3.3")
st.markdown("### Sistem za preciznu dnevnu fertigaciju")

faze = {
    "1. Ukorenjavanje (prva nedelja)": {"n_cilj": 100, "ec_cilj": 1200, "osnovno": "NPK 8:55:10", "g_min": 0.5, "g_max": 1.0, "hum": "0.01"},
    "2. Porast vreže": {"n_cilj": 180, "ec_cilj": 1800, "osnovno": "NPK 25:5:10", "g_min": 1.0, "g_max": 1.5, "hum": "0.007"},
    "3. Cvetanje i zametanje": {"n_cilj": 120, "ec_cilj": 2200, "osnovno": "NPK 14:8:28", "g_min": 1.5, "g_max": 2.0, "hum": "0.007"},
    "4. Pun rod (Intenzivna berba)": {"n_cilj": 150, "ec_cilj": 2500, "osnovno": "Kalijum-nitrat", "g_min": 2.0, "g_max": 2.5, "hum": "0.005"}
}

st.sidebar.header("Podešavanja")
izabrana_faza = st.sidebar.selectbox("Izaberi fazu razvoja:", list(faze.keys()))
uploaded_file = st.sidebar.file_uploader("Učitaj PDF sa merača", type="pdf")

def clean(t):
    if t is None: return 0.0
    # Čisti tekst od jedinica i pretvara u broj
    t = str(t).replace(',', '.')
    broj = "".join(c for c in t if c.isdigit() or c == '.')
    try:
        return float(broj) if broj else 0.0
    except:
        return 0.0

if uploaded_file is not None:
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # Uzimamo prvu stranicu i sve tabele
            table = pdf.pages[0].extract_table()
            
            if table:
                # Pokušavamo da izvučemo podatke bez obzira na tačan broj kolone
                # Ovo je sigurniji pristup: tražimo vrednosti u drugom redu (indeks 1)
                data_row = table[1]
                
                # Dinamičko mapiranje (prilagođeno tvojoj grešci)
                # Ako tvoj PDF ima manje kolona, ovde proveravamo dužinu reda
                podaci = {
                    'ec': clean(data_row[5]) if len(data_row) > 5 else 0.0,
                    'vlaznost': clean(data_row[6]) if len(data_row) > 6 else 0.0,
                    'k': clean(data_row[8]) if len(data_row) > 8 else 0.0,
                    'ph': clean(data_row[9]) if len(data_row) > 9 else 0.0
                }
                
                # Azot i Fosfor su često u koloni 7 podeljeni novim redom
                if len(data_row) > 7:
                    np_raw = str(data_row[7]).split('\n')
                    podaci['n'] = clean(np_raw[0])
                    podaci['p'] = clean(np_raw[1]) if len(np_raw) > 1 else 0.0
                else:
                    podaci['n'] = 0.0
                    podaci['p'] = 0.0

                f = faze[izabrana_faza]
                
                # Kalkulacije
                doza = f['g_max'] if podaci['ec'] < (f['ec_cilj'] * 0.5) else f['g_min']
                deficit = 80.0 - podaci['vlaznost']
                voda = max(0.4, (deficit * 0.015) + 0.4) if deficit > 0 else 0.4

                # Vizuelni prikaz
                st.info(f"✅ Podaci uspešno učitani za fazu: {izabrana_faza}")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("EC (µS/cm)", podaci['ec'])
                c2.metric("pH", podaci['ph'])
                c3.metric("Vlažnost (%)", f"{podaci['vlaznost']}%")

                st.divider()

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📝 Receptura (Dnevno po biljci)")
                    st.success(f"**Glavno đubrivo ({f['osnovno']}): {doza:.2f} gr**")
                    st.write(f"💧 Huminske kiseline: {f['hum']} ml")
                    if podaci['ph'] > 7.0:
                        st.warning("⚠️ Visok pH: Dodati 0.20 ml kiseline za korekciju")

                with col2:
                    st.subheader("💧 Navodnjavanje")
                    st.write(f"Ciljna vlažnost: **80%**")
                    st.info(f"Potrebno vode: **{voda:.2f} litara / biljci**")
                    st.caption("Savet: Podeliti u dva ciklusa (rano ujutru i kasno popodne).")

            else:
                st.error("Nije pronađena tabela u PDF-u. Proveri da li je fajl ispravan.")
    except Exception as e:
        st.error(f"Došlo je do greške prilikom čitanja PDF-a: {e}")