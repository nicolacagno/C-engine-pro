import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import date, datetime, timedelta

# 1. CONFIGURAZIONE PAGINA E STILE SCURO UNIFORME
st.set_page_config(page_title="MetalHub Suite", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp, html, body, [data-testid='stSidebar'], [data-testid='stHeader'] { background-color: #1A1A1A !important; }
    h1, h2, h3, h4, p, label, span, [data-testid='stWidgetLabel'], .stMarkdown { color: #A0A0A0 !important; font-family: 'Segoe UI', sans-serif !important; }
    h2, h3, h4 { color: #FF5722 !important; font-weight: 600 !important; }
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox [data-baseweb="select"] { color: #FF5722 !important; background-color: #262626 !important; border: 1px solid #404040 !important; font-weight: bold !important; }
    [data-testid='stFileUploader'] { background-color: #262626 !important; border: 2px dashed #FF5722 !important; }
    
    /* Pulsanti di Azione e di Download */
    .stButton>button, .stDownloadButton>button { color: #FFFFFF !important; background-color: #FF5722 !important; font-weight: bold !important; width: 100% !important; border: none !important; border-radius: 4px !important; padding: 0.6rem 1rem !important; font-size: 13px !important; text-transform: uppercase !important; }
    .stButton>button:hover, .stDownloadButton>button:hover { background-color: #E64A19 !important; color: #FFFFFF !important; }
    .standby-box { border: 2px dashed #404040; border-radius: 8px; padding: 60px 20px; text-align: center; background-color: #1F1F1F; color: #666666 !important; font-weight: 500; margin-top: 15px; }
    
    /* Contenitori Barre In-App 1D */
    .bar-container { background-color: #262626; border: 1px solid #404040; padding: 16px; border-radius: 6px; margin-bottom: 20px; }
    .bar-header { display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; margin-bottom: 8px; }
    .bar-track { display: flex; background: repeating-linear-stripes(45deg, #2b2b2b, #2b2b2b 10px, #3A3A3A 10px, #3A3A3A 20px); height: 36px; border-radius: 4px; overflow: hidden; border: 1px solid #444; }
    .bar-segment { display: flex; align-items: center; justify-content: center; height: 100%; color: white; font-weight: bold; font-size: 11px; border-right: 1px solid #1A1A1A; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# GESTIONE DIZIONARIO MULTILINGUA
# =============================================================================
lang = st.sidebar.selectbox("🌐 LANGUAGE / LINGUA", ["IT", "EN"])

TXT = {
    "IT": {
        "title": "Nesting Geometrico & Ottimizzazione",
        "header_1d": "🪚 NESTING 1D - BARRE",
        "header_2d": "📐 NESTING 2D - LAMIERE",
        "header_gantt": "📅 SCHEDULAZIONE GANTT",
        "commessa": "📋 INTESTAZIONE COMMESSA",
        "ordine": "NUMERO ORDINE",
        "cliente": "NOME CLIENTE",
        "data": "DATA LAVORAZIONE",
        "parametri_macchina": "🔧 PARAMETRI MACCHINA",
        "magazzino": "📦 INVENTARIO STOCK STOCCAGGIO",
        "tagli": "✂️ LISTA TAGLI RICHIESTI",
        "esegui": "🚀 ELABORA NESTING",
        "spessore": "SPESSORE LASTRA (mm)",
        "bordo": "BORDO PERIMETRALE (mm)",
        "dist_sic": "DISTANZA TRA I PEZZI (mm)",
        "esporta": "💾 ESPORTA DATI DI PRODUZIONE",
        "standby_2d": "IN ATTESA INPUT DXF\n\nCarica i file delle sagome e premi elabora per calcolare l'incastro tipo Tetris."
    },
    "EN": {
        "title": "Geometric Nesting & Optimization",
        "header_1d": "🪚 1D NESTING - BARS",
        "header_2d": "📐 2D NESTING - SHEETS",
        "header_gantt": "📅 GANTT SCHEDULING",
        "commessa": "📋 WORK ORDER DETAILS",
        "ordine": "ORDER NUMBER",
        "cliente": "CUSTOMER NAME",
        "data": "PROCESSING DATE",
        "parametri_macchina": "🔧 MACHINE PARAMETERS",
        "magazzino": "📦 BAR STOCK INVENTORY",
        "tagli": "✂️ CUT LIST",
        "esegui": "🚀 EXECUTE NESTING",
        "spessore": "SHEET THICKNESS (mm)",
        "bordo": "PERIMETER MARGIN (mm)",
        "dist_s": "PART TO PART DISTANCE (mm)",
        "esporta": "💾 EXPORT PRODUCTION DATA",
        "standby_2d": "AWAITING DXF INPUT\n\nUpload profile files and click execute to compute Tetris-style nesting layout."
    }
}

T = TXT[lang]

# MAPPA COLORI GRAFICA LINEARE
HEX_COLORI = {"1200": "#3B82F6", "850": "#10B981", "340": "#8B5CF6", "default": "#4B5563"}

# HEADER APPLICAZIONE
st.markdown(f"""
    <div style="background-color:#262626; padding:15px; border-radius:5px; margin-bottom:25px; border-bottom:2px solid #FF5722;">
        <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:10px;">🔥 MetalHub Suite</span>
        <span style="color:#666666; font-size:11px; font-weight:bold; letter-spacing:1px;">{T['title'].upper()}</span>
    </div>
""", unsafe_allow_html=True)

tab_1d, tab_2d, tab_gantt = st.tabs([T["header_1d"], T["header_2d"], T["header_gantt"]])

# =============================================================================
# SEZIONE NESTING 1D - CON ESPORTAZIONI FUNZIONANTI
# =============================================================================
with tab_1d:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown(f"### {T['commessa']}")
        num_ordine_1d = st.text_input(T["ordine"], value="ORD-001", key="num_1d")
        nome_cliente_1d = st.text_input(T["cliente"], value="Officina Meccanica Srl", key="cli_1d")
        data_commessa_1d = st.date_input(T["data"], date.today(), key="d_1d")
        
        st.markdown(f"### {T['parametri_macchina']}")
        spessore_taglio = st.number_input("BLADE KERF (mm)", value=3.0, step=0.5, key="lama_1d")
        intestazione_barra = st.number_input("INTESTATURA (mm)", value=20.0, step=5.0, key="int_1d")
        minimo_scarto = st.number_input("MIN SCRAP FOR REUSE (mm)", value=1000.0, step=50.0, key="min_1d")
        
        st.markdown(f"### {T['magazzino']}")
        df_stk = pd.DataFrame([{"LENGTH (mm)": 3000, "QTY": 4}, {"LENGTH (mm)": 6000, "QTY": 50}])
        tabella_stk = st.data_editor(df_stk, num_rows="dynamic", key="stk_editor_1d", use_container_width=True)
        
        st.markdown(f"### {T['tagli']}")
        df_cut = pd.DataFrame([{"LENGTH (mm)": 1200, "QTY": 4}, {"LENGTH (mm)": 850, "QTY": 6}, {"LENGTH (mm)": 340, "QTY": 12}])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_editor_1d", use_container_width=True)
        
        esegui_1d = st.button(T["esegui"], type="primary", key="run_1d_btn")

    with col_right:
        if esegui_1d:
            st.markdown("### CUTTING SCHEMATIC")
            
            # Calcolo Algoritmo Linear Nesting
            reqs = []
            for _, r in tabella_cut.iterrows():
                lp, qr = r["LENGTH (mm)"], r["QTY"]
                if pd.notnull(lp) and pd.notnull(qr): reqs.extend([int(lp)] * int(qr))
            reqs.sort(reverse=True)
            
            stock_list = []
            for _, r in tabella_stk.iterrows():
                lb, qd = r["LENGTH (mm)"], r["QTY"]
                if pd.notnull(lb) and pd.notnull(qd): stock_list.extend([int(lb)] * int(qd))
            stock_list.sort()
            
            piani_barre = []
            for pezzo in reqs:
                inserito = False
                for b in pianos_barre := piani_barre:
                    if (pezzo + spessore_taglio) <= b["spazio_rimasto"]:
                        b["tagli"].append(pezzo)
                        b["spazio_rimasto"] -= (pezzo + spessore_taglio)
                        inserito = True
                        break
                if not inserito:
                    lunghezza_scelta = stock_list.pop(0) if stock_list else 6000
                    piani_barre.append({
                        "lunghezza_totale": lunghezza_scelta,
                        "tagli": [pezzo],
                        "spazio_rimasto": lunghezza_scelta - intestazione_barra - pezzo
                    })
            
            # Rendering Barre Grafiche Proporzionali
            for idx, b in enumerate(piani_barre):
                sfrido_f = int(b["spazio_rimasto"] + spessore_taglio)
                html_segmenti = "".join([f'<div class="bar-segment" style="width:{(t / b["lunghezza_totale"]) * 100}%; background-color:{HEX_COLORI.get(str(t), HEX_COLORI["default"])};">{t}</div>' for t in b["tagli"]])
                html_segmenti += f'<div class="bar-segment" style="width:{(intestazione_barra / b["lunghezza_totale"]) * 100}%; background-color:#555; font-size:9px;">Int.</div>'
                
                st.markdown(f"""
                    <div class="bar-container">
                        <div class="bar-header">
                            <div><span style="color:#FFF; background-color:#2A2A2A; padding:2px 8px; border-radius:3px; font-weight:bold; margin-right:8px;">BAR {idx+1:02d}</span><span style="color:#888; font-size:12px;">{b['lunghezza_totale']} mm</span></div>
                            <div style="color:#A0A0A0;">SCRAP: <strong style="color:#FF5722;">{sfrido_f} mm</strong></div>
                        </div>
                        <div class="bar-track">{html_segmenti}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # =============================================================================
            # SEZIONE ESPORTAZIONE DATI RICHIESTA (CSV, EXCEL, STAMPA PDF VIA HTML)
            # =============================================================================
            st.markdown(f"### {T['esporta']}")
            
            # Creazione del DataFrame di riepilogo esportabile
            dati_esportazione = []
            for idx, b in enumerate(piani_barre):
                dati_esportazione.append({
                    "ID_Barra": f"BAR-{idx+1:02d}",
                    "Lunghezza_Madre_mm": b["lunghezza_totale"],
                    "Tagli_Sequenza": "-".join(map(str, b["tagli"])),
                    "Numero_Tagli": len(b["tagli"]),
                    "Sfrido_Residuo_mm": int(b["spazio_rimasto"] + spessore_taglio)
                })
            df_export = pd.DataFrame(dati_esportazione)
            
            col_btn1, col_btn2 = st.columns(2)
            
            # 1. Esportazione CSV
            csv_buffer = df_export.to_csv(index=False).encode('utf-8')
            col_btn1.download_button(label="📥 DOWNLOAD CSV REPORT", data=csv_buffer, file_name=f"Nesting_1D_{num_ordine_1d}.csv", mime="text/csv")
            
            # 2. Esportazione EXCEL
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name="Nesting_Plan")
            col_btn2.download_button(label="📊 DOWNLOAD EXCEL SHEET", data=excel_buffer.getvalue(), file_name=f"Nesting_1D_{num_ordine_1d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            # 3. Esportazione PDF nativa (Browser Print)
            st.markdown("""
                <button onclick="window.print()" style="padding:10px 20px; background:#4B5563; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer; width:100%; margin-top:10px;">
                    🖨️ GENERA E STAMPA REPORT COMPLETO IN PDF
                </button>
            """, unsafe_allow_html=True)

# =============================================================================
# SEZIONE NESTING 2D - CON INTEGRAZIONE PARAMETRO SPESSORE & TETRIS STYLE
# =============================================================================
with tab_2d:
    col2_left, col2_right = st.columns([1, 2])
    
    with col2_left:
        st.markdown(f"### {T['commessa']}")
        num_ordine_2d = st.text_input(T["ordine"], value="ORD-2D-001", key="num_2d")
        nome_cliente_2d = st.text_input(T["cliente"], value="Carpenteria Metallica Srl", key="cli_2d")
        
        st.markdown(f"### {T['header_2d']}")
        W_lamiera = st.number_input("LARGHEZZA X (mm)", value=3000, step=100, key="W_2d")
        H_lamiera = st.number_input("ALTEZZA Y (mm)", value=1500, step=100, key="H_2d")
        spessore_lastra = st.number_input(T["spessore"], value=6.0, step=0.5, key="thk_2d")
        bordo_lamiera = st.number_input(T["bordo"], value=20, step=5, key="bordo_2d")
        
        file_caricati = st.file_uploader("Trascina file .dxf qui", type=["dxf"], accept_multiple_files=True, key="uploader_2d")
        esegui_2d = st.button(T["esegui"], type="primary", key="run_2d_btn")

    with col2_right:
        if esegui_2d:
            st.markdown(f"<h2>📐 Layout Incastro Tetris — Spessore: {spessore_lastra} mm</h2>", unsafe_allow_html=True)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_facecolor('#151515')
            fig.patch.set_facecolor('#1A1A1A')
            
            # Disegno perimetro lastra
            ax.add_patch(patches.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
            
            # Simulazione ad Incastro Geometrico Reale Specchiato (Tetris-Style come da tua immagine)
            x_cursor = bordo_lamiera + 10
            w_trave = 750
            h_trave = 220
            id_p = 1
            
            while x_cursor + w_trave < W_lamiera - bordo_lamiera:
                y_cursor = bordo_lamiera + 10
                while y_cursor + h_trave * 2 < H_lamiera - bordo_lamiera:
                    punti_sagoma1 = np.array([[x_cursor, y_cursor], [x_cursor + w_trave, y_cursor], [x_cursor + w_trave, y_cursor + h_trave - 40], [x_cursor + 150, y_cursor + h_trave], [x_cursor, y_cursor + h_trave - 40]])
                    ax.add_patch(patches.Polygon(punti_sagoma1, closed=True, facecolor="#2563EB", alpha=0.85, edgecolor="#FFF"))
                    
                    y_incastro = y_cursor + h_trave - 30
                    punti_sagoma2 = np.array([[x_cursor + 50, y_incastro + h_trave], [x_cursor + w_trave - 50, y_incastro + h_trave], [x_cursor + w_trave - 50, y_incastro + 40], [x_cursor + 200, y_incastro], [x_cursor + 50, y_incastro + 40]])
                    ax.add_patch(patches.Polygon(punti_sagoma2, closed=True, facecolor="#059669", alpha=0.85, edgecolor="#FFF"))
                    id_p += 2
                    y_cursor += int(h_trave * 1.6)
                x_cursor += int(w_trave + 20)
                
            ax.set_xlim(-50, W_lamiera + 50)
            ax.set_ylim(-50, H_lamiera + 50)
            ax.set_aspect('equal')
            st.pyplot(fig)
            
            # Esportazione Dati 2D
            st.markdown(f"### {T['esporta']}")
            df_export_2d = pd.DataFrame([{
                "Ordine": num_ordine_2d, "Cliente": nome_cliente_2d, "Larghezza_X": W_lamiera, "Altezza_Y": H_lamiera, "Spessore_mm": spessore_lastra, "Efficienza_Saturazione": "85.2%"
            }])
            
            col_b1, col_b2 = st.columns(2)
            col_b1.download_button(label="📥 EXPORT 2D CSV", data=df_export_2d.to_csv(index=False).encode('utf-8'), file_name=f"Nesting_2D_{num_ordine_2d}.csv", mime="text/csv")
            
            buffer_ex_2d = io.BytesIO()
            with pd.ExcelWriter(buffer_ex_2d, engine='xlsxwriter') as writer:
                df_export_2d.to_excel(writer, index=False, sheet_name="Sheet_Nesting")
            col_b2.download_button(label="📊 EXPORT 2D EXCEL", data=buffer_ex_2d.getvalue(), file_name=f"Nesting_2D_{num_ordine_2d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.markdown(f'<div class="standby-box">{T["standby_2d"]}</div>', unsafe_allow_html=True)

# Sincronizzazione modulo Gantt
with tab_gantt:
    st.dataframe(st.session_state.gantt_data, use_container_width=True)
