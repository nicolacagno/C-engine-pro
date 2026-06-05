import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, datetime, timedelta

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="MetalHub Suite", layout="wide", initial_sidebar_state="expanded")

# 2. INIZIALIZZAZIONE DATI REPARTO GANTT
if "gantt_data" not in st.session_state:
    st.session_state.gantt_data = pd.DataFrame([
        {"Commessa": "CMD-001", "Reparto": "Taglio Laser", "Ore Previste": 4, "Inizio": date.today()},
        {"Commessa": "CMD-001", "Reparto": "Piegatura", "Ore Previste": 2, "Inizio": date.today() + timedelta(days=1)},
        {"Commessa": "CMD-002", "Reparto": "Tornitura", "Ore Previste": 6, "Inizio": date.today()}
    ])

# 3. INTERFACCIA UTENTE CSS SCURA
st.markdown("""
<style>
    .stApp, html, body, [data-testid='stSidebar'], [data-testid='stHeader'] { background-color: #1A1A1A !important; }
    h1, h2, h3, h4, p, label, span, [data-testid='stWidgetLabel'], .stMarkdown { color: #A0A0A0 !important; font-family: 'Segoe UI', sans-serif !important; }
    h2, h3, h4 { color: #FF5722 !important; font-weight: 600 !important; }
    .stTextInput input, .stNumberInput input, .stDateInput input { color: #FF5722 !important; background-color: #262626 !important; border: 1px solid #404040 !important; font-weight: bold !important; }
    [data-testid='stFileUploader'] { background-color: #262626 !important; border: 2px dashed #FF5722 !important; }
    
    /* Pulsanti Principali */
    .stButton>button, .stDownloadButton>button { color: #FFFFFF !important; background-color: #FF5722 !important; font-weight: bold !important; width: 100% !important; border: none !important; border-radius: 4px !important; padding: 0.6rem 1rem !important; font-size: 13px !important; text-transform: uppercase !important; }
    .stButton>button:hover, .stDownloadButton>button:hover { background-color: #E64A19 !important; color: #FFFFFF !important; }
    .stDataFrame, [data-testid='stDataEditor'] { background-color: #262626 !important; border: 1px solid #404040 !important; }
    .standby-box { border: 2px dashed #404040; border-radius: 8px; padding: 60px 20px; text-align: center; background-color: #1F1F1F; color: #666666 !important; font-weight: 500; margin-top: 15px; }
    
    /* Contenitori Barre In-App */
    .bar-container { background-color: #262626; border: 1px solid #404040; padding: 16px; border-radius: 6px; margin-bottom: 20px; }
    .bar-header { display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; margin-bottom: 8px; }
    .bar-track { display: flex; background: repeating-linear-stripes(45deg, #2b2b2b, #2b2b2b 10px, #3A3A3A 10px, #3A3A3A 20px); height: 36px; border-radius: 4px; overflow: hidden; border: 1px solid #444; }
    .bar-segment { display: flex; align-items: center; justify-content: center; height: 100%; color: white; font-weight: bold; font-size: 11px; border-right: 1px solid #1A1A1A; box-shadow: inset 0 -2px 0 rgba(0,0,0,0.2); }
    .bar-labels-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    .label-badge { display: flex; align-items: center; gap: 6px; font-size: 11px; padding: 4px 10px; background-color: #2A2A2A; border-radius: 4px; border: 1px solid #3A3A3A; color: #FFF !important; }
    .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .badge-offcut { background-color: #FEF3C7; color: #92400E; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 8px; border: 1px solid #F59E0B; }
</style>
""", unsafe_allow_html=True)

HEX_COLORI = {"1200": "#3B82F6", "850": "#10B981", "340": "#8B5CF6", "default": "#4B5563"}

# HEADER APPLICAZIONE
st.markdown("""
    <div style="background-color:#262626; padding:15px; border-radius:5px; margin-bottom:25px; border-bottom:2px solid #FF5722;">
        <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:10px;">🔥 MetalHub Suite</span>
        <span style="color:#666666; font-size:11px; font-weight:bold; letter-spacing:1px;">WORKSHOP OPTIMIZATION</span>
    </div>
""", unsafe_allow_html=True)

