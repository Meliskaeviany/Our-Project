import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os

# =========================
# STYLE MAROON & PUTIH
# =========================
st.markdown("""
<style>
.stApp {background-color: #740505; color: #fefdfd;}
h1,h2,h3,h4,h5,h6 {color: #fefdfd;}
[data-testid="stSidebar"] {background-color: #5c0303; color: #fefdfd;}
div.stButton > button {background-color: #9c0a0a; color: #fefdfd;}
div[data-testid="metric-container"] {background-color: #8b0c0c; color: #fefdfd; padding:15px; border-radius:10px;}
</style>
""", unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
USERS = ["Steward","Meliska"]
PASSWORD = "1312"
log_file = "log_login.csv"

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
            # Simpan log login
            login_data = pd.DataFrame([{
                "Username": username,
                "Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            if os.path.exists(log_file):
                login_data.to_csv(log_file, mode='a', header=False, index=False)
            else:
                login_data.to_csv(log_file, index=False)
            st.rerun()
        else:
            st.error("Username atau password salah")
    st.stop()

# =========================
# CSV FILES
# =========================
transaksi_file = "transaksi.csv"
pembagian_file = "pembagian.csv"

def load_csv(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        return pd.DataFrame(columns=columns)

st.session_state.transaksi = load_csv(transaksi_file,
                                      ["Tanggal","Jenis","Keterangan","Unit","Pemasukan","Pengeluaran","Rekening","SubRekening"])
st.session_state.pembagian = load_csv(pembagian_file,
                                      ["Tanggal","Keuntungan","Persepuluhan","Tabungan","Modal","Partner","Rekening","SubRekening"])

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
    rekening = st.selectbox("Kategori Rekening", ["Rekening Bersama", "Aladin"])
    subrekening = ""
    if rekening == "Rekening Bersama":
        subrekening = st.selectbox("SubRekening", ["BCA Steward", "BCA Meliska"])
    elif rekening == "Aladin":
        subrekening = st.selectbox("SubRekening", ["Aladin Steward", "Aladin Meliska"])

if st.button("Simpan Transaksi"):
    new_data = pd.DataFrame([{
        "Tanggal": tanggal,
        "Jenis": jenis,
        "Keterangan": keterangan,
        "Unit": unit,
        "Pemasukan": pemasukan_input,
        "Pengeluaran": pengeluaran_input,
        "Rekening": rekening,
        "SubRekening": subrekening
    }])
    st.session_state.transaksi = pd.concat([st.session_state.transaksi,new_data], ignore_index=True)
    st.session_state.transaksi.to_csv(transaksi_file, index=False)
    st.success("Transaksi berhasil disimpan")

# =========================
# DATA TRANSAKSI & HAPUS
# =========================
st.subheader("Data Transaksi")
st.dataframe(st.session_state.transaksi)

st.markdown("#### Hapus Baris Transaksi")
hapus_index = st.number_input("Masukkan index baris untuk dihapus:", min_value=0, max_value=len(st.session_state.transaksi)-1 if len(st.session_state.transaksi)>0 else 0)
if st.button("Hapus Transaksi"):
    if len(st.session_state.transaksi) > 0:
        st.session_state.transaksi = st.session_state.transaksi.drop(hapus_index).reset_index(drop=True)
        st.session_state.transaksi.to_csv(transaksi_file, index=False)
        st.success("Transaksi berhasil dihapus")
st.divider()

# =========================
# GRAFIK KEUANGAN HARIAN
# =========================
st.subheader("Grafik Keuangan Harian")
df = st.session_state.transaksi.copy()
if not df.empty:
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    grafik = df.groupby("Tanggal").agg(
        Pemasukan=("Pemasukan","sum"),
        Pengeluaran=("Pengeluaran","sum")
    )
    grafik["Keuntungan"] = grafik["Pemasukan"] - grafik["Pengeluaran"]
    st.line_chart(grafik)

# =========================
# GRAFIK KEUANGAN BULANAN
# =========================
st.subheader("Grafik Keuangan Bulanan")
if not df.empty:
    df["Bulan"] = df["Tanggal"].dt.to_period("M")
    bulanan = df.groupby("Bulan").agg(
        Pemasukan=("Pemasukan","sum"),
        Pengeluaran=("Pengeluaran","sum")
    )
    bulanan["Keuntungan"] = bulanan["Pemasukan"] - bulanan["Pengeluaran"]
    st.line_chart(bulanan)
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

rekening_pb = st.selectbox("Pilih Rekening Pembagian", ["Rekening Bersama","Aladin"])
subrekening_pb = ""
if rekening_pb == "Rekening Bersama":
    subrekening_pb = st.selectbox("SubRekening", ["BCA Steward", "BCA Meliska"])
elif rekening_pb == "Aladin":
    subrekening_pb = st.selectbox("SubRekening", ["Aladin Steward", "Aladin Meliska"])

st.write("Persepuluhan :", rupiah(persepuluhan))
st.write("Tabungan :", rupiah(tabungan))
st.write("Modal :", rupiah(modal))
st.write("Partner :", rupiah(partner))

if st.button("Simpan Pembagian"):
    new_data = pd.DataFrame([{
        "Tanggal": datetime.today().strftime("%Y-%m-%d"),
        "Keuntungan": keuntungan_input,
        "Persepuluhan": persepuluhan,
        "Tabungan": tabungan,
        "Modal": modal,
        "Partner": partner,
        "Rekening": rekening_pb,
        "SubRekening": subrekening_pb
    }])
    st.session_state.pembagian = pd.concat([st.session_state.pembagian,new_data], ignore_index=True)
    st.session_state.pembagian.to_csv(pembagian_file, index=False)
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
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(306, 750, "LAPORAN KEUANGAN USAHA")
    tanggal_laporan = datetime.now().strftime("%d %B %Y")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(306, 730, f"Tanggal Laporan: {tanggal_laporan}")
    pdf.line(50, 720, 562, 720)
    y = 690
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Tanggal")
    pdf.drawString(150, y, "Jenis")
    pdf.drawString(300, y, "Pemasukan")
    pdf.drawString(420, y, "Pengeluaran")
    pdf.drawString(500, y, "Rekening/Sub")
    y -= 10
    pdf.line(50, y, 562, y)
    y -= 20
    pdf.setFont("Helvetica", 10)
    for i, row in st.session_state.transaksi.iterrows():
        pdf.drawString(50, y, str(row["Tanggal"]))
        pdf.drawString(150, y, str(row["Jenis"]))
        pdf.drawString(300, y, rupiah(row["Pemasukan"]))
        pdf.drawString(420, y, rupiah(row["Pengeluaran"]))
        pdf.drawString(500, y, str(row["Rekening"])+"/"+str(row["SubRekening"]))
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

# =========================
# LIHAT LOG LOGIN
# =========================
st.divider()
st.subheader("Login History")
if st.button("📋 Lihat Log Login"):
    if os.path.exists("log_login.csv"):
        log_df = pd.read_csv("log_login.csv")
        st.dataframe(log_df)
    else:
        st.write("Belum ada login yang tercatat.")
