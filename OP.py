import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

st.set_page_config(page_title="Keuangan Usaha", layout="wide")

# =========================
# LOGIN SYSTEM
# =========================

USERS = ["Steward","Meliska"]
PASSWORD = "1312"

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("Login Aplikasi Keuangan")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and password == PASSWORD:
            st.session_state.login = True
            st.session_state.user = username
            st.success("Login berhasil")
            st.rerun()
        else:
            st.error("Username atau password salah")

    st.stop()

st.sidebar.success(f"Login sebagai: {st.session_state.user}")

# =========================
# STYLE MAROON
# =========================

st.markdown("""
<style>
h1,h2,h3{color:#800000;}
div[data-testid="metric-container"]{
background-color:#800000;
color:white;
padding:15px;
border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# DATA STORAGE
# =========================

if "transaksi" not in st.session_state:
    st.session_state.transaksi = pd.DataFrame(
        columns=["Tanggal","Jenis","Keterangan","Unit","Pemasukan","Pengeluaran"]
    )

if "pembagian" not in st.session_state:
    st.session_state.pembagian = pd.DataFrame(
        columns=["Tanggal","Keuntungan","Persepuluhan","Tabungan","Modal","Partner",
                 "Cek Persepuluhan","Cek Tabungan","Cek Modal","Cek Partner"]
    )

# =========================
# FORMAT RUPIAH
# =========================

def rupiah(x):
    return "Rp {:,}".format(int(x)).replace(",", ".")

# =========================
# MENU
# =========================

menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard","Transaksi Usaha","Rekap Bulanan","Pembagian Keuntungan","Laporan Lengkap"]
)

# =========================
# DASHBOARD
# =========================

if menu == "Dashboard":

    st.title("Our Project")

    pemasukan = st.session_state.transaksi["Pemasukan"].sum()
    pengeluaran = st.session_state.transaksi["Pengeluaran"].sum()
    keuntungan = pemasukan - pengeluaran

    col1,col2,col3 = st.columns(3)

    col1.metric("Total Pemasukan", rupiah(pemasukan))
    col2.metric("Total Pengeluaran", rupiah(pengeluaran))
    col3.metric("Keuntungan", rupiah(keuntungan))

    if keuntungan < 0:
        st.warning("⚠ Usaha mengalami kerugian")

    st.subheader("Transaksi Terakhir")
    st.dataframe(st.session_state.transaksi)

# =========================
# TRANSAKSI USAHA
# =========================

if menu == "Transaksi Usaha":

    st.title("Input Transaksi Usaha")

    tanggal = st.date_input("Tanggal")
    jenis = st.selectbox("Jenis Transaksi",
                         ["Modal Awal","Pembelian Unit","Penjualan Unit","Operasional"])

    ket = st.text_input("Keterangan")
    unit = st.number_input("Jumlah Unit",0)
    pemasukan = st.number_input("Pemasukan",0)
    pengeluaran = st.number_input("Pengeluaran",0)

    if st.button("Simpan Transaksi"):

        data = {
            "Tanggal":tanggal,
            "Jenis":jenis,
            "Keterangan":ket,
            "Unit":unit,
            "Pemasukan":pemasukan,
            "Pengeluaran":pengeluaran
        }

        st.session_state.transaksi = pd.concat(
            [st.session_state.transaksi,pd.DataFrame([data])],
            ignore_index=True
        )

        st.success("Transaksi tersimpan")

    st.dataframe(st.session_state.transaksi)

# =========================
# REKAP BULANAN
# =========================

if menu == "Rekap Bulanan":

    st.title("Rekap Usaha Bulanan")

    df = st.session_state.transaksi.copy()

    if not df.empty:
        df["Bulan"] = pd.to_datetime(df["Tanggal"]).dt.month

        rekap = df.groupby("Bulan").agg(
            Pemasukan=("Pemasukan","sum"),
            Pengeluaran=("Pengeluaran","sum"),
            Unit=("Unit","sum")
        )

        rekap["Keuntungan"] = rekap["Pemasukan"] - rekap["Pengeluaran"]

        st.dataframe(rekap)

        if (rekap["Keuntungan"] < 0).any():
            st.warning("⚠ Ada bulan yang mengalami kerugian")

# =========================
# PEMBAGIAN KEUNTUNGAN
# =========================

if menu == "Pembagian Keuntungan":

    st.title("Pembagian Keuntungan")

    keuntungan = st.number_input("Jumlah Keuntungan",0)

    persepuluhan = keuntungan * 0.10
    tabungan = keuntungan * 0.50
    modal = keuntungan * 0.30
    partner = keuntungan * 0.10

    st.write("Persepuluhan:", rupiah(persepuluhan))
    st.write("Tabungan:", rupiah(tabungan))
    st.write("Modal Usaha:", rupiah(modal))
    st.write("Partner:", rupiah(partner))

    cek1 = st.checkbox("Persepuluhan sudah disalurkan")
    cek2 = st.checkbox("Tabungan sudah disimpan")
    cek3 = st.checkbox("Modal sudah dimasukkan")
    cek4 = st.checkbox("Pembagian partner sudah diberikan")

    if st.button("Simpan Pembagian"):

        data = {
            "Tanggal":datetime.today(),
            "Keuntungan":keuntungan,
            "Persepuluhan":persepuluhan,
            "Tabungan":tabungan,
            "Modal":modal,
            "Partner":partner,
            "Cek Persepuluhan":cek1,
            "Cek Tabungan":cek2,
            "Cek Modal":cek3,
            "Cek Partner":cek4
        }

        st.session_state.pembagian = pd.concat(
            [st.session_state.pembagian,pd.DataFrame([data])],
            ignore_index=True
        )

        st.success("Data pembagian tersimpan")

    st.dataframe(st.session_state.pembagian)

# =========================
# LAPORAN PDF
# =========================

if menu == "Laporan Lengkap":

    st.title("Laporan Keuangan Lengkap")

    st.subheader("Transaksi Usaha")
    st.dataframe(st.session_state.transaksi)

    st.subheader("Pembagian Keuntungan")
    st.dataframe(st.session_state.pembagian)

    def buat_pdf():

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer,pagesize=letter)

        pdf.drawString(100,750,"Laporan Keuangan Usaha")

        y = 700

        for i,row in st.session_state.transaksi.iterrows():
            text = f"{row['Tanggal']} - {row['Jenis']} - {row['Keterangan']} - {row['Pemasukan']} - {row['Pengeluaran']}"
            pdf.drawString(50,y,text)
            y -= 20

        pdf.save()

        buffer.seek(0)
        return buffer

    pdf_file = buat_pdf()

    st.download_button(
        label="Download PDF",
        data=pdf_file,
        file_name="laporan_keuangan.pdf",
        mime="application/pdf"
    )