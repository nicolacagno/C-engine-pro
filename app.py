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

# 3. INTERFACCIA UTENTE CSS SCURA (Risolti tutti i glitch di stringa)
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
    
    /* Contenitori Barre In-App con riempimento geometrico proporzionale */
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

# MAPPATURA COLORI PALETTE REPLIT
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
# SEZIONE NESTING 1D - CALCOLO E RENDERING PROPORZIONALE
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
        df_stk = pd.DataFrame([
            {"LENGTH (mm)": 3000, "QTY": 4},
            {"LENGTH (mm)": 6000, "QTY": 50}
        ])
        tabella_stk = st.data_editor(df_stk, num_rows="dynamic", key="stk_editor_1d", use_container_width=True)
        
        st.markdown("### ✂️ CUT LIST")
        df_cut = pd.DataFrame([
            {"LENGTH (mm)": 1200, "QTY": 4},
            {"LENGTH (mm)": 850, "QTY": 6},
            {"LENGTH (mm)": 340, "QTY": 12}
        ])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_editor_1d", use_container_width=True)
        
        esegui_1d = st.button("🚀 EXECUTE NESTING", type="primary", key="run_1d_btn")

    with col_right:
        if esegui_1d:
            st.markdown("### CUTTING SCHEMATIC")
            
            # 1. Parsing ed elaborazione pezzi
            reqs = []
            for _, r in tabella_cut.iterrows():
                lp, qr = r["LENGTH (mm)"], r["QTY"]
                if pd.notnull(lp) and pd.notnull(qr):
                    reqs.extend([int(lp)] * int(qr))
            reqs.sort(reverse=True)
            
            # 2. Parsing ed elaborazione magazzino stock
            stock_list = []
            for _, r in tabella_stk.iterrows():
                lb, qd = r["LENGTH (mm)"], r["QTY"]
                if pd.notnull(lb) and pd.notnull(qd):
                    stock_list.extend([int(lb)] * int(qd))
            stock_list.sort() # Priorità alle barre corte per ridurre i residui lunghi
            
            piani_barre = []
            total_req_length = sum(reqs)
            
            # 3. Algoritmo First-Fit Decreasing Lineare
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
            
            # 4. Calcolo metriche globali
            total_stock_used = sum([b["lunghezza_totale"] for b in piani_barre])
            total_scrap = sum([int(b["spazio_rimasto"] + spessore_taglio) for b in piani_barre])
            rendimento = (total_req_length / total_stock_used) * 100 if total_stock_used > 0 else 0
            
            offcuts_rilevati = [int(b["spazio_rimasto"] + spessore_taglio) for b in piani_barre if int(b["spazio_rimasto"] + spessore_taglio) >= minimo_scarto]
            
            # 5. GENERAZIONE SCHEMA VISIVO IN-APP CON METRICHE PROPORZIONALI DI TAGLIO
            for idx, b in enumerate(piani_barre):
                id_barra = idx + 1
                sfrido_f = int(b["spazio_rimasto"] + spessore_taglio)
                is_offcut = sfrido_f >= minimo_scarto
                badge_offcut = '<span class="badge-offcut">♻ offcut</span>' if is_offcut else ''
                
                # Generazione dei singoli blocchetti HTML con larghezza in % reale rispetto alla barra madre
                html_segmenti = ""
                for taglio in b["tagli"]:
                    percentuale_w = (taglio / b["lunghezza_totale"]) * 100
                    colore_bg = HEX_COLORI.get(str(taglio), HEX_COLORI["default"])
                    html_segmenti += f'<div class="bar-segment" style="width:{percentuale_w}%; background-color:{colore_bg};">{taglio}</div>'
                
                # Inclusione dello spazio di intestazione iniziale
                percentuale_int = (intestazione_barra / b["lunghezza_totale"]) * 100
                html_segmenti += f'<div class="bar-segment" style="width:{percentuale_int}%; background-color:#555; font-size:9px;">Int.</div>'
                
                st.markdown(f"""
                    <div class="bar-container">
                        <div class="bar-header">
                            <div>
                                <span style="color:#FFF; background-color:#2A2A2A; padding:2px 8px; border-radius:3px; font-weight:bold; margin-right:8px;">BAR {id_barra:02d}</span>
                                <span style="color:#888; font-size:12px;">{b['lunghezza_totale']} mm</span>
                                <span style="color:#888; margin-left:12px; font-size:12px;">{len(b['tagli'])} tagli</span>
                                {badge_offcut}
                            </div>
                            <div style="color:#A0A0A0;">SCRAP: <strong style="color:{'#ffd700' if is_offcut else '#FF5722'};">{sfrido_f} mm</strong></div>
                        </div>
                        <div class="bar-track">
                            {html_segmenti}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
            # 6. MOTORE DI GENERAZIONE REPORT HTML COSTRUTTIVO (Sostituto di FPDF privo di errori)
            html_report = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Helvetica', Arial, sans-serif; margin: 30px; color: #333; background-color: #fff; }}
                    .header {{ background-color: #1A1A1A; color: white; padding: 20px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }}
                    .title {{ font-size: 22px; font-weight: bold; }}
                    .meta {{ font-size: 12px; color: #A0A0A0; }}
                    .params-box {{ background-color: #F3F4F6; padding: 15px; margin-top: 20px; border-radius: 6px; border: 1px solid #E5E7EB; }}
                    .cards-container {{ display: flex; gap: 15px; margin-top: 20px; }}
                    .card {{ flex: 1; border: 1px solid #E5E7EB; padding: 15px; border-radius: 6px; }}
                    .card-title {{ font-size: 11px; color: #6B7280; font-weight: bold; text-transform: uppercase; }}
                    .card-value {{ font-size: 24px; font-weight: bold; margin-top: 5px; }}
                    .offcut-section {{ margin-top: 25px; }}
                    .offcut-badge {{ display: inline-block; background-color: #FEF3C7; color: #92400E; border: 1px solid #F59E0B; padding: 4px 12px; font-weight: bold; border-radius: 4px; font-size: 13px; margin-right: 8px; }}
                    .schematic-section {{ margin-top: 30px; }}
                    .pdf-bar-row {{ display: flex; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #F3F4F6; }}
                    .pdf-bar-info {{ width: 100px; font-size: 12px; font-weight: bold; }}
                    .pdf-bar-track {{ flex-grow: 1; display: flex; background: #E5E7EB; height: 30px; border-radius: 4px; overflow: hidden; position: relative; }}
                    .pdf-segment {{ display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 11px; height: 100%; border-right: 1px solid rgba(255,255,255,0.3); }}
                    .pdf-scrap-info {{ width: 120px; text-align: right; font-size: 12px; font-weight: bold; padding-left: 10px; }}
                    .legend {{ display: flex; gap: 15px; margin-top: 20px; font-size: 12px; font-weight: bold; }}
                    .legend-item {{ display: flex; align-items: center; gap: 6px; }}
                    @media print {{ .no-print {{ display: none; }} }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="title">MetalHub Suite | <span style="color:#FF5722;">Nesting 1D</span></div>
                    <div class="meta">Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
                </div>
                
                <div class="params-box">
                    <strong>MACHINE PARAMETERS:</strong> Blade Kerf: {spessore_taglio} mm | Intestatura: {intestazione_barra} mm | Ordine: {num_ordine_1d} ({nome_cliente_1d})
                </div>
                
                <div class="cards-container">
                    <div class="card"><div class="card-title">Bars to Pull</div><div class="card-value">{len(piani_barre)} pcs</div></div>
                    <div class="card"><div class="card-title">Efficiency Yield</div><div class="card-value" style="color:#D97706;">{rendimento:.1f}%</div></div>
                    <div class="card"><div class="card-title">Total Scrap</div><div class="card-value">{total_scrap} mm</div></div>
                </div>
                
                <div class="offcut-section">
                    <h4 style="margin-bottom:8px; color:#B45309;">REUSABLE OFFCUTS</h4>
                    {"".join([f'<div class="offcut-badge">{o} mm</div>' for o in offcuts_rilevati]) if offcuts_rilevati else '<span style="color:#888; font-style:italic;">Nessuno scarto riutilizzabile sopra la soglia minima.</span>'}
                </div>
                
                <div class="schematic-section">
                    <h3 style="border-bottom: 2px solid #333; padding-bottom: 5px;">CUTTING SCHEMATIC</h3>
            """
            
            for idx, b in enumerate(piani_barre):
                sfrido_f = int(b["spazio_rimasto"] + spessore_taglio)
                lbl_scarto = "offcut" if sfrido_f >= minimo_scarto else "scrap"
                
                html_report += f"""
                <div class="pdf-bar-row">
                    <div class="pdf-bar-info">BAR {idx+1:02d}<br><span style="color:#888; font-size:10px;">{b['lunghezza_totale']}mm</span></div>
                    <div class="pdf-bar-track">
                """
                for t in b["tagli"]:
                    w_perc = (t / b["lunghezza_totale"]) * 100
                    c_bg = HEX_COLORI.get(str(t), HEX_COLORI["default"])
                    html_report += f'<div class="pdf-segment" style="width:{w_perc}%; background-color:{c_bg};">{t}</div>'
                
                w_int_perc = (intestazione_barra / b["lunghezza_totale"]) * 100
                html_report += f'<div class="pdf-segment" style="width:{w_int_perc}%; background-color:#9CA3AF; font-size:9px;">Int.</div>'
                
                html_report += f"""
                    </div>
                    <div class="pdf-scrap-info">{sfrido_f}mm<br><span style="color:#888; font-size:10px; font-style:italic;">{lbl_scarto}</span></div>
                </div>
                """
                
            html_report += """
                <div class="legend">
                    <div class="legend-item"><div style="width:12px; height:12px; background:#3B82F6;"></div> 1200 mm</div>
                    <div class="legend-item"><div style="width:12px; height:12px; background:#10B981;"></div> 850 mm</div>
                    <div class="legend-item"><div style="width:12px; height:12px; background:#8B5CF6;"></div> 340 mm</div>
                </div>
                <br>
                <button class="no-print" onclick="window.print()" style="padding:10px 20px; background:#FF5722; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer; width:100%;">🖨️ CONFERMA E STAMPA IN PDF PROFESSIONALE</button>
            </body>
            </html>
            """
            
            st.markdown("---")
            st.markdown("### 📄 DOWNLOAD SCHEDA DI TAGLIO")
            st.components.v1.html(html_report, height=500, scrolling=True)

# =============================================================================
# REPARTO NESTING 2D & GANTT (Invariati e stabili)
# =============================================================================
with tab_2d:
    st.markdown('<div class="standby-box">IN ATTESA INPUT DXF<br><br>Carica i file .dxf per sbloccare la mappa bidimensionale.</div>', unsafe_allow_html=True)

with tab_gantt:
    st.dataframe(st.session_state.gantt_data, use_container_width=True)
