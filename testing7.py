import pandas as pd
import streamlit as st
import os
import psycopg2
from datetime import datetime

DB_FILE = "pengeluaran_kas.db"

def get_connection():
    return psycopg2.connect(
        host="aws-1-ap-southeast-1.pooler.supabase.com",
        database="postgres",
        user="postgres.fmvclahyaekbujfbkoaq",
        password="IsatechArthaJaya",
        port=6543
    )

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kas (
            id TEXT,
            tanggal TEXT,
            deskripsi_pekerjaan TEXT,
            deskripsi_pengeluaran TEXT,
            jumlah_barang INTEGER,
            unit TEXT,
            harga_per_satuan INTEGER,
            total_harga INTEGER,
            keterangan TEXT,
            po_number TEXT,
            invoice_number TEXT,
            surat_jalan_number TEXT
        )
    """)
    conn.commit()
    conn.close()

setup_database()

def load_data():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM kas", conn)
    df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    conn.close()
    return df

def save_data(row):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO kas (id, tanggal, deskripsi_pekerjaan, deskripsi_pengeluaran,
                         jumlah_barang, unit, harga_per_satuan, total_harga, keterangan,
                         po_number, invoice_number, surat_jalan_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", row)
    conn.commit()
    conn.close()

def delete_data_by_index(index):
    df = load_data()
    if index < len(df):
        id_to_delete = df.iloc[index]['id']
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kas WHERE id = %s", (id_to_delete,))
        conn.commit()
        conn.close()

def update_data_by_id(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE kas SET
            tanggal = %s,
            deskripsi_pekerjaan = %s,
            deskripsi_pengeluaran = %s,
            jumlah_barang = %s,
            unit = %s,
            harga_per_satuan = %s,
            total_harga = %s,
            keterangan = %s,
            po_number = %s,
            invoice_number = %s,
            surat_jalan_number = %s
        WHERE id = %s
    """, data)
    conn.commit()
    conn.close()

def generate_id_transaksi(kode_pelanggan, tanggal, df):
    prefix = kode_pelanggan.upper() if kode_pelanggan else "X1"
    bulan_tahun = tanggal.strftime("%m%y")
    filter_prefix = prefix + bulan_tahun
    df_filtered = df[df['id'].notna() & df['id'].astype(str).str.startswith(filter_prefix)]
    nomor_urut = len(df_filtered) + 1
    nomor_urut_str = f"{nomor_urut:03d}"
    return f"{filter_prefix}{nomor_urut_str}"

def format_rupiah(x):
    try:
        if isinstance(x, (int, float)):
            return f"Rp {x:,.0f}".replace(",", ".")
        return x
    except:
        return x

