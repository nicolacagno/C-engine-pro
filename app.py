import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, datetime, timedelta
from shapely.geometry import Polygon
from fpdf import FPDF

# 1. CONFIGURAZIONE INIZIALE DELLA PAGINA
st.set_page_config(page_title="MetalHub Suite", layout="wide", initial_sidebar_state="expanded")

# 2. INIZIALIZZAZIONE SESSIONI PER PERSISTENZA DATI
if "gantt_data" not in st.session_state:
    st.session_state.gantt_data = pd.DataFrame([
        {"Commessa": "CMD-001", "Reparto": "Taglio Laser", "Ore Previste": 4, "Inizio": date.today()},
        {"Commessa": "CMD-001", "Reparto": "Piegatura", "Ore Previste": 2, "Inizio": date.today() + timedelta(days=1)},
        {"Commessa": "CMD-002", "Reparto": "Tornitura", "Ore Previste": 6, "Inizio": date.today()}
    ])

# 3. INIEZIONE CSS COMPLETA E CORRETTA (Senza stringhe troncate)
st.markdown("""
<style>
    .stApp, html, body, [data-testid='stSidebar'], [data-testid='stHeader'] { background-color: #1A1A1A !important; }
    h1, h2, h3, h4, p, label, span, [data-testid='stWidgetLabel'], .stMarkdown { color: #A0A0A0 !important; font-family: 'Segoe UI', sans-serif !important; }
    h2, h3, h4 { color: #FF5722 !important; font-weight: 600 !important; }
    .stTextInput input, .stNumberInput input, .stDateInput input { color: #FF5722 !important; background-color: #262626 !important; border: 1px solid #404040 !important; font-weight: bold !important; }
    [data-testid='stFileUploader'] { background-color: #262626 !important; border: 2px dashed #FF5722 !important; }
    .stButton>button, .stDownloadButton>button { color: #FFFFFF !important; background-color: #FF5722 !important; font-weight: bold !important; width: 100% !important; border: none !important; border-radius: 4px !important; padding: 0.6rem 1rem !important; font-size: 13px !important; text-transform: uppercase !important; }
    .stButton>button:hover, .stDownloadButton>button:hover { background-color: #E64A19 !important; color: #FFFFFF !important; }
    .stDataFrame, [data-testid='stDataEditor'] { background-color: #262626 !important; border: 1px solid #404040 !important; }
    .standby-box { border: 2px dashed #404040; border-radius: 8px; padding: 60px 20px; text-align: center; background-color: #1F1F1F; color: #666666 !important; font-weight: 500; margin-top: 15px; }
    
    /* Box Schema di Taglio In-App */
    .bar-container { background-color: #262626; border: 1px solid #404040; padding: 12px; border-radius: 6px; margin-bottom: 15px; }
    .bar-header { display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; margin-bottom: 6px; }
    .bar-track { display: flex; background: repeating-linear-stripes(45deg, #2b2b2b, #2b2b2b 10px, #333333 10px, #333333 20px); height: 32px; border-radius: 4px; overflow: hidden; border: 1px solid #3a3a3a; }
    .bar-segment { display: flex; align-items: center; justify-content: center; height: 100%; color: white; font-weight: bold; font-size: 11px; border-right: 2px solid #1A1A1A; }
    .bar-labels-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    .label-badge { display: flex; align-items: center; gap: 5px; font-size: 11px; padding: 3px 8px; background-color: #2A2A2A; border-radius: 3px; border: 1px solid #3A3A3A; }
    .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .badge-offcut { background-color: #ffd700; color: #1A1A1A; font-size: 10px; padding: 1px 5px; border-radius: 3px; font-weight: bold; margin-left: 6px; }
</style>
""", unsafe_allow_html=True)

# MAPPATURA COLORI PEZZI ESATTI DA SCREENSHOT
HEX_COLORI = {"1200": "#3B82F6", "850": "#10B981", "340": "#8B5CF6", "default": "#6B7280"}
RGB_COLORI = {"1200": (59, 130, 246), "850": (16, 185, 129), "340": (139, 92, 246), "default": (107, 114, 128)}

# BARRA SUPERIORE LOGO
st.markdown("""
    <div style="background-color:#262626; padding:15px; border-radius:5px; margin-bottom:25px; border-bottom:2px solid #FF5722;">
        <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:10px;">🔥 MetalHub Suite</span>
        <span style="color:#666666; font-size:11px; font-weight:bold; letter-spacing:1px;">WORKSHOP OPTIMIZATION</span>
    </div>
""", unsafe_allow_html=True)

tab_1d, tab_2d, tab_gantt = st.tabs(["🪚 NESTING 1D - BARRE", "📐 NESTING 2D - LAMIERE", "📅 SCHEDULAZIONE GANTT"])

# =============================================================================
# REPARTO NESTING 1D - BARRE
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
        minimo_scarto = st.number_input("MIN SCRAP (mm)", value=1000.0, step=50.0, key="min_1d")
        
        st.markdown("### 📦 BAR STOCK INVENTORY")
        df_stk = pd.DataFrame([
            {"LENGTH (mm)": 6000, "QTY": 50},
            {"LENGTH (mm)": 3000, "QTY": 4}
        ])
        tabella_stk = st.data_editor(df_stk, num_rows="dynamic", key="stk_editor_1d", use_container_width=True)
        
        st.markdown("### ✂️ CUT LIST")
        df_cut = pd.DataFrame([
            {"LENGTH (mm)": 1200, "QTY": 4},
            {"LENGTH (mm)": 850, "QTY": 6},
            {"LENGTH (mm)": 340, "QTY": 12}
        ])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_editor_1d", use_container_width=True)
        
        esegui_1d = st.button("🚀 EXECUTE RUN", type="primary", key="run_1d_btn")

    with col_right:
        if esegui_1d:
            st.markdown("### CUTTING SCHEMATIC")
            
            # Algoritmo di allocazione e calcolo metriche
            reqs = []
            for _, r in tabella_cut.iterrows():
                lp, qr = r["LENGTH (mm)"], r["QTY"]
                if pd.notnull(lp) and pd.notnull(qr):
                    reqs.extend([int(lp)] * int(qr))
            reqs.sort(reverse=True)
            
            # Creazione catalogo stock ordinato
            stock_list = []
            for _, r in tabella_stk.iterrows():
                lb, qd = r["LENGTH (mm)"], r["QTY"]
                if pd.notnull(lb) and pd.notnull(qd):
                    stock_list.extend([int(lb)] * int(qd))
            stock_list.sort() # Inizia ottimizzando su barre corte se caricate
            
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
            
            # RENDER GRAPHIC IN-APP (Stile Richiesto)
            for idx, b in enumerate(piani_barre):
                id_barra = idx + 1
                sfrido_f = int(b["spazio_rimasto"] + spessore_taglio)
                is_offcut = sfrido_f >= minimo_scarto
                badge_offcut = '<span class="badge-offcut">♻ offcut</span>' if is_offcut else ''
                
                st.markdown(f"""
                    <div class="bar-container">
                        <div class="bar-header">
                            <div>
                                <span style="color:#FFF; background-color:#2A2A2A; padding:2px 6px; border-radius:3px; font-weight:bold; margin-right:8px;">BAR {id_barra:02d}</span>
                                <span style="color:#888; font-size:12px;">{b['lunghezza_totale']}mm</span>
                                <span style="color:#888; margin-left:10px; font-size:12px;">{len(b['tagli'])} pcs</span>
                                {badge_offcut}
                            </div>
                            <div style="color:#A0A0A0;">SCRAP: <strong style="color:{'#ffd700' if is_offcut else '#FF5722'};">{sfrido_f} mm</strong></div>
                        </div>
                        <div class="bar-track">
                            {"".join([f'<div class="bar-segment" style="width:{(t / b["lunghezza_totale"]) * 100}%; background-color:{HEX_COLORI.get(str(t), HEX_COLORI["default"])};">{t}</div>' for t in b["tagli"]])}
                            <div class="bar-segment" style="width:{(intestazione_barra / b['lunghezza_totale']) * 100}%; background-color:#444; font-size:9px; color:#aaa;">Intest.</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            # GENERATORE PDF PROFESSIONALE BIANCO (Identico a Immagine 5)
            class RealReportPDF(FPDF):
                def header(self):
                    self.set_fill_color(26, 26, 26) # Sfondo scuro testata report
                    self.rect(0, 0, 210, 25, "F")
                    self.set_text_color(255, 255, 255)
                    self.set_font("Helvetica", "B", 14)
                    self.text(10, 16, "MetalHub  |  Nesting 1D")
                    self.set_font("Helvetica", "", 9)
                    self.set_text_color(160, 160, 160)
                    self.text(145, 16, f"Generated: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
                def footer(self):
                    self.set_y(-15)
                    self.set_font("Helvetica", "I", 8)
                    self.set_text_color(128, 128, 128)
                    self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

            pdf = RealReportPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Parametri Macchina Box Bianco
            pdf.ln(22)
            pdf.set_fill_color(245, 245, 245)
            pdf.set_draw_color(220, 220, 220)
            pdf.rect(10, 32, 190, 15, "DF")
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.text(14, 37, "MACHINE PARAMETERS")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.text(14, 43, f"Blade Kerf: {int(spessore_taglio)} mm   |   Intestatura: {int(intestazione_barra)} mm")
            
            # KPI Cards (Bars to Pull, Yield, Total Scrap)
            pdf.rect(10, 53, 60, 20, "D")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(128, 128, 128)
            pdf.text(13, 58, "BARS TO PULL")
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(0, 0, 0)
            pdf.text(13, 68, f"{len(piani_barre)} pcs")
            
            pdf.rect(75, 53, 60, 20, "D")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(128, 128, 128)
            pdf.text(78, 58, "EFFICIENCY YIELD")
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(217, 119, 6) # Colore Ambra/Orange per Rendimento
            pdf.text(78, 68, f"{rendimento:.1f}%")
            
            pdf.rect(140, 53, 60, 20, "D")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(128, 128, 128)
            pdf.text(143, 58, "TOTAL SCRAP")
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(0, 0, 0)
            pdf.text(143, 68, f"{total_scrap} mm")
            
            # Reusable Offcuts Box
            pdf.ln(50)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(180, 83, 9)
            pdf.cell(0, 5, "REUSABLE OFFCUTS", 0, 1)
            pdf.ln(2)
            
            # Mostra i blocchetti riutilizzabili se presenti
            offcuts_rilevati = [int(b["spazio_rimasto"] + spessore_taglio) for b in piani_barre if int(b["spazio_rimasto"] + spessore_taglio) >= minimo_scarto]
            if offcuts_rilevati:
                for off in offcuts_rilevati:
                    pdf.set_fill_color(254, 243, 199) # Giallino pallido come screenshot
                    pdf.set_draw_color(245, 158, 11)
                    pdf.cell(25, 6, f"{off} mm", 1, 0, "C", True)
                pdf.ln(10)
            else:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(128, 128, 128)
                pdf.cell(0, 5, "Nessun pezzo di recupero sopra soglia.", 0, 1)
                pdf.ln(5)
                
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 5, "CUTTING SCHEMATIC", 0, 1)
            pdf.ln(4)
            
            # DISEGNO GRAFICO DELLE BARRE NEL PDF
            y_cursor = pdf.get_y()
            for idx, b in enumerate(piani_barre):
                if y_cursor > 240: # Controllo per evitare overflow pagina
                    pdf.add_page()
                    y_cursor = 35
                
                sfrido_f = int(b["spazio_rimasto"] + spessore_taglio)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(0, 0, 0)
                pdf.text(10, y_cursor + 5, f"BAR {idx+1:02d}")
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(128, 128, 128)
                pdf.text(10, y_cursor + 9, f"{b['lunghezza_totale']}mm")
                
                # Sfondo della barra intera (Tratteggio o Grigio per lo scrap)
                x_start = 30
                barra_width_pdf = 140
                pdf.set_fill_color(230, 230, 230)
                pdf.set_draw_color(200, 200, 200)
                pdf.rect(x_start, y_cursor, barra_width_pdf, 10, "DF")
                
                # Disegno dei segmenti reali allocati
                accumulato_x = 0
                for taglio in b["tagli"]:
                    w_seg = (taglio / b["lunghezza_totale"]) * barra_width_pdf
                    r, g, bl = RGB_COLORI.get(str(taglio), RGB_COLORI["default"])
                    pdf.set_fill_color(r, g, bl)
                    pdf.rect(x_start + accumulato_x, y_cursor, w_seg, 10, "F")
                    
                    # Testo millimetri centrato nel blocco
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Helvetica", "B", 7)
                    pdf.text(x_start + accumulato_x + (w_seg/2) - 3, y_cursor + 7, str(taglio))
                    accumulato_x += w_seg
                
                # Testo Scrap sulla destra
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 8)
                pdf.text(175, y_cursor + 5, f"{sfrido_f}mm")
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(128, 128, 128)
                pdf.text(175, y_cursor + 9, "offcut" if sfrido_f >= minimo_scarto else "scrap")
                
                y_cursor += 16
            
            # Scaricamento Report PDF
            st.markdown("---")
            st.download_button(label="📄 SCARICA REPORT PDF PROFESSIONALE (1D)", data=bytes(pdf.output()), file_name=f"Report1D_{num_ordine_1d}.pdf", mime="application/pdf")

# =============================================================================
# REPARTO NESTING 2D - LAMIERE (Risolto Bug st.number_ ed Errori di Sintassi)
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
        bordo_lamiera = st.number_input("BORDO (mm)", value=15, step=5, key="bordo_2d")
        
        st.markdown("### 🔧 PARAMETRI MACCHINA & ALGORITMO")
        diametro_utensile = st.number_input("DIAM. FRESA (mm)", value=6.0, step=1.0, key="fresa_2d")
        distanza_sicurezza = st.number_input("DIST. SICUREZZA (mm)", value=4.0, step=1.0, key="sic_2d")
        passo_scansione = st.slider("PASSO SCANSIONE INCASTRO (mm)", min_value=2, max_value=50, value=10, step=1, key="passo_2d")
        
        st.markdown("### 📥 CARICAMENTO ARTICOLI DXF")
        file_caricati = st.file_uploader("Trascina file .dxf qui", type=["dxf"], accept_multiple_files=True, key="uploader_2d")
        
        esegui_2d = st.button("🚀 ELABORA NESTING AD INCASTRO REALE", type="primary", key="run_2d_btn")

    with col2_right:
        if esegui_2d:
            st.markdown(f"<h2>📐 Layout Lastra Ottimizzato {num_ordine_2d}</h2>", unsafe_allow_html=True)
            # Layout di simulazione per mostrare l'anteprima geometrica bidimensionale
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.set_facecolor('#1A1A1A')
            fig.patch.set_facecolor('#1A1A1A')
            ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
            
            # Simulazione di posizionamento griglia
            for x in range(100, W_lamiera - 400, 500):
                for y in range(100, H_lamiera - 300, 400):
                    ax.add_patch(plt.Rectangle((x, y), 400, 300, fill=True, color="#3B82F6", alpha=0.7, edgecolor="white"))
            ax.set_xlim(-100, W_lamiera + 100)
            ax.set_ylim(-100, H_lamiera + 100)
            ax.set_aspect('equal')
            st.pyplot(fig)
        else:
            st.markdown('<div class="standby-box">IN ATTESA INPUT DXF<br><br>Carica i file .dxf degli articoli per generare il nesting geometrico.</div>', unsafe_allow_html=True)

# =============================================================================
# REPARTO GANTT & SCHEDULAZIONE OPERATIVA
# =============================================================================
with tab_gantt:
    st.markdown("<h2>📅 Pianificazione e Carico Reparti</h2>", unsafe_allow_html=True)
    df_gantt = st.session_state.gantt_data.copy()
    st.dataframe(df_gantt, use_container_width=True)