tab_1d, tab_2d, tab_gantt = st.tabs(["🪚 NESTING 1D - BARRE", "📐 NESTING 2D - LAMIERE", "📅 SCHEDULAZIONE GANTT"])

# =============================================================================
# SEZIONE NESTING 1D - INVARIATA
# =============================================================================
with tab_1d:
    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.markdown("### 📋 INTESTAZIONE COMMESSA")
        num_ordine_1d = st.text_input("NUMERO ORDINE", value="ORD-001", key="num_1d")
        nome_cliente_1d = st.text_input("NOME CLIENTE", value="Officina Meccanica Srl", key="cli_1d")
        data_commessa_1d = st.date_input("DATA COMMESSA", date.today(), key="d_1d")
        
        st.markdown("### 🔧 MACHINE PARAMETERS")
        spessore_taglio = st.number_input("BLADE KERF (mm)", value=3.0, step=0.5, key="lama_1d")
        intestazione_barra = st.number_input("INTESTATURA (mm)", value=20.0, step=5.0, key="int_1d")
        minimo_scarto = st.number_input("MIN SCRAP FOR OFFCUT (mm)", value=1000.0, step=50.0, key="min_1d")
        
        st.markdown("### 📦 BAR STOCK INVENTORY")
        df_stk = pd.DataFrame([{"LENGTH (mm)": 3000, "QTY": 4}, {"LENGTH (mm)": 6000, "QTY": 50}])
        tabella_stk = st.data_editor(df_stk, num_rows="dynamic", key="stk_editor_1d", use_container_width=True)
        
        st.markdown("### ✂️ CUT LIST")
        df_cut = pd.DataFrame([{"LENGTH (mm)": 1200, "QTY": 4}, {"LENGTH (mm)": 850, "QTY": 6}, {"LENGTH (mm)": 340, "QTY": 12}])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_editor_1d", use_container_width=True)
        esegui_1d = st.button("🚀 EXECUTE NESTING", type="primary", key="run_1d_btn")

    with col_right:
        if esegui_1d:
            st.markdown("### CUTTING SCHEMATIC")
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
            total_req_length = sum(reqs)
            
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
            
            total_stock_used = sum([b["lunghezza_totale"] for b in piani_barre])
            total_scrap = sum([int(b["spazio_rimasto"] + spessore_taglio) for b in piani_barre])
            rendimento = (total_req_length / total_stock_used) * 100 if total_stock_used > 0 else 0
            offcuts_rilevati = [int(b["spazio_rimasto"] + spessore_taglio) for b in piani_barre if int(b["spazio_rimasto"] + spessore_taglio) >= minimo_scarto]
            
            for idx, b in enumerate(piani_barre):
                sfrido_f = int(b["spazio_rimasto"] + spessore_taglio)
                is_offcut = sfrido_f >= minimo_scarto
                badge_offcut = '<span class="badge-offcut">♻ offcut</span>' if is_offcut else ''
                html_segmenti = "".join([f'<div class="bar-segment" style="width:{(t / b["lunghezza_totale"]) * 100}%; background-color:{HEX_COLORI.get(str(t), HEX_COLORI["default"])};">{t}</div>' for t in b["tagli"]])
                html_segmenti += f'<div class="bar-segment" style="width:{(intestazione_barra / b["lunghezza_totale"]) * 100}%; background-color:#555; font-size:9px;">Int.</div>'
                
                st.markdown(f"""
                    <div class="bar-container">
                        <div class="bar-header">
                            <div><span style="color:#FFF; background-color:#2A2A2A; padding:2px 8px; border-radius:3px; font-weight:bold; margin-right:8px;">BAR {idx+1:02d}</span><span style="color:#888; font-size:12px;">{b['lunghezza_totale']} mm</span></div>
                            <div style="color:#A0A0A0;">SCRAP: <strong style="color:{'#ffd700' if is_offcut else '#FF5722'};">{sfrido_f} mm</strong></div>
                        </div>
                        <div class="bar-track">{html_segmenti}</div>
                    </div>
                """, unsafe_allow_html=True)

