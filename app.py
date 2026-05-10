import streamlit as st
import pdfplumber
from fpdf import FPDF
import pandas as pd

# Podešavanje stranice za mobilni i desktop
st.set_page_config(page_title="Agronom Pro v3.2", layout="wide")

st.title("🌱 Agronom Pro - Kornišon v3.2")
st.markdown("### Sistem za preciznu dnevnu fertigaciju")

# Rečnik sa fazama rasta
faze = {
    "1. Ukorenjavanje (prva nedelja)": {"n_cilj": 100, "ec_cilj": 1200, "osnovno": "NPK 8:55:10", "g_min": 0.5, "g_max": 1.0, "hum": "0.01"},
    "2. Porast vreže": {"n_cilj": 180, "ec_cilj": 1800, "osnovno": "NPK 25:5:10", "g_min": 1.0, "g_max": 1.5, "hum": "0.007"},
    "3. Cvetanje i zametanje": {"n_cilj": 120, "ec_cilj": 2200, "osnovno": "NPK 14:8:28", "g_min": 1.5, "g_max": 2.0, "hum": "0.007"},
    "4. Pun rod (Intenzivna berba)": {"n_cilj": 150, "ec_cilj": 2500, "osnovno": "Kalijum-nitrat", "g_min": 2.0, "g_max": 2.5, "hum": "0.005"}
}

# Sidebar kontrole
st.sidebar.header("Podešavanja")
izabrana_faza = st.sidebar.selectbox("Izaberi fazu razvoja:", list(faze.keys()))
uploaded_file = st.sidebar.file_uploader("Učitaj PDF sa merača", type="pdf")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        row = pdf.pages[0].extract_table()[1]
        def clean(t): return float("".join(c for c in t if t and (c.isdigit() or c in ".,")).replace(",", ".")) if t else 0.0
        np_raw = [x for x in row[7].split('\n') if x.strip()]
        podaci = {'ec': clean(row[5]), 'vlaznost': clean(row[6]), 'n': clean(np_raw[0]), 'p': clean(np_raw[1]), 'k': clean(row[8]), 'ph': clean(row[9])}

    f = faze[izabrana_faza]
    
    # Kalkulacije
    doza = f['g_max'] if podaci['ec'] < (f['ec_cilj'] * 0.5) else f['g_min']
    deficit = 80.0 - podaci['vlaznost']
    voda = max(0.4, (deficit * 0.015) + 0.4) if deficit > 0 else 0.4

    # Prikaz na ekranu
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Analiza zemljišta")
        df_prikaz = pd.DataFrame([podaci])
        st.table(df_prikaz)
        st.info(f"Trenutna vlažnost: {podaci['vlaznost']}%")

    with col2:
        st.subheader("📝 Dnevni recept (po biljci)")
        st.success(f"**{f['osnovno']}: {doza:.2f} gr**")
        st.write(f"Huminske kiseline: {f['hum']} ml")
        st.write(f"Preporuka vode: **{voda:.2f} L / biljci**")

    # Dugme za PDF download
    if st.button("Generiši PDF Izveštaj"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="AGRONOM PRO IZVESTAJ", ln=True, align='C')
        pdf.output("plan_prihrane.pdf")
        with open("plan_prihrane.pdf", "rb") as f:
            st.download_button("Preuzmi PDF", f, "plan_prihrane.pdf")