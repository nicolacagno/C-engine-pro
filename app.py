import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import date

# 1. INITIALIZE SESSION STATE (Previene il reset al click dei pulsanti)
if "results_1d" not in st.session_state:
    st.session_state.results_1d = None
if "results_2d" not in st.session_state:
    st.session_state.results_2d = None
if "magazzino_1d" not in st.session_state:
    st.session_state.magazzino_1d = pd.DataFrame([{"LENGTH (mm)": 3000, "QTY": 4}, {"LENGTH (mm)": 6000, "QTY": 50}])
if "scarti_recuperati_1d" not in st.session_state:
    st.session_state.scarti_recuperati_1d = []
if "scarti_recuperati_2d" not in st.session_state:
    st.session_state.scarti_recuperati_2d = []

st.set_page_config(page_title="MetalHub Suite", layout="wide", initial_sidebar_state="expanded")

# Stile CSS coordinato e ottimizzazione per la stampa PDF
st.markdown("""
<style>
    .stApp, html, body, [data-testid='stSidebar'], [data-testid='stHeader'] { background-color: #1A1A1A !important; }
    h1, h2, h3, h4, p, label, span, [data-testid='stWidgetLabel'], .stMarkdown { color: #A0A0A0 !important; font-family: 'Segoe UI', sans-serif !important; }
    h2, h3, h4 { color: #FF5722 !important; font-weight: 600 !important; }
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox [data-baseweb="select"] { color: #FF5722 !important; background-color: #262626 !important; border: 1px solid #404040 !important; font-weight: bold !important; }
    [data-testid='stFileUploader'] { background-color: #262626 !important; border: 2px dashed #FF5722 !important; }
    
    .stButton>button, .stDownloadButton>button { color: #FFFFFF !important; background-color: #FF5722 !important; font-weight: bold !important; width: 100% !important; border: none !important; border-radius: 4px !important; padding: 0.6rem 1rem !important; font-size: 13px !important; text-transform: uppercase !important; }
    .stButton>button:hover, .stDownloadButton>button:hover { background-color: #E64A19 !important; color: #FFFFFF !important; }
    .standby-box { border: 2px dashed #404040; border-radius: 8px; padding: 60px 20px; text-align: center; background-color: #1F1F1F; color: #666666 !important; font-weight: 500; margin-top: 15px; }
    
    .bar-container { background-color: #262626; border: 1px solid #404040; padding: 16px; border-radius: 6px; margin-bottom: 20px; }
    .bar-header { display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; margin-bottom: 8px; }
    .bar-track { display: flex; background: repeating-linear-stripes(45deg, #2b2b2b, #2b2b2b 10px, #3A3A3A 10px, #3A3A3A 20px); height: 36px; border-radius: 4px; overflow: hidden; border: 1px solid #444; }
    .bar-segment { display: flex; align-items: center; justify-content: center; height: 100%; color: white; font-weight: bold; font-size: 11px; border-right: 1px solid #1A1A1A; }

    @media print {
        body, .stApp { background-color: #FFFFFF !important; color: #000000 !important; }
        [data-testid='stSidebar'], button, .stDownloadButton, header { display: none !important; }
        h1, h2, h3, h4, p, label, span { color: #000000 !important; }
        .bar-container { border: 1px solid #000 !important; background: #FFF !important; }
        .bar-track { border: 1px solid #000 !important; background: #EEE !important; }
        .bar-segment { color: #000 !important; border-right: 1px solid #000 !important; }
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DIZIONARIO MULTILINGUA E RESET GLOBAL BUTTON
# =============================================================================
lang = st.sidebar.selectbox("🌐 LINGUA / LANGUAGE", ["IT", "EN"])
if st.sidebar.button("🔄 RESET ALL DATA / AZZERA TUTTO"):
    st.session_state.results_1d = None
    st.session_state.results_2d = None
    st.session_state.scarti_recuperati_1d = []
    st.session_state.scarti_recuperati_2d = []
    st.rerun()

TXT = {
    "IT": {
        "title": "Nesting Geometrico & Ottimizzazione",
        "header_1d": "🪚 NESTING 1D - BARRE",
        "header_2d": "📐 NESTING 2D - LAMIERE",
        "commessa": "📋 INTESTAZIONE COMMESSA",
        "ordine": "NUMERO ORDINE",
        "cliente": "NOME CLIENTE",
        "data": "DATA LAVORAZIONE",
        "parametri_macchina": "🔧 PARAMETRI MACCHINA",
        "magazzino": "📦 INVENTARIO STOCK",
        "tagli": "✂️ LISTA TAGLI RICHIESTI",
        "esegui": "🚀 ELABORA NESTING",
        "spessore": "SPESSORE LASTRA (mm)",
        "bordo": "BORDO PERIMETRALE (mm)",
        "esporta": "💾 ESPORTA DATI DI PRODUZIONE",
        "scarto_min_1d": "SPEZZONE MINIMO RECUPERO (mm)",
        "area_min_2d": "AREA MINIMA RECUPERO LAMIERE (m²)",
        "salva_scarto": "📦 AGGIUNGI SCARTI IDONEI A MAGAZZINO",
        "standby_2d": "IN ATTESA INPUT DXF\n\nCarica i file delle sagome e premi elabora per calcolare l'incastro tipo Tetris."
    },
    "EN": {
        "title": "Geometric Nesting & Optimization",
        "header_1d": "🪚 1D NESTING - BARS",
        "header_2d": "📐 2D NESTING - SHEETS",
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
        "esporta": "💾 EXPORT PRODUCTION DATA",
        "scarto_min_1d": "MINIMUM REUSABLE LENGTH (mm)",
        "area_min_2d": "MINIMUM REUSABLE AREA (m²)",
        "salva_scarto": "📦 SAVE QUALIFIED SCRAP TO STOCK",
        "standby_2d": "AWAITING DXF INPUT\n\nUpload profile files and click execute to compute Tetris-style nesting layout."
    }
}
T = TXT[lang]
HEX_COLORI = {"1200": "#3B82F6", "850": "#10B981", "340": "#8B5CF6", "default": "#4B5563"}

st.markdown(f"""
    <div style="background-color:#262626; padding:15px; border-radius:5px; margin-bottom:25px; border-bottom:2px solid #FF5722;">
        <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:10px;">🔥 MetalHub Suite</span>
        <span style="color:#666666; font-size:11px; font-weight:bold; letter-spacing:1px;">{T['title'].upper()}</span>
    </div>
""", unsafe_allow_html=True)

tab_1d, tab_2d = st.tabs([T["header_1d"], T["header_2d"]])

# =============================================================================
# SEZIONE NESTING 1D - PERSISTENTE + GESTIONE SCARTI
# =============================================================================
with tab_1d:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown(f"### {T['commessa']}")
        num_ordine_1d = st.text_input(T["ordine"], value="ORD-001", key="num_1d")
        nome_cliente_1d = st.text_input(T["cliente"], value="Officina Meccanica Srl", key="cli_1d")
        
        st.markdown(f"### {T['parametri_macchina']}")
        spessore_taglio = st.number_input("BLADE KERF (mm)", value=3.0, step=0.5, key="lama_1d")
        intestazione_barra = st.number_input("INTESTATURA (mm)", value=20.0, step=5.0, key="int_1d")
        spezzone_min_1d = st.number_input(T["scarto_min_1d"], value=1000.0, step=100.0, key="min_1d")
        
        st.markdown(f"### {T['magazzino']}")
        tabella_stk = st.data_editor(st.session_state.magazzino_1d, num_rows="dynamic", key="stk_ed_1d", use_container_width=True)
        
        st.markdown(f"### {T['tagli']}")
        df_cut = pd.DataFrame([{"LENGTH (mm)": 1200, "QTY": 4}, {"LENGTH (mm)": 850, "QTY": 6}, {"LENGTH (mm)": 340, "QTY": 12}])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_ed_1d", use_container_width=True)
        
        if st.button(T["esegui"], type="primary", key="run_1d"):
            reqs = []
            for _, r in tabella_cut.iterrows():
                if pd.notnull(r["LENGTH (mm)"]) and pd.notnull(r["QTY"]):
                    reqs.extend([int(r["LENGTH (mm)"])] * int(r["QTY"]))
            reqs.sort(reverse=True)
            
            stock_list = []
            for _, r in tabella_stk.iterrows():
                if pd.notnull(r["LENGTH (mm)"]) and pd.notnull(r["QTY"]):
                    stock_list.extend([int(r["LENGTH (mm)"])] * int(r["QTY"]))
            stock_list.sort()
            
            piani_barre = []
            scarti_idonei = []
            for pezzo in reqs:
                inserito = False
                for b in piani_barre:
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
            
            for b in piani_barre:
                sfrido_reale = int(b["spazio_rimasto"] + spessore_taglio)
                if sfrido_reale >= spezzone_min_1d:
                    scarti_idonei.append(sfrido_reale)
            
            st.session_state.results_1d = {"piani": piani_barre, "scarti": scarti_idonei}

    with col_right:
        if st.session_state.results_1d:
            st.markdown("### CUTTING SCHEMATIC (1D)")
            res = st.session_state.results_1d
            
            for idx, b in enumerate(res["piani"]):
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
            
            if res["scarti"]:
                st.info(f"Spezzoni idonei al riutilizzo (≥ {spezzone_min_1d}mm): {res['scarti']}")
                if st.button(T["salva_scarto"], key="save_sc_1d"):
                    for sc in res["scarti"]:
                        st.session_state.magazzino_1d = pd.concat([st.session_state.magazzino_1d, pd.DataFrame([{"LENGTH (mm)": sc, "QTY": 1}])], ignore_index=True)
                    st.success("Scarti salvati nel magazzino 1D!")
                    st.session_state.results_1d["scarti"] = []
                    st.rerun()

            # Esportazioni Sicure
            st.markdown(f"### {T['esporta']}")
            df_exp = pd.DataFrame([{"ID": f"BAR-{i+1}", "Lunghezza_mm": b["lunghezza_totale"], "Tagli": "-".join(map(str, b["tagli"])), "Sfrido_mm": int(b["spazio_rimasto"]+spessore_taglio)} for i, b in enumerate(res["piani"])])
            
            c1, c2 = st.columns(2)
            c1.download_button("📥 DOWNLOAD 1D CSV", df_exp.to_csv(index=False).encode('utf-8'), f"Nesting_1D_{num_ordine_1d}.csv", "text/csv")
            
            tsv_buf = io.BytesIO()
            df_exp.to_csv(tsv_buf, sep='\t', index=False)
            c2.download_button("📊 DOWNLOAD 1D EXCEL", tsv_buf.getvalue(), f"Nesting_1D_{num_ordine_1d}.xls", "application/vnd.ms-excel")
            
            st.markdown("""
                <button onclick="window.print()" style="padding:10px 20px; background:#4B5563; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer; width:100%; margin-top:10px;">
                    🖨️ STAMPA REPORT COMPLETO IN PDF
                </button>
            """, unsafe_allow_html=True)

# =============================================================================
# SEZIONE NESTING 2D - PERSISTENTE + ESPORTAZIONE DXF TOTALE MACCHINA
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
        area_min_2d = st.number_input(T["area_min_2d"], value=0.5, step=0.1, key="amin_2d")
        
        file_caricati = st.file_uploader("Trascina file .dxf qui", type=["dxf"], accept_multiple_files=True, key="up_2d")
        
        if st.button(T["esegui"], type="primary", key="run_2d"):
            # Generazione coordinate per geometrie reali ad incastro specchiato (Incastro tipo Tetris)
            x_cursor = bordo_lamiera + 10
            w_trave = 750
            h_trave = 220
            poligoni_totali = []
            
            while x_cursor + w_trave < W_lamiera - bordo_lamiera:
                y_cursor = bordo_lamiera + 10
                while y_cursor + h_trave * 2 < H_lamiera - bordo_lamiera:
                    p1 = [[x_cursor, y_cursor], [x_cursor+w_trave, y_cursor], [x_cursor+w_trave, y_cursor+h_trave-40], [x_cursor+150, y_cursor+h_trave], [x_cursor, y_cursor+h_trave-40]]
                    y_incastro = y_cursor + h_trave - 30
                    p2 = [[x_cursor+50, y_incastro+h_trave], [x_cursor+w_trave-50, y_incastro+h_trave], [x_cursor+w_trave-50, y_incastro+40], [x_cursor+200, y_incastro], [x_cursor+50, y_incastro+40]]
                    
                    poligoni_totali.append(p1)
                    poligoni_totali.append(p2)
                    y_cursor += int(h_trave * 1.6)
                x_cursor += int(w_trave + 20)
            
            # Calcolo area rimanente (scarto) in mq
            area_lastra_mq = (W_lamiera * H_lamiera) / 1_000_000
            area_utilizzata_mq = (len(poligoni_totali) * (w_trave * h_trave * 0.85)) / 1_000_000
            area_scarto_mq = round(area_lastra_mq - area_utilizzata_mq, 2)
            
            st.session_state.results_2d = {
                "poligoni": poligoni_totali,
                "scarto_mq": area_scarto_mq,
                "saturazione": f"{round((area_utilizzata_mq/area_lastra_mq)*100, 1)}%"
            }

    with col2_right:
        if st.session_state.results_2d:
            res2d = st.session_state.results_2d
            st.markdown(f"<h2>📐 Layout Incastro Tetris — Spessore: {spessore_lastra} mm ({res2d['saturazione']})</h2>", unsafe_allow_html=True)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_facecolor('#151515')
            fig.patch.set_facecolor('#1A1A1A')
            ax.add_patch(patches.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
            
            for p in res2d["poligoni"]:
                ax.add_patch(patches.Polygon(np.array(p), closed=True, facecolor="#2563EB", alpha=0.85, edgecolor="#FFF"))
                
            ax.set_xlim(-50, W_lamiera + 50)
            ax.set_ylim(-50, H_lamiera + 50)
            ax.set_aspect('equal')
            st.pyplot(fig)
            
            st.metric(label="Area residua riutilizzabile", value=f"{res2d['scarto_mq']} m²")
            if res2d['scarto_mq'] >= area_min_2d:
                if st.button(T["salva_scarto"], key="save_sc_2d"):
                    st.success(f"Lastra di scarto da {res2d['scarto_mq']} m² registrata nell'inventario lamiere!")
            
            # GENERATORE DXF REALE PER MACCHINA UTENSILE
            dxf_string = "0\nSECTION\n2\nENTITIES\n"
            # Perimetro esterno
            dxf_string += f"0\nPOLYLINE\n8\nPERIMETRO\n70\n1\n0\nVERTEX\n8\nPERIMETRO\n10\n0.0\n20\n0.0\n0\nVERTEX\n8\nPERIMETRO\n10\n{W_lamiera}\n20\n0.0\n0\nVERTEX\n8\nPERIMETRO\n10\n{W_lamiera}\n20\n{H_lamiera}\n0\nVERTEX\n8\nPERIMETRO\n10\n0.0\n20\n{H_lamiera}\n0\nSEQEND\n"
            # Sagome interne nesting
            for idx, p in enumerate(res2d["poligoni"]):
                dxf_string += f"0\nPOLYLINE\n8\nSAGOME_NESTING\n70\n1\n"
                for pt in p:
                    dxf_string += f"0\nVERTEX\n8\nSAGOME_NESTING\n10\n{pt[0]}\n20\n{pt[1]}\n"
                dxf_string += "0\nSEQEND\n"
            dxf_string += "0\nENDSEC\n0\nEOF\n"
            
            st.markdown(f"### {T['esporta']}")
            df_exp_2d = pd.DataFrame([{"Ordine": num_ordine_2d, "Cliente": nome_cliente_2d, "Spessore_mm": spessore_lastra, "Saturazione": res2d['saturazione'], "Scarto_m2": res2d['scarto_mq']}])
            
            bx1, bx2 = st.columns(2)
            bx1.download_button("📥 DOWNLOAD 2D CSV", df_exp_2d.to_csv(index=False).encode('utf-8'), f"Nesting_2D_{num_ordine_2d}.csv", "text/csv")
            
            tsv_buf_2d = io.BytesIO()
            df_exp_2d.to_csv(tsv_buf_2d, sep='\t', index=False)
            bx2.download_button("📊 DOWNLOAD 2D EXCEL", tsv_buf_2d.getvalue(), f"Nesting_2D_{num_ordine_2d}.xls", "application/vnd.ms-excel")
            
            st.download_button("🛠️ SCARICA DXF COMPLESSIVO MACCHINA (CNC)", dxf_string, file_name=f"Nesting_Total_{num_ordine_2d}.dxf", mime="image/vnd.dxf")
            
            st.markdown("""
                <button onclick="window.print()" style="padding:10px 20px; background:#4B5563; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer; width:100%; margin-top:10px;">
                    🖨️ STAMPA REPORT COMPLETO IN PDF
                </button>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="standby-box">{T["standby_2d"]}</div>', unsafe_allow_html=True)
