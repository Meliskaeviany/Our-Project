import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# =========================
# STYLE MAROON & PUTIH
# =========================
st.markdown(
    """
    <style>
    /* Background utama */
    .stApp {
        background-color: #740505;
        color: #fefdfd;
    }

    /* Judul dan header */
    h1,h2,h3,h4,h5,h6 {
        color: #fefdfd;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #5c0303;
        color: #fefdfd;
    }

    /* Tombol */
    div.stButton > button {
        background-color: #9c0a0a;
        color: #fefdfd;
    }

    /* Metric card */
    div[data-testid="metric-container"] {
        background-color: #8b0c0c;
        color: #fefdfd;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# LOGIN
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
            st.rerun()
        else:
            st.error("Username atau password salah")
    st.stop()

# =========================
# DATA STORAGE
# =========================
if "transaksi" not in st.session_state:
    st.session_state.transaksi = pd.DataFrame(
        columns=["Tanggal","Jenis","Keterangan","Unit","Pemasukan","Pengeluaran"]
    )

if "pembagian" not in st.session_state:
    st.session_state.pembagian = pd.DataFrame(
        columns=["Tanggal","Keuntungan","Persepuluhan","Tabungan","Modal","Partner"]
    )

# =========================
# FORMAT RUPIAH
# =========================
def rupiah(x):
    return "Rp {:,}".format(int(x)).replace(",", ".")

# =========================
# DASHBOARD
# =========================
st.title("Dashboard Keuangan Usaha")

pemasukan = st.session_state.transaksi["Pemasukan"].sum()
pengeluaran = st.session_state.transaksi["Pengeluaran"].sum()
keuntungan = pemasukan - pengeluaran

col1, col2, col3 = st.columns(3)
col1.metric("Total Pemasukan", rupiah(pemasukan))
col2.metric("Total Pengeluaran", rupiah(pengeluaran))
col3.metric("Keuntungan", rupiah(keuntungan))

if keuntungan < 0:
    st.warning("⚠ Usaha mengalami kerugian")

st.divider()

# =========================
# INPUT TRANSAKSI
# =========================
st.subheader("Input Transaksi")
col1, col2 = st.columns(2)

with col1:
    tanggal = st.date_input("Tanggal")
    jenis = st.selectbox("Jenis Transaksi", ["Penjualan","Pembelian Barang","Modal Masuk","Operasional"])
    keterangan = st.text_input("Keterangan")
with col2:
    unit = st.number_input("Jumlah Unit",0)
    pemasukan_input = st.number_input("Pemasukan",0)
    pengeluaran_input = st.number_input("Pengeluaran",0)

if st.button("Simpan Transaksi"):
    data = {
        "Tanggal":tanggal,
        "Jenis":jenis,
        "Keterangan":keterangan,
        "Unit":unit,
        "Pemasukan":pemasukan_input,
        "Pengeluaran":pengeluaran_input
    }
    st.session_state.transaksi = pd.concat([st.session_state.transaksi,pd.DataFrame([data])], ignore_index=True)
    st.success("Transaksi berhasil disimpan")

st.divider()

# =========================
# DATA TRANSAKSI
# =========================
st.subheader("Data Transaksi")
st.dataframe(st.session_state.transaksi)

st.divider()

# =========================
# GRAFIK KEUANGAN
# =========================
st.subheader("Grafik Keuangan")
df = st.session_state.transaksi.copy()
if not df.empty:
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    grafik = df.groupby("Tanggal").agg(Pemasukan=("Pemasukan","sum"),
                                       Pengeluaran=("Pengeluaran","sum"))
    grafik["Keuntungan"] = grafik["Pemasukan"] - grafik["Pengeluaran"]
    st.line_chart(grafik)

st.divider()

# =========================
# REKAP BULANAN
# =========================
st.subheader("Rekap Bulanan")
if not df.empty:
    df["Bulan"] = df["Tanggal"].dt.month
    rekap = df.groupby("Bulan").agg(Pemasukan=("Pemasukan","sum"),
                                    Pengeluaran=("Pengeluaran","sum"))
    rekap["Keuntungan"] = rekap["Pemasukan"] - rekap["Pengeluaran"]
    st.dataframe(rekap)

st.divider()

# =========================
# PEMBAGIAN KEUNTUNGAN
# =========================
st.subheader("Pembagian Keuntungan")
keuntungan_input = st.number_input("Masukkan Total Keuntungan",0)
persepuluhan = keuntungan_input * 0.10
tabungan = keuntungan_input * 0.50
modal = keuntungan_input * 0.30
partner = keuntungan_input * 0.10

st.write("Persepuluhan :", rupiah(persepuluhan))
st.write("Tabungan :", rupiah(tabungan))
st.write("Modal :", rupiah(modal))
st.write("Partner :", rupiah(partner))

if st.button("Simpan Pembagian"):
    data = {
        "Tanggal":datetime.today(),
        "Keuntungan":keuntungan_input,
        "Persepuluhan":persepuluhan,
        "Tabungan":tabungan,
        "Modal":modal,
        "Partner":partner
    }
    st.session_state.pembagian = pd.concat([st.session_state.pembagian,pd.DataFrame([data])], ignore_index=True)
    st.success("Pembagian tersimpan")

st.dataframe(st.session_state.pembagian)

st.divider()

# =========================
# DOWNLOAD PDF
# =========================
st.subheader("Download Laporan PDF")

def buat_pdf():
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    # Judul Bold di Tengah
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(306, 750, "LAPORAN KEUANGAN USAHA")

    # Tanggal laporan
    tanggal_laporan = datetime.now().strftime("%d %B %Y")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(306, 730, f"Tanggal Laporan: {tanggal_laporan}")

    # Garis pemisah
    pdf.line(50, 720, 562, 720)

    # Header tabel
    y = 690
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Tanggal")
    pdf.drawString(150, y, "Jenis")
    pdf.drawString(300, y, "Pemasukan")
    pdf.drawString(420, y, "Pengeluaran")
    y -= 10
    pdf.line(50, y, 562, y)
    y -= 20

    # Data transaksi
    pdf.setFont("Helvetica", 10)
    for i, row in st.session_state.transaksi.iterrows():
        pdf.drawString(50, y, str(row["Tanggal"]))
        pdf.drawString(150, y, str(row["Jenis"]))
        pdf.drawString(300, y, str(row["Pemasukan"]))
        pdf.drawString(420, y, str(row["Pengeluaran"]))
        y -= 20
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = 750

    pdf.save()
    buffer.seek(0)
    return buffer

pdf_file = buat_pdf()
st.download_button(
    label="📥 Download PDF",
    data=pdf_file,
    file_name="laporan_keuangan.pdf",
    mime="application/pdf"
)