def print_data(df_to_print, no_voucher, nama_pengeluaran, total_pengeluaran):
    df_to_print = df_to_print.copy()
    df_to_print['harga_per_satuan'] = df_to_print['harga_per_satuan'].apply(format_rupiah)
    df_to_print['total_harga'] = df_to_print['total_harga'].apply(format_rupiah)
    total_pengeluaran_rupiah = format_rupiah(total_pengeluaran)

    html_content = df_to_print.to_html(index=False)

    full_html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Voucher Pengeluaran</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ text-align: center; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Voucher Pengeluaran</h1>
        <h3>No Voucher: {no_voucher}</h3>
        <h3>Nama Pengeluaran: {nama_pengeluaran}</h3>
        <h3>Total Pengeluaran: {total_pengeluaran_rupiah}</h3>
        {html_content}
    </body>
    </html>
    """

    html_path = "pengeluaran_kas_print.html"
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html_page)

        with open(html_path, "r", encoding="utf-8") as f:
            html_data = f.read()

        st.download_button(
            label="📥 Download Voucher (HTML)",
            data=html_data,
            file_name="voucher_pengeluaran.html",
            mime="text/html"
        )

        st.success("Laporan berhasil dibuat. Silakan download untuk melihat hasilnya.")
    except Exception as e:
        st.error(f"Gagal membuat atau membuka file HTML: {e}")

def print_invoice(invoice_data, items, output_file="invoice_print.html"):
    logo_base64 = "data:image/jpeg;base64,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"
    def format_rupiah(x):
        return f"Rp {x:,.0f}".replace(",", ".")
    items_html = ""
    for item in items:
        items_html += f"""
        <tr>
            <td style="text-align:center;">{item['no']}</td>
            <td>{item['description']}</td>
            <td style="text-align:center;">{item['qty']}</td>
            <td style="text-align:center;">{item['unit']}</td>
            <td style="text-align:right;">{format_rupiah(item['unit_price'])}</td>
            <td style="text-align:right;">{format_rupiah(item['total_price'])}</td>
        </tr>
        """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Invoice</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 40px;
                color: #222;
                background: #fff;
            }}
            .header {{
                display: flex;
                align-items: flex-start;
                border-bottom: 2px solid #005baa;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .logo {{
                width: 70px;
                height: auto;
                margin-right: 20px;
            }}
            .company-info {{
                flex: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            .company-name {{
                font-size: 2em;
                font-weight: bold;
                color: #005baa;
            }}
            .company-address {{
                font-size: 1em;
                color: #333;
                margin-bottom: 10px;
            }}
            .invoice-title {{
                font-size: 1.5em;
                font-weight: bold;
                margin: 30px 0 10px 0;
                color: #005baa;
            }}
            .info-table {{
                width: 100%;
                margin-bottom: 20px;
            }}
            .info-table td {{
                vertical-align: top;
                padding: 2px 8px;
                font-size: 1em;
            }}
            .main-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}
            .main-table th, .main-table td {{
                border: 1px solid #bbb;
                padding: 10px 12px;
                font-size: 1em;
            }}
            .main-table th {{
                background: #eaf3fa;
                font-weight: bold;
                text-align: center;
                color: #005baa;
            }}
            .summary-table {{
                float: right;
                width: 350px;
                border-collapse: collapse;
                margin-top: 10px;
                margin-bottom: 30px;
            }}
            .summary-table td {{
                padding: 8px 14px;
                font-size: 1em;
                border: none;
            }}
            .summary-table tr:not(:last-child) td {{
                border-bottom: 1px solid #eee;
            }}
            .summary-table tr:last-child td {{
                font-weight: bold;
                font-size: 1.2em;
                border-top: 2px solid #005baa;
                background: #eaf3fa;
                color: #005baa;
            }}
            .note {{
                margin-top: 60px;
                font-size: 1em;
            }}
            .signature {{
                margin-top: 60px;
                font-size: 1em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="data:image/jpeg;base64,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" class="logo" alt="Logo Perusahaan">
            <div class="company-info">
                <div class="company-name">{invoice_data['company_name']}</div>
                <div class="company-address">{invoice_data['company_address']}</div>
            </div>
        </div>
        <div class="invoice-title">INVOICE</div>
        <table class="info-table">
            <tr>
                <td style="width:50%; vertical-align:top;">
                    <b>TO:</b><br>{invoice_data['to']}
                </td>
                <td style="width:50%; vertical-align:top; text-align:right;">
                    <b>INVOICE DATE:</b> {invoice_data['invoice_date']}<br>
                    <b>INVOICE NO:</b> {invoice_data['invoice_no']}<br>
                    <b>CURRENCY:</b> {invoice_data['currency']}<br>
                    <b>PO NO:</b> {invoice_data['po_no']}<br>
                    <b>PO DATE:</b> {invoice_data['po_date']}<br>
                </td>
            </tr>
        </table>
        <table class="main-table">
            <tr>
                <th>NO</th>
                <th>DESCRIPTION</th>
                <th>QTY</th>
                <th>UNIT</th>
                <th>UNIT PRICE</th>
                <th>TOTAL PRICE</th>
            </tr>
            {items_html}
        </table>
        <table class="summary-table">
            <tr>
                <td style="text-align:right;">RETENSI 15%:</td>
                <td style="text-align:right;">{format_rupiah(invoice_data['retensi'])}</td>
            </tr>
            <tr>
                <td style="text-align:right;">SUB TOTAL:</td>
                <td style="text-align:right;">{format_rupiah(invoice_data['subtotal'])}</td>
            </tr>
            <tr>
                <td style="text-align:right;">PPN 11%:</td>
                <td style="text-align:right;">{format_rupiah(invoice_data['ppn'])}</td>
            </tr>
            <tr>
                <td style="text-align:right;">TOTAL:</td>
                <td style="text-align:right;">{format_rupiah(invoice_data['total'])}</td>
            </tr>
        </table>
        <div style="clear: both;"></div>
        <div class="note">
            <b>Note:</b><br>
            {invoice_data['bank_info']}
        </div>
        <div class="signature">
            <br><br>
            Best Regards,<br><br>
            ({invoice_data['sign_name']})
        </div>
    </body>
    </html>
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    with open(output_file, "r", encoding="utf-8") as f:
        html_data = f.read()
    st.download_button(
        label="📥 Download Invoice (HTML)",
        data=html_data,
        file_name="invoice.html",
        mime="text/html"
    )
    st.success("Invoice berhasil dibuat. Silakan download untuk melihat hasilnya.")

def print_surat_jalan(surat_jalan_data, items, output_file="surat_jalan_print.html"):
    logo_base64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/..."  # ...base64 logo Anda...
    items_html = ""
    for item in items:
        items_html += f"""
        <tr>
            <td style="text-align:center;">{item['no']}</td>
            <td>{item['description']}</td>
            <td style="text-align:center;">{item['qty']}</td>
        </tr>
        """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Surat Jalan</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 40px;
                color: #222;
                background: #fff;
            }}
            .header {{
                display: flex;
                align-items: center;
                border-bottom: 3px solid #1976d2;
                padding-bottom: 12px;
                margin-bottom: 28px;
            }}
            .logo {{
                width: 70px;
                height: auto;
                margin-right: 24px;
            }}
            .company-info {{
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            .company-name {{
                font-size: 2.2em;
                font-weight: bold;
                color: #1976d2;
                letter-spacing: 1px;
            }}
            .company-address {{
                font-size: 1.05em;
                color: #333;
                margin-top: 2px;
            }}
            .suratjalan-title {{
                font-size: 1.4em;
                font-weight: bold;
                color: #1976d2;
                margin: 32px 0 10px 0;
            }}
            .info-table {{
                width: 100%;
                margin-bottom: 18px;
            }}
            .info-table td {{
                vertical-align: top;
                padding: 2px 8px;
                font-size: 1em;
            }}
            .info-label {{
                font-weight: bold;
                color: #1976d2;
            }}
            .main-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 32px;
            }}
            .main-table th, .main-table td {{
                border: 1px solid #cfd8dc;
                padding: 12px 10px;
                font-size: 1em;
            }}
            .main-table th {{
                background: #e3f2fd;
                font-weight: bold;
                text-align: center;
                color: #1976d2;
                letter-spacing: 0.5px;
            }}
            .main-table td {{
                background: #fff;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="data:image/jpeg;base64,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" class="logo" alt="Logo Perusahaan">
            <div class="company-info">
                <div class="company-name">{surat_jalan_data['company_name']}</div>
                <div class="company-address">{surat_jalan_data['company_address']}</div>
            </div>
        </div>
        <div class="suratjalan-title">SURAT JALAN</div>
        <table class="info-table">
            <tr>
                <td style="width:25%; vertical-align:top;">
                    <span class="info-label">TANGGAL:</span> {surat_jalan_data['tanggal_surat_jalan']}
                </td>
                <td style="width:25%; vertical-align:top;">
                    <span class="info-label">KEPADA:</span> {surat_jalan_data['kepada']}
                </td>
                <td style="width:25%; vertical-align:top;">
                    <span class="info-label">NO SURAT JALAN:</span> {surat_jalan_data['no_surat_jalan']}
                </td>
                <td style="width:25%; vertical-align:top;">
                    <span class="info-label">PO NO:</span> {surat_jalan_data['po_no']}
                </td>
            </tr>
        </table>
        <table class="main-table">
            <tr>
                <th>NO</th>
                <th>DESCRIPTION</th>
                <th>QTY</th>
            </tr>
            {items_html}
        </table>
    </body>
    </html>
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    with open(output_file, "r", encoding="utf-8") as f:
        html_data = f.read()
    st.download_button(
        label="📥 Download Surat Jalan (HTML)",
        data=html_data,
        file_name="surat_jalan.html",
        mime="text/html"
    )
    st.success("Surat Jalan berhasil dibuat. Silakan download untuk melihat hasilnya.")

st.set_page_config(page_title="Pengeluaran Kas", layout="wide")
menu = st.sidebar.radio("Pilih Halaman", ["Dashboard", "Input Data", "Data & Pencarian", "Kelola Data", "Cetak Invoice", "Cetak Surat Jalan"])

if menu == "Dashboard":
    st.title("📊 Dashboard Pengeluaran")
    df = load_data()
    if not df.empty:
        total_harga = df['total_harga'].sum()
        avg_harga = df['total_harga'].mean()
        count = len(df)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pengeluaran", format_rupiah(total_harga))
        col2.metric("Rata-rata Pengeluaran", format_rupiah(avg_harga))
        col3.metric("Jumlah Transaksi", count)
        df['Bulan'] = df['tanggal'].dt.to_period('M').astype(str)
        monthly_summary = df.groupby('Bulan')['total_harga'].sum()
        st.line_chart(monthly_summary)
    else:
        st.warning("Belum ada data untuk ditampilkan.")

elif menu == "Input Data":
    st.title("📝 Input Pengeluaran Baru")
    df = load_data()
    kode_pelanggan = st.text_input("Kode Pelanggan", max_chars=10)
    tanggal = st.date_input("Tanggal", value=datetime.today())
    deskripsi_pekerjaan = st.text_area("Deskripsi Pekerjaan")
    deskripsi_pengeluaran = st.text_area("Deskripsi Pengeluaran")
    jumlah_barang = st.number_input("Jumlah Barang", min_value=1)
    unit = st.selectbox("Unit", ["pcs", "ea", "meter", "galon", "liter", "lot", "set", "assy", "kaleng", "pail", "unit", "lembar"])
    harga_per_satuan = st.number_input("Harga per Satuan", min_value=0)
    keterangan = st.text_input("Keterangan")
    po_number = st.text_input("PO Number (max 25 karakter)", max_chars=25)
    invoice_number = st.text_input("Invoice Number (max 12 karakter)", max_chars=12)
    surat_jalan_number = st.text_input("Surat Jalan Number (max 12 karakter)", max_chars=12)
    total_harga = jumlah_barang * harga_per_satuan

    if st.button("Simpan Data"):
        if not kode_pelanggan:
            st.error("Kode Pelanggan harus diisi.")
        elif not po_number:
            st.error("PO Number harus diisi.")
        elif not invoice_number:
            st.error("Invoice Number harus diisi.")
        elif not surat_jalan_number:
            st.error("Surat Jalan Number harus diisi.")
        else:
            id_transaksi = generate_id_transaksi(kode_pelanggan, tanggal, df)
            row = (id_transaksi, tanggal.strftime("%Y-%m-%d"), deskripsi_pekerjaan, deskripsi_pengeluaran,
                   jumlah_barang, unit, harga_per_satuan, total_harga, keterangan,
                   po_number, invoice_number, surat_jalan_number)
            save_data(row)
            st.session_state['success_message'] = f"Data ID {id_transaksi} berhasil disimpan!"
            st.rerun()
    if 'success_message' in st.session_state:
        st.success(st.session_state['success_message'])
        del st.session_state['success_message']

elif menu == "Data & Pencarian":
    st.title("🔍 Data & Pencarian")
    df = load_data()
    no_voucher = st.text_input("No Voucher (diisi manual)")
    unique_pengeluaran = df['deskripsi_pekerjaan'].dropna().unique()
    nama_pengeluaran = st.selectbox("Pilih Nama Pengeluaran", unique_pengeluaran)
    search_col1, search_col2, search_col3 = st.columns(3)
    with search_col1:
        search_pekerjaan = st.text_input("Cari Deskripsi Pekerjaan", key="search_pekerjaan")
    with search_col2:
        search_id = st.text_input("Cari ID Transaksi", key="search_id")
    with search_col3:
        search_tanggal = st.date_input("Cari Tanggal (Opsional)", value=None, key="search_tanggal")
    df_filtered = df.copy()
    if search_pekerjaan:
        df_filtered = df_filtered[df_filtered['deskripsi_pekerjaan'].astype(str).str.contains(search_pekerjaan, case=False, na=False)]
    if search_id:
        df_filtered = df_filtered[df_filtered['id'].astype(str).str.contains(search_id, case=False, na=False)]
    if search_tanggal:
        df_filtered_by_date = df_filtered[df_filtered['tanggal'].dt.strftime('%Y-%m-%d') == search_tanggal.strftime('%Y-%m-%d')]
        if not df_filtered_by_date.empty:
            df_filtered = df_filtered_by_date
        else:
            st.warning("Tidak ada data ditemukan untuk tanggal tersebut.")
            df_filtered = df.iloc[0:0]
    st.write("Menampilkan semua data.")
    df_tampil = df_filtered.copy()
    df_tampil['harga_per_satuan'] = df_tampil['harga_per_satuan'].apply(format_rupiah)
    df_tampil['total_harga'] = df_tampil['total_harga'].apply(format_rupiah)
    df_tampil['tanggal'] = df_tampil['tanggal'].dt.strftime('%Y-%m-%d')
    st.dataframe(df_tampil)
    col_download1, col_print_button = st.columns([1, 1])
    with col_download1:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Unduh CSV", csv, "hasil_pengeluaran.csv", "text/csv", key='download_csv')
    with col_print_button:
        if not df_filtered.empty:
            if st.button("🖨️ Cetak Data", key='print_html_data'):
                total_pengeluaran = df_filtered['total_harga'].sum()
                print_data(df_filtered, no_voucher, nama_pengeluaran, total_pengeluaran)
        else:
            st.info("Tidak ada data untuk dicetak.")

elif menu == "Kelola Data":
    st.title("✏️ Kelola Data")
    df = load_data()
    if 'delete_message' in st.session_state:
        st.success(st.session_state['delete_message'])
        del st.session_state['delete_message']
    if 'update_message' in st.session_state:
        st.success(st.session_state['update_message'])
        del st.session_state['update_message']
    if not df.empty:
        df_tampil = df.copy()
        df_tampil['harga_per_satuan'] = df_tampil['harga_per_satuan'].apply(format_rupiah)
        df_tampil['total_harga'] = df_tampil['total_harga'].apply(format_rupiah)
        df_tampil['tanggal'] = df_tampil['tanggal'].dt.strftime('%Y-%m-%d')
        st.dataframe(df_tampil)
        selected_index = st.number_input("Pilih Index untuk Edit/Hapus", min_value=0, max_value=len(df)-1, step=1)
        selected_row = df.iloc[selected_index]
        with st.expander("Edit Data Ini"):
            tanggal_value = selected_row['tanggal']
            if pd.isna(tanggal_value):
                tanggal_value = datetime.today()
            tanggal = st.date_input("Tanggal", value=pd.to_datetime(tanggal_value))
            deskripsi_pekerjaan = st.text_input("Deskripsi Pekerjaan", value=selected_row['deskripsi_pekerjaan'])
            deskripsi_pengeluaran = st.text_input("Deskripsi Pengeluaran", value=selected_row['deskripsi_pengeluaran'])
            jumlah_barang = st.number_input("Jumlah Barang", min_value=1, value=int(selected_row['jumlah_barang']))
            unit_options = ["pcs", "ea", "meter", "galon", "liter", "lot", "set", "assy", "kaleng", "pail", "unit", "lembar"]
            try:
                selected_unit_index = unit_options.index(selected_row['unit'])
            except ValueError:
                selected_unit_index = 0
            unit = st.selectbox("Unit", unit_options, index=selected_unit_index)
            harga_per_satuan = st.number_input("Harga per Satuan", min_value=0, value=int(selected_row['harga_per_satuan']))
            keterangan = st.text_input("Keterangan", value=selected_row['keterangan'])
            po_number = st.text_input("PO Number (max 25 karakter)", value=selected_row.get('po_number', ''), max_chars=25)
            invoice_number = st.text_input("Invoice Number (max 12 karakter)", value=selected_row.get('invoice_number', ''), max_chars=12)
            surat_jalan_number = st.text_input("Surat Jalan Number (max 12 karakter)", value=selected_row.get('surat_jalan_number', ''), max_chars=12)
            total_harga = jumlah_barang * harga_per_satuan
            if st.button("Simpan Perubahan"):
                data = (
                    tanggal.strftime("%Y-%m-%d"),
                    deskripsi_pekerjaan,
                    deskripsi_pengeluaran,
                    jumlah_barang,
                    unit,
                    harga_per_satuan,
                    total_harga,
                    keterangan,
                    po_number,
                    invoice_number,
                    surat_jalan_number,
                    selected_row['id']
                )
                update_data_by_id(data)
                st.session_state['update_message'] = "Perubahan berhasil disimpan!"
                st.rerun()
        if st.button("Hapus Data Ini"):
            id_transaksi = selected_row['id']
            delete_data_by_index(selected_index)
            st.session_state['delete_message'] = f"Data ID {id_transaksi} berhasil dihapus!"
            st.rerun()
    else:
        st.warning("Belum ada data.")

elif menu == "Cetak Invoice":
    st.title("🧾 Cetak Invoice")
    df = load_data()
    if not df.empty:
        df['tanggal'] = df['tanggal'].dt.strftime('%Y-%m-%d')
        df['label'] = df.apply(lambda x: f"{x['id']} | {x['deskripsi_pekerjaan']} | {x['tanggal']}", axis=1)
        selected_rows = st.multiselect(
            "Pilih Data Transaksi untuk Invoice",
            options=df.index,
            format_func=lambda idx: df.loc[idx, 'label']
        )
        po_no = ""
        invoice_no = ""
        surat_jalan_no = ""
        if len(selected_rows) == 1:
            row = df.loc[selected_rows[0]]
            po_no = row.get('po_number', '')
            invoice_no = row.get('invoice_number', '')
            surat_jalan_no = row.get('surat_jalan_number', '')
        elif len(selected_rows) > 1:
            po_no = ", ".join(df.loc[selected_rows, 'po_number'].dropna().unique())
            invoice_no = ", ".join(df.loc[selected_rows, 'invoice_number'].dropna().unique())
            surat_jalan_no = ", ".join(df.loc[selected_rows, 'surat_jalan_number'].dropna().unique())
        company_name = st.text_input("Nama Perusahaan", value="PT. ISATECH ARTHA JAYA")
        company_address = st.text_area("Alamat Perusahaan", value="Jl. ...")
        to = st.text_area("Kepada", value="PT. LION MENTARI ...")
        invoice_date = st.date_input("Tanggal Invoice", value=datetime.today())
        invoice_no_input = st.text_input("No Invoice", value=invoice_no, key="invoice_no_input")
        currency = st.text_input("Mata Uang", value="IDR")
        po_no_input = st.text_input("No PO", value=po_no, key="po_no_input")
        surat_jalan_no_input = st.text_input("No Surat Jalan", value=surat_jalan_no, key="surat_jalan_no_input")
        po_date = st.date_input("Tanggal PO", value=datetime.today())
        bank_info = st.text_area("Info Bank", value="...")
        sign_name = st.text_input("Nama Penanda Tangan", value="Indra Budihartono")
        items = []
        subtotal = 0
        for i, idx in enumerate(selected_rows, 1):
            row = df.loc[idx]
            total_harga = int(row['total_harga']) if not pd.isna(row['total_harga']) else 0
            items.append({
                "no": i,
                "description": row['deskripsi_pekerjaan'],
                "qty": int(row['jumlah_barang']),
                "unit": row['unit'],
                "unit_price": int(row['harga_per_satuan']),
                "total_price": total_harga
            })
            subtotal += total_harga
        retensi = int(subtotal * 0.15)
        ppn = int(subtotal * 0.11)
        total = subtotal + ppn + retensi
        if items:
            st.write("**Preview Item Invoice:**")
            st.table(pd.DataFrame(items))
        st.write(f"**Subtotal:** {format_rupiah(subtotal)}")
        st.write(f"**Retensi 15%:** {format_rupiah(retensi)}")
        st.write(f"**PPN 11%:** {format_rupiah(ppn)}")
        st.write(f"**Total:** {format_rupiah(total)}")
        if st.button("Cetak Invoice"):
            invoice_data = {
                "company_name": company_name,
                "company_address": company_address,
                "to": to,
                "invoice_date": invoice_date.strftime("%d/%m/%Y"),
                "invoice_no": invoice_no_input,
                "currency": currency,
                "po_no": po_no_input,
                "po_date": po_date.strftime("%d/%m/%Y"),
                "retensi": retensi,
                "subtotal": subtotal,
                "ppn": ppn,
                "total": total,
                "bank_info": bank_info,
                "sign_name": sign_name,
                "surat_jalan_no": surat_jalan_no_input
            }
            print_invoice(invoice_data, items)
    else:
        st.info("Belum ada data transaksi untuk dibuat invoice.")

elif menu == "Cetak Surat Jalan":
    st.title("🚚 Cetak Surat Jalan")
    df = load_data()
    if not df.empty:
        df['tanggal'] = df['tanggal'].dt.strftime('%Y-%m-%d')
        df['label'] = df.apply(lambda x: f"{x['id']} | {x['deskripsi_pekerjaan']} | {x['tanggal']}", axis=1)
        selected_rows = st.multiselect(
            "Pilih Data Transaksi untuk Surat Jalan",
            options=df.index,
            format_func=lambda idx: df.loc[idx, 'label']
        )
        kepada = ""
        tanggal_surat_jalan = ""
        no_surat_jalan = ""
        po_no = ""
        if selected_rows:
            row = df.loc[selected_rows[0]]
            kepada = row.get('kepada', '')
            tanggal_surat_jalan = row.get('tanggal', '')
            no_surat_jalan = row.get('surat_jalan_number', '')
            po_no = row.get('po_number', '')
        company_name = st.text_input("Nama Perusahaan", value="PT. ISATECH ARTHA JAYA")
        company_address = st.text_area("Alamat Perusahaan", value="Jl. ...")
        kepada = st.text_input("Kepada", value=kepada)
        tanggal_surat_jalan = st.text_input("Tanggal Surat Jalan", value=tanggal_surat_jalan)
        no_surat_jalan = st.text_input("No Surat Jalan", value=no_surat_jalan)
        po_no = st.text_input("PO Number", value=po_no)
        items = []
        for i, idx in enumerate(selected_rows, 1):
            row = df.loc[idx]
            items.append({
                "no": i,
                "description": row['deskripsi_pekerjaan'],
                "qty": int(row['jumlah_barang'])
            })
        if items and st.button("Cetak Surat Jalan"):
            surat_jalan_data = {
                "company_name": company_name,
                "company_address": company_address,
                "kepada": kepada,
                "tanggal_surat_jalan": tanggal_surat_jalan,
                "no_surat_jalan": no_surat_jalan,
                "po_no": po_no,
            }
            print_surat_jalan(surat_jalan_data, items)
    else:
        st.info("Belum ada data transaksi untuk dibuat surat jalan.")