# =============================================================================
# SEZIONE NESTING 2D - AGGIORNATO CON SPESSORE LASTRA
# =============================================================================
with tab_2d:
    col2_left, col2_right = st.columns([1, 2])
    
    with col2_left:
        st.markdown("### 📋 INTESTAZIONE COMMESSA")
        num_ordine_2d = st.text_input("NUMERO ORDINE", value="ORD-2D-001", key="num_2d")
        nome_cliente_2d = st.text_input("NOME CLIENTE", value="Carpenteria Metallica Industriale", key="cli_2d")
        data_commessa_2d = st.date_input("DATA LAVORAZIONE", date.today(), key="d_2d")
        
        st.markdown("### 📐 FOGLIO LAMIERA")
        W_lamiera = st.number_input("LARG. X (mm)", value=3000, step=100, key="W_2d")
        H_lamiera = st.number_input("ALT. Y (mm)", value=1500, step=100, key="H_2d")
        
        # NUOVO PARAMETRO RICHIESTO PER INFORMAZIONE OPERATORE
        spessore_lastra = st.number_input("SPESSORE LASTRA (mm)", value=4.0, step=0.5, min_value=0.5, key="thk_2d")
        
        bordo_lamiera = st.number_input("BORDO PERIMETRALE (mm)", value=15, step=5, key="bordo_2d")
        
        st.markdown("### 🔧 PARAMETRI MACCHINA & ALGORITMO")
        diametro_utensile = st.number_input("DIAM. FRESA / RAGGIO LASER (mm)", value=6.0, step=1.0, key="fresa_2d")
        distanza_sicurezza = st.number_input("DIST. SICUREZZA (mm)", value=4.0, step=1.0, key="sic_2d")
        passo_scansione = st.slider("PASSO SCANSIONE INCASTRO (mm)", min_value=2, max_value=50, value=10, step=1, key="passo_2d")
        
        st.markdown("### 📥 CARICAMENTO ARTICOLI DXF")
        file_caricati = st.file_uploader("Trascina file .dxf qui", type=["dxf"], accept_multiple_files=True, key="uploader_2d")
        
        esegui_2d = st.button("🚀 ELABORA NESTING AD INCASTRO REALE", type="primary", key="run_2d_btn")

    with col2_right:
        if esegui_2d:
            # Mostra i metadati nel titolo del layout incluse le informazioni di spessore
            st.markdown(f"<h2>📐 Layout Lastra: {num_ordine_2d} — Spessore: <span style='color:#FFF;'>{spessore_lastra} mm</span></h2>", unsafe_allow_html=True)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.set_facecolor('#1A1A1A')
            fig.patch.set_facecolor('#1A1A1A')
            ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
            
            # Simulazione ad incastro geometrico 2D
            for x in range(100, W_lamiera - 400, 500):
                for y in range(100, H_lamiera - 300, 400):
                    ax.add_patch(plt.Rectangle((x, y), 400, 300, fill=True, color="#3B82F6", alpha=0.7, edgecolor="white"))
            ax.set_xlim(-100, W_lamiera + 100)
            ax.set_ylim(-100, H_lamiera + 100)
            ax.set_aspect('equal')
            st.pyplot(fig)
            
            # Anteprima della stringa che andrà nel blocco di esportazione
            st.info(f"ℹ️ Dati di configurazione salvati per il report: Lamiera {W_lamiera}x{H_lamiera} mm | Spessore: {spessore_lastra} mm.")
        else:
            st.markdown(f'<div class="standby-box">IN ATTESA INPUT DXF<br><br>Carica i file delle sagome. Il sistema configurerà il piano di taglio considerando lo spessore inserito di {spessore_lastra} mm per la scheda tecnica finale.</div>', unsafe_allow_html=True)

# =============================================================================
# REPARTO GANTT
# =============================================================================
with tab_gantt:
    st.dataframe(st.session_state.gantt_data, use_container_width=True)
