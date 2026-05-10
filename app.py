import streamlit as st
import pdfplumber
from fpdf import FPDF
import pandas as pd

st.set_page_config(page_title="Agronom Pro v3.4", layout="wide")

st.title("🌱 Agronom Pro - Kornišon v3.4")

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
    t = str(t).replace(',', '.')
    # Zadrži samo brojeve i tačku
    broj = "".join(c for c in t if c.isdigit() or c == '.')
    try:
        return float(broj) if broj else 0.0
    except:
        return 0.0

if uploaded_file is not None:
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            table = pdf.pages[0].extract_table()
            
            if table and len(table) > 1:
                data_row = table[1]
                
                # --- AUTOMATSKO PREPOZNAVANJE KOLONA ---
                # Ako su N i P spojeni u jednoj ćeliji (čest slučaj)
                npk_pronadjen = False
                podaci = {'ec': 0.0, 'vlaznost': 0.0, 'n': 0.0, 'p': 0.0, 'k': 0.0, 'ph': 0.0}

                # Mapiranje po pretpostavljenim pozicijama (proširena provera)
                podaci['ec'] = clean(data_row[5]) if len(data_row) > 5 else 0.0
                podaci['vlaznost'] = clean(data_row[6]) if len(data_row) > 6 else 0.0
                podaci['ph'] = clean(data_row[-1]) if len(data_row) > 0 else 0.0 # PH je obično zadnji
                
                # Pokušaj izvlačenja N, P, K iz ćelija 7 i 8
                if len(data_row) > 7:
                    sadrzaj_7 = str(data_row[7]).split('\n')
                    podaci['n'] = clean(sadrzaj_7[0])
                    if len(sadrzaj_7) > 1:
                        podaci['p'] = clean(sadrzaj_7[1])
                
                if len(data_row) > 8:
                    podaci['k'] = clean(data_row[8])

                # --- PRIKAZ REZULTATA ---
                st.success("✅ PDF uspešno analiziran")
                
                # Tabela sa očitanim vrednostima
                st.subheader("📊 Izmerene vrednosti sa senzora")
                kolone_prikaz = st.columns(5)
                kolone_prikaz[0].metric("EC", podaci['ec'])
                kolone_prikaz[1].metric("pH", podaci['ph'])
                kolone_prikaz[2].metric("Azot (N)", podaci['n'])
                kolone_prikaz[3].metric("Fosfor (P)", podaci['p'])
                kolone_prikaz[4].metric("Kalijum (K)", podaci['k'])

                st.divider()

                # Receptura
                f = faze[izabrana_faza]
                doza = f['g_max'] if podaci['ec'] < (f['ec_cilj'] * 0.5) else f['g_min']
                voda = max(0.4, ((80.0 - podaci['vlaznost']) * 0.015) + 0.4) if podaci['vlaznost'] < 80 else 0.4

                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("📝 Dnevni recept")
                    st.info(f"Osnovno đubrivo: **{f['osnovno']}**")
                    st.write(f"Količina: **{doza:.2f} gr / biljci**")
                    st.write(f"Huminske kiseline: **{f['hum']} ml**")
                
                with c2:
                    st.subheader("💧 Navodnjavanje")
                    st.write(f"Vlažnost zemljišta: {podaci['vlaznost']}%")
                    st.write(f"Preporuka vode: **{voda:.2f} L / biljci**")

                # DEBUG MOD (Samo ako ne vidiš brojeve, otvori ovo da vidiš gde greši)
                with st.expander("Sadržaj PDF tabele (za tehničku proveru)"):
                    st.write(data_row)

            else:
                st.error("Tabela nije pronađena u PDF-u.")
    except Exception as e:
        st.error(f"Greška: {e}")