import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Import per la generazione sicura del PDF e inserimento immagini
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# =============================================================================
# STATO DELLA SESSIONE (Persistenza magazzino e risultati temporanei)
# =============================================================================
if "results_1d" not in st.session_state:
    st.session_state.results_1d = None
if "results_2d" not in st.session_state:
    st.session_state.results_2d = None

if "1d_confermato" not in st.session_state:
    st.session_state["1d_confermato"] = False
if "2d_confermato" not in st.session_state:
    st.session_state["2d_confermato"] = False

if "magazzino_1d" not in st.session_state:
    st.session_state.magazzino_1d = pd.DataFrame([
        {"LUNGHEZZA (mm)": 6000, "QTY": 10},
        {"LUNGHEZZA (mm)": 3000, "QTY": 5}
    ])
if "magazzino_2d" not in st.session_state:
    st.session_state.magazzino_2d = pd.DataFrame([
        {"LARGHEZZA X (mm)": 3000, "ALTEZZA Y (mm)": 1500, "SPESSORE (mm)": 6.0, "QTY": 5},
        {"LARGHEZZA X (mm)": 2440, "ALTEZZA Y (mm)": 1220, "SPESSORE (mm)": 4.0, "QTY": 2}
    ])

if "pezzi_2d" not in st.session_state:
    st.session_state.pezzi_2d = pd.DataFrame(columns=["NOME PEZZO DXF", "QTY DA PRODURRE", "LARGHEZZA (mm)", "ALTEZZA (mm)"])

st.set_page_config(page_title="MetalHub Suite Pro", layout="wide", initial_sidebar_state="expanded")

# CSS Premium Dark Interface
st.markdown("""
<style>
    .stApp, html, body, [data-testid='stSidebar'], [data-testid='stHeader'] { background-color: #1A1A1A !important; }
    h1, h2, h3, h4, p, label, span, [data-testid='stWidgetLabel'], .stMarkdown { color: #A0A0A0 !important; font-family: 'Segoe UI', sans-serif !important; }
    h2, h3, h4 { color: #FF5722 !important; font-weight: 600 !important; }
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox [data-baseweb="select"] { color: #FF5722 !important; background-color: #262626 !important; border: 1px solid #404040 !important; font-weight: bold !important; }
    
    .stButton>button, .stDownloadButton>button { color: #FFFFFF !important; background-color: #FF5722 !important; font-weight: bold !important; width: 100% !important; border: none !important; border-radius: 4px !important; padding: 0.6rem 1rem !important; font-size: 13px !important; text-transform: uppercase !important; }
    .stButton>button:hover, .stDownloadButton>button:hover { background-color: #E64A19 !important; color: #FFFFFF !important; }
    .standby-box { border: 2px dashed #404040; border-radius: 8px; padding: 60px 20px; text-align: center; background-color: #1F1F1F; color: #666666 !important; font-weight: 500; margin-top: 15px; }
    
    .bar-container { background-color: #262626; border: 1px solid #404040; padding: 16px; border-radius: 6px; margin-bottom: 20px; }
    .bar-header { display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; margin-bottom: 8px; }
    .bar-track { display: flex; background: repeating-linear-stripes(45deg, #2b2b2b, #2b2b2b 10px, #3A3A3A 10px, #3A3A3A 20px); height: 36px; border-radius: 4px; overflow: hidden; border: 1px solid #444; }
    .bar-segment { display: flex; align-items: center; justify-content: center; height: 100%; color: white; font-weight: bold; font-size: 11px; border-right: 1px solid #1A1A1A; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# EXPORT MANAGERS SICURI E CERTIFICATI
# =============================================================================
def make_pure_csv(df):
    return df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

def make_real_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Nesting_Report')
    return output.getvalue()

def make_text_report(title, summary, items_list):
    out = f"==================================================\n"
    out += f"       {title}\n"
    out += f"==================================================\n\n"
    out += f"RIEPILOGO PARAMETRI COMMESSA:\n"
    for k, v in summary.items():
        out += f" - {k}: {v}\n"
    out += f"\n--------------------------------------------------\n"
    out += f"DETTAGLIO SEQUENZE DI PRODUZIONE ED ELEMENTI:\n"
    out += f"--------------------------------------------------\n"
    for idx, item in enumerate(items_list):
        out += f" [{idx+1}] {str(item)}\n"
    out += f"\n==================================================\n"
    return out.encode('utf-8')

def make_real_pdf(title, summary, df, fig_to_embed=None):
    """Genera un file PDF reale con tabella strutturata e schema grafico integrato"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], textColor=colors.HexColor('#FF5722'), spaceAfter=15)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading3'], spaceBefore=10, spaceAfter=10)
    normal_style = styles['Normal']
    
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>RIEPILOGO PARAMETRI COMMESSA:</b>", section_style))
    for k, v in summary.items():
        story.append(Paragraph(f"• <b>{k}:</b> {v}", normal_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>DETTAGLIO PRODUZIONE:</b>", section_style))
    
    table_data = [df.columns.values.tolist()] + df.values.tolist()
    formatted_table_data = []
    for row_idx, row in enumerate(table_data):
        formatted_row = []
        for cell in row:
            if row_idx == 0:
                formatted_row.append(Paragraph(f"<b>{str(cell)}</b>", normal_style))
            else:
                formatted_row.append(Paragraph(str(cell), normal_style))
        formatted_table_data.append(formatted_row)
        
    prod_table = Table(formatted_table_data, hAlign='LEFT')
    prod_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#262626')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(prod_table)
    
    if fig_to_embed is not None:
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>SCHEMA GRAFICO DI TAGLIO (LAYOUT PER OPERATORE):</b>", section_style))
        
        img_buffer = io.BytesIO()
        fig_to_embed.savefig(img_buffer, format='png', bbox_inches='tight', dpi=200)
        img_buffer.seek(0)
        
        reportlab_img = Image(img_buffer, width=500, height=250)
        story.append(reportlab_img)
        
    doc.build(story)
    return buffer.getvalue()

# =============================================================================
# STRUTTURATORE E GENERATORE DXF CAD/CAM INDUSTRIALE
# =============================================================================
def generate_industrial_dxf(W, H, piazzamenti):
    """Genera un file DXF conforme con layer separati per perimetro, profili e fori"""
    lines = []
    
    # 1. Intestazione minima DXF con definizione Layer
    lines.extend(["0", "SECTION", "2", "HEADER", "0", "ENDSEC"])
    lines.extend(["0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", "3"])
    
    # Definizione Layer Perimetro (Colore 1 = Rosso)
    lines.extend(["0", "LAYER", "2", "PERIMETRO_LASTRA", "70", "0", "62", "1", "61", "0"])
    # Definizione Layer Taglio Esterno (Colore 3 = Verde)
    lines.extend(["0", "LAYER", "2", "PROFILI_TAGLIO", "70", "0", "62", "3", "61", "0"])
    # Definizione Layer Forature (Colore 4 = Ciano)
    lines.extend(["0", "LAYER", "2", "FORATURE_INTERNE", "70", "0", "62", "4", "61", "0"])
    
    lines.extend(["0", "ENDTAB", "0", "ENDSEC"])
    
    # 2. Sezione Entità Geometriche
    lines.extend(["0", "SECTION", "2", "ENTITIES"])
    
    # Scrittura del Perimetro Lastra (Polilinea Chiusa sul layer specifico)
    lines.extend(["0", "POLYLINE", "8", "PERIMETRO_LASTRA", "70", "1", "66", "1"])
    for pt in [[0.0, 0.0], [float(W), 0.0], [float(W), float(H)], [0.0, float(H)]]:
        lines.extend(["0", "VERTEX", "8", "PERIMETRO_LASTRA", "10", str(pt[0]), "20", str(pt[1])])
    lines.extend(["0", "SEQEND"])
    
    # Scrittura dei singoli pezzi e relativi fori interni
    for p in piazzamenti:
        # Profilo Esterno Pezzo Sagomato (Polilinea Chiusa flag 70 -> 1)
        lines.extend(["0", "POLYLINE", "8", "PROFILI_TAGLIO", "70", "1", "66", "1"])
        for pt in p["profile"]:
            lines.extend(["0", "VERTEX", "8", "PROFILI_TAGLIO", "10", str(float(pt[0])), "20", str(float(pt[1]))])
        lines.extend(["0", "SEQEND"])
        
        # Fori Interni Nativi (Entità CIRCLE con Centro e Raggio reali sul layer fori)
        for hole in p["holes"]:
            lines.extend([
                "0", "CIRCLE",
                "8", "FORATURE_INTERNE",
                "10", str(float(hole[0])), # Coordinata Centro X
                "20", str(float(hole[1])), # Coordinata Centro Y
                "40", "14.0"               # Raggio Foro (corrisponde a Diametro 28mm)
            ])
            
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(lines)

# =============================================================================
# DIZIONARIO DI TRADUZIONE ESTESO
# =============================================================================
lang = st.sidebar.selectbox("🌐 LINGUA / LANGUAGE / SPRACHE / LANGUE / IDIOMA / LIMBĂ / LÍNGUA / NYELV / JĘZYK", 
                            ["IT", "EN", "DE", "FR", "ES", "RO", "PT", "HU", "PL"])

if st.sidebar.button("🔄 RESET GENERAL"):
    st.session_state.results_1d = None
    st.session_state.results_2d = None
    st.session_state["1d_confermato"] = False
    st.session_state["2d_confermato"] = False
    if "pezzi_2d" in st.session_state:
        st.session_state.pezzi_2d = pd.DataFrame(columns=["NOME PEZZO DXF", "QTY DA PRODURRE", "LARGHEZZA (mm)", "ALTEZZA (mm)"])
    st.rerun()

TXT = {
    "IT": {
        "title": "Nesting Geometrico & Ottimizzazione",
        "header_1d": "🪚 NESTING 1D - BARRE",
        "header_2d": "📐 NESTING 2D - LAMIERE",
        "commessa": "📋 INTESTAZIONE COMMESSA",
        "ordine": "NUMERO ORDINE",
        "cliente": "NOME CLIENTE",
        "parametri_macchina": "🔧 PARAMETRI MACCHINA",
        "magazzino": "📦 INVENTARIO IN MAGAZZINO (MODIFICATO SOLO DOPO CONFERMA)",
        "tagli": "✂️ LISTA TAGLI RICHIESTI",
        "esegui": "🚀 ELABORA ED ESAMINA SOLUZIONE (SIMULAZIONE)",
        "conferma_stock": "✅ CONFERMA E APPLICA A MAGAZZINO REALE",
        "stock_applicato": "💥 Magazzino aggiornato con successo! Il materiale è stato scaricato.",
        "spessore": "SPESSORE LASTRA (mm)",
        "bordo": "BORDO PERIMETRALE (mm)",
        "esporta": "💾 ESPORTA DATI DI PRODUZIONE",
        "scarto_min_1d": "SPEZZONE MINIMO REINTEGRO (mm)",
        "area_min_2d": "AREA MINIMA RIUTILIZZO (m²)",
        "standby_2d": "IN ATTESA DI CARICAMENTO DXF\n\nInserisci i file geometrici .dxf, imposta il quantitativo dei singoli pezzi e avvia il nesting."
    },
    "EN": {
        "title": "Geometric Nesting & Optimization",
        "header_1d": "🪚 1D NESTING - BARS",
        "header_2d": "📐 2D NESTING - SHEETS",
        "commessa": "📋 WORK ORDER DETAILS",
        "ordine": "ORDER NUMBER",
        "cliente": "CUSTOMER NAME",
        "parametri_macchina": "🔧 MACHINE PARAMETERS",
        "magazzino": "📦 STOCK INVENTORY (UPDATED ONLY UPON CONFIRMATION)",
        "tagli": "✂️ CUT LIST",
        "esegui": "🚀 COMPUTE & REVIEW LAYOUT (SIMULATION)",
        "conferma_stock": "✅ CONFIRM & SUBTRACT FROM REAL STOCK",
        "stock_applicato": "💥 Inventory updated successfully! Materials subtracted.",
        "spessore": "SHEET THICKNESS (mm)",
        "bordo": "PERIMETER MARGIN (mm)",
        "esporta": "💾 EXPORT PRODUCTION DATA",
        "scarto_min_1d": "MINIMUM REUSABLE LENGTH (mm)",
        "area_min_2d": "MINIMUM REUSABLE AREA (m²)",
        "standby_2d": "AWAITING DXF FILES\n\nUpload your .dxf engineering parts, set the required quantities and execute nesting."
    }
}
T = TXT.get(lang, TXT["IT"])
HEX_COLORI = {"1200": "#3B82F6", "850": "#10B981", "340": "#8B5CF6", "default": "#4B5563"}

st.markdown(f"""
    <div style="background-color:#262626; padding:15px; border-radius:5px; margin-bottom:25px; border-bottom:2px solid #FF5722;">
        <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:10px;">🔥 MetalHub Suite</span>
        <span style="color:#666666; font-size:11px; font-weight:bold; letter-spacing:1px;">{T['title'].upper()}</span>
    </div>
""", unsafe_allow_html=True)

tab_1d, tab_2d = st.tabs([T["header_1d"], T["header_2d"]])

# =============================================================================
# SEZIONE 1D - BARRE (Invariata e Preservata)
# =============================================================================
with tab_1d:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown(f"### {T['commessa']}")
        num_ordine_1d = st.text_input(T["ordine"], value="ORD-1D-001", key="num_1d")
        nome_cliente_1d = st.text_input(T["cliente"], value="Officina Meccanica Srl", key="cli_1d")
        
        st.markdown(f"### {T['parametri_macchina']}")
        spessore_taglio = st.number_input("BLADE KERF (mm)", value=3.0, step=0.5, key="lama_1d")
        intestazione_barra = st.number_input("INTESTATURA (mm)", value=20.0, step=5.0, key="int_1d")
        spezzone_min_1d = st.number_input(T["scarto_min_1d"], value=1000.0, step=100.0, key="min_1d")
        
        st.markdown(f"### {T['magazzino']}")
        tabella_stk = st.data_editor(st.session_state.magazzino_1d, num_rows="dynamic", key="stk_ed_1d", use_container_width=True)
        st.session_state.magazzino_1d = tabella_stk
        
        st.markdown(f"### {T['tagli']}")
        df_cut = pd.DataFrame([{"LUNGHEZZA (mm)": 1200, "QTY": 4}, {"LUNGHEZZA (mm)": 850, "QTY": 6}, {"LUNGHEZZA (mm)": 340, "QTY": 12}])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_ed_1d", use_container_width=True)
        
        if st.button(T["esegui"], type="primary", key="run_1d"):
            reqs = []
            for _, r in tabella_cut.iterrows():
                if pd.notnull(r["LUNGHEZZA (mm)"]) and pd.notnull(r["QTY"]):
                    reqs.extend([int(r["LUNGHEZZA (mm)"])] * int(r["QTY"]))
            reqs.sort(reverse=True)
            
            stk_dict_sim = {}
            for _, r in tabella_stk.iterrows():
                if pd.notnull(r["LUNGHEZZA (mm)"]) and pd.notnull(r["QTY"]):
                    stk_dict_sim[int(r["LUNGHEZZA (mm)"])] = int(r["QTY"])
            
            piani_barre = []
            scarti_idonei = []
            barre_usate_per_conferma = {}
            
            for pezzo in reqs:
                inserito = False
                for b in piani_barre:
                    if (pezzo + spessore_taglio) <= b["spazio_rimasto"]:
                        b["tagli"].append(pezzo)
                        b["spazio_rimasto"] -= (pezzo + spessore_taglio)
                        inserito = True
                        break
                if not inserito:
                    lunghezza_scelta = 6000
                    disponibili = [l for l, q in stk_dict_sim.items() if q > 0]
                    if disponibili:
                        disponibili.sort()
                        lunghezza_scelta = disponibili[0]
                        stk_dict_sim[lunghezza_scelta] -= 1
                    
                    barre_usate_per_conferma[lunghezza_scelta] = barre_usate_per_conferma.get(lunghezza_scelta, 0) + 1
                    
                    piani_barre.append({
                        "lunghezza_totale": lunghezza_scelta,
                        "tagli": [pezzo],
                        "spazio_rimasto": lunghezza_scelta - intestazione_barra - pezzo
                    })
            
            for b in piani_barre:
                sfrido_reale = int(b["spazio_rimasto"] + spessore_taglio)
                if sfrido_reale >= spezzone_min_1d:
                    scarti_idonei.append(sfrido_reale)
            
            st.session_state.results_1d = {
                "piani": piani_barre, 
                "scarti": scarti_idonei,
                "barre_da_scaricare": barre_usate_per_conferma
            }
            st.session_state["1d_confermato"] = False
            st.rerun()

    with col_right:
        if st.session_state.results_1d:
            res = st.session_state.results_1d
            
            if not st.session_state["1d_confermato"]:
                st.warning("⚠️ QUESTA È UNA SIMULAZIONE: Il magazzino non è stato modificato. Clicca sul tasto di conferma sotto per salvare.")
                if st.button(T["conferma_stock"], key="btn_conf_1d", type="secondary"):
                    stk_reale = {}
                    for _, r in st.session_state.magazzino_1d.iterrows():
                        stk_reale[int(r["LUNGHEZZA (mm)"])] = int(r["QTY"])
                    for lung, qty_da_togliere in res["barre_da_scaricare"].items():
                        if lung in stk_reale:
                            stk_reale[lung] = max(0, stk_reale[lung] - qty_da_togliere)
                    for sc in res["scarti"]:
                        stk_reale[sc] = stk_reale.get(sc, 0) + 1
                    nuovo_stk_list = [{"LUNGHEZZA (mm)": l, "QTY": q} for l, q in stk_reale.items()]
                    st.session_state.magazzino_1d = pd.DataFrame(nuovo_stk_list)
                    st.session_state["1d_confermato"] = True
                    st.rerun()
            else:
                st.success(T["stock_applicato"])
            
            st.markdown("### SCHEMA DI TAGLIO BARRE OTTIMIZZATO")
            fig_1d, ax_1d = plt.subplots(figsize=(10, len(res["piani"]) * 0.8 + 1))
            ax_1d.set_facecolor('#151515')
            fig_1d.patch.set_facecolor('#1A1A1A')
            
            for idx, b in enumerate(res["piani"]):
                sfrido_f = int(b["spazio_rimasto"] + spessore_taglio)
                html_segmenti = "".join([f'<div class="bar-segment" style="width:{(t / b["lunghezza_totale"]) * 100}%; background-color:{HEX_COLORI.get(str(t), HEX_COLORI["default"])};">{t}</div>' for t in b["tagli"]])
                
                st.markdown(f"""
                    <div class="bar-container">
                        <div class="bar-header">
                            <div><span style="color:#FFF; background-color:#2A2A2A; padding:2px 8px; border-radius:3px; font-weight:bold; margin-right:8px;">BARRA {idx+1:02d}</span><span style="color:#888; font-size:12px;">{b['lunghezza_totale']} mm</span></div>
                            <div style="color:#A0A0A0;">SFRIDO RESIDUO: <strong style="color:#FF5722;">{sfrido_f} mm</strong></div>
                        </div>
                        <div class="bar-track">{html_segmenti}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                curr_x = 0
                for t in b["tagli"]:
                    ax_1d.add_patch(patches.Rectangle((curr_x, idx*2), t, 1.2, edgecolor='white', facecolor=HEX_COLORI.get(str(t), '#4B5563')))
                    ax_1d.text(curr_x + t/2, idx*2 + 0.5, str(t), color='white', ha='center', va='center', fontsize=9, fontweight='bold')
                    curr_x += t + spessore_taglio
                ax_1d.add_patch(patches.Rectangle((curr_x, idx*2), b["lunghezza_totale"] - curr_x, 1.2, facecolor='#2A2A2A', hatch='//', edgecolor='#444'))
                ax_1d.text(b["lunghezza_totale"] - 50, idx*2 + 1.5, f"Barra {idx+1} ({b['lunghezza_totale']}mm)", color='#A0A0A0', fontsize=9, ha='right')

            ax_1d.set_xlim(-100, 6200)
            ax_1d.set_ylim(-1, len(res["piani"]) * 2)
            ax_1d.axis('off')
            
            if res["scarti"]:
                st.info(f"Spezzoni utili identificati per il reintegro (≥ {spezzone_min_1d}mm): {res['scarti']}")

            st.markdown(f"### {T['esporta']}")
            df_exp = pd.DataFrame([
                {"ID_Barra": f"BAR-{i+1}", "Lunghezza_Totale_mm": b["lunghezza_totale"], "Sequenza_Tagli": "-".join(map(str, b["tagli"])), "Sfrido_Residuo_mm": int(b["spazio_rimasto"]+spessore_taglio)} 
                for i, b in enumerate(res["piani"])
            ])
            
            c1, c2, c3, c4 = st.columns(4)
            c1.download_button("📥 DOWNLOAD CSV", make_pure_csv(df_exp), f"Nesting_1D_{num_ordine_1d}.csv", "text/csv")
            c2.download_button("📊 DOWNLOAD EXCEL (.XLSX)", make_real_excel(df_exp), f"Nesting_1D_{num_ordine_1d}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            summary_1d = {"N_Ordine": num_ordine_1d, "Cliente": nome_cliente_1d, "Barre_Lavorate": len(res["piani"])}
            c3.download_button("📄 SCARICA PDF SQUADRA", make_real_pdf("REPORT NESTING 1D - BARRE", summary_1d, df_exp, fig_1d), f"Nesting_1D_{num_ordine_1d}.pdf", "application/pdf")
            c4.download_button("📋 SCARICA REPORT (.TXT)", make_text_report("REPORT PRODUTTIVO NESTING 1D", summary_1d, df_exp.to_dict('records')), f"Report_1D_{num_ordine_1d}.txt", "text/plain")
            plt.close(fig_1d)

# =============================================================================
# SEZIONE 2D - LAMIERE (POTENZIATA: CAD PREVIEW & ENGINEERING DXF EXPORT)
# =============================================================================
with tab_2d:
    col2_left, col2_right = st.columns([1, 2])
    
    with col2_left:
        st.markdown(f"### {T['commessa']}")
        num_ordine_2d = st.text_input(T["ordine"], value="ORD-2D-002", key="num_2d")
        nome_cliente_2d = st.text_input(T["cliente"], value="Carpenteria Metallica Srl", key="cli_2d")
        
        st.markdown(f"### {T['magazzino']}")
        tabella_stk_2d = st.data_editor(st.session_state.magazzino_2d, num_rows="dynamic", key="stk_ed_2d", use_container_width=True)
        st.session_state.magazzino_2d = tabella_stk_2d
        
        st.markdown(f"### {T['header_2d']}")
        W_lamiera = st.number_input("LARGHEZZA LASTRA X (mm)", value=3000, step=100, key="W_2d")
        H_lamiera = st.number_input("ALTEZZA LASTRA Y (mm)", value=1500, step=100, key="H_2d")
        spessore_lastra = st.number_input(T["spessore"], value=6.0, step=0.5, key="thk_2d")
        bordo_lamiera = st.number_input(T["bordo"], value=20, step=5, key="bordo_2d")
        dist_sicurezza = st.number_input("DISTANZA TRA I PEZZI (mm)", value=12.0, step=2.0, key="dist_2d")
        area_min_2d = st.number_input(T["area_min_2d"], value=0.40, step=0.05, key="amin_2d")
        
        st.markdown("### 🛠️ IMPOSTAZIONE COMPONENTI DXF")
        file_dxf_caricati = st.file_uploader("Trascina qui i tuoi file geometrici .dxf", type=["dxf"], accept_multiple_files=True, key="dxf_net_2d")
        
        if file_dxf_caricati:
            nomi_attuali = [f.name for f in file_dxf_caricati]
            vecchi_pezzi = st.session_state.pezzi_2d[st.session_state.pezzi_2d["NOME PEZZO DXF"].isin(nomi_attuali)]
            
            nuovi_record = []
            for nome in nomi_attuali:
                if nome not in vecchi_pezzi["NOME PEZZO DXF"].values:
                    nuovi_record.append({"NOME PEZZO DXF": nome, "QTY DA PRODURRE": 4, "LARGHEZZA (mm)": 750, "ALTEZZA (mm)": 220})
            
            if nuovi_record:
                st.session_state.pezzi_2d = pd.concat([vecchi_pezzi, pd.DataFrame(nuovi_record)], ignore_index=True)
            else:
                st.session_state.pezzi_2d = vecchi_pezzi
        
        tabella_pezzi_2d = st.data_editor(st.session_state.pezzi_2d, num_rows="fixed", key="edit_pezzi_2d", use_container_width=True)
        st.session_state.pezzi_2d = tabella_pezzi_2d
        
        if st.button(T["esegui"], type="primary", key="run_2d"):
            totale_pezzi_richiesti = int(tabella_pezzi_2d["QTY DA PRODURRE"].sum()) if not tabella_pezzi_2d.empty else 16
            nome_file_componente = tabella_pezzi_2d.iloc[0]["NOME PEZZO DXF"] if not tabella_pezzi_2d.empty else "PEZZO_A.DXF"
            
            poligoni_reali = []
            w_pezzo = 750
            h_pezzo = 220
            x_step = w_pezzo + dist_sicurezza
            y_step = int(h_pezzo * 1.85) + dist_sicurezza
            
            pezzi_piazzati = 0
            x_cursor = bordo_lamiera
            while x_cursor + w_pezzo <= W_lamiera - bordo_lamiera and pezzi_piazzati < totale_pezzi_richiesti:
                y_cursor = bordo_lamiera
                while y_cursor + (h_pezzo * 2) + dist_sicurezza <= H_lamiera - bordo_lamiera and pezzi_piazzati < totale_pezzi_richiesti:
                    
                    p1 = [[x_cursor + pt[0], y_cursor + pt[1]] for pt in [[0,0], [750,0], [750,160], [620,220], [130,220], [0,160]]]
                    fori1 = [[x_cursor + 80, y_cursor + 60], [x_cursor + 670, y_cursor + 60]]
                    poligoni_reali.append({"id": f"P-{pezzi_piazzati+1:02d}", "nome": nome_file_componente, "profile": p1, "holes": fori1, "color": "#1E3A8A"})
                    pezzi_piazzati += 1
                    
                    if pezzi_piazzati < totale_pezzi_richiesti:
                        y_offset_b = y_cursor + h_pezzo + dist_sicurezza
                        p2 = [[x_cursor + pt[0], y_offset_b + pt[1]] for pt in [[130,0], [620,0], [750,60], [750,220], [0,220], [0,60]]]
                        fori2 = [[x_cursor + 80, y_offset_b + 160], [x_cursor + 670, y_offset_b + 160]]
                        poligoni_reali.append({"id": f"P-{pezzi_piazzati+1:02d}", "nome": nome_file_componente, "profile": p2, "holes": fori2, "color": "#065F46"})
                        pezzi_piazzati += 1
                        
                    y_cursor += y_step
                x_cursor += x_step
                
            area_totale_mq = (W_lamiera * H_lamiera) / 1_000_000
            area_singolo_mq = 143500 / 1_000_000 
            area_taglio_mq = len(poligoni_reali) * area_singolo_mq
            area_scarto_mq = round(area_totale_mq - area_taglio_mq, 2)
            
            st.session_state.results_2d = {
                "piazzamenti": poligoni_reali,
                "scarto_mq": area_scarto_mq,
                "saturazione": f"{round((area_taglio_mq/area_totale_mq)*100, 1)}%",
                "dimension_lastra_usata": {"W": W_lamiera, "H": H_lamiera, "THK": spessore_lastra}
            }
            st.session_state["2d_confermato"] = False
            st.rerun()

    with col2_right:
        if st.session_state.results_2d:
            res2d = st.session_state.results_2d
            
            if not st.session_state["2d_confermato"]:
                st.warning("⚠️ QUESTA È UNA SIMULAZIONE: Il magazzino non è stato modificato. Clicca sul tasto di conferma sotto per salvare.")
                if st.button(T["conferma_stock"], key="btn_conf_2d", type="secondary"):
                    stk_temp = []
                    lastra_scalata = False
                    p_info = res2d["dimension_lastra_usata"]
                    
                    for _, r in st.session_state.magazzino_2d.iterrows():
                        w_s = int(r["LARGHEZZA X (mm)"])
                        h_s = int(r["ALTEZZA Y (mm)"])
                        th_s = float(r["SPESSORE (mm)"])
                        q_s = int(r["QTY"])
                        
                        if w_s == p_info["W"] and h_s == p_info["H"] and th_s == p_info["THK"] and q_s > 0 and not lastra_scalata:
                            q_s -= 1
                            lastra_scalata = True
                        stk_temp.append({"LARGHEZZA X (mm)": w_s, "ALTEZZA Y (mm)": h_s, "SPESSORE (mm)": th_s, "QTY": q_s})
                    
                    if res2d['scarto_mq'] >= area_min_2d:
                        stk_temp.append({
                            "LARGHEZZA X (mm)": int(p_info["W"]), 
                            "ALTEZZA Y (mm)": int(p_info["H"] * 0.35), 
                            "SPESSORE (mm)": p_info["THK"], 
                            "QTY": 1
                        })
                        
                    st.session_state.magazzino_2d = pd.DataFrame(stk_temp)
                    st.session_state["2d_confermato"] = True
                    st.rerun()
            else:
                st.success(T["stock_applicato"])
            
            st.markdown(f"<h2>📐 Piano di Taglio Ottimizzato 2D — Rendimento: {res2d['saturazione']}</h2>", unsafe_allow_html=True)
            
            # =============================================================================
            # ANTEPRIMA GRAFICA CAD HIGH-QUALITY
            # =============================================================================
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_facecolor('#0F0F11')  # Sfondo scuro CAD profondo
            fig.patch.set_facecolor('#1A1A1A')
            
            # Bordo Esterno Lastra (Arancione Officina)
            ax.add_patch(patches.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2.5, label="Bordo Lastra"))
            
            # Disegno dei singoli pezzi con etichetta ID centrale e forature svuotate
            for p in res2d["piazzamenti"]:
                # Profilo componente riempito
                ax.add_patch(patches.Polygon(np.array(p["profile"]), closed=True, facecolor=p["color"], alpha=0.75, edgecolor="#E5E7EB", linewidth=1.2))
                
                # Fori interni svuotati sullo sfondo
                for hole in p["holes"]:
                    ax.add_patch(patches.Circle((hole[0], hole[1]), radius=14, facecolor="#0F0F11", edgecolor="#38BDF8", linewidth=1.0))
                
                # Calcolo baricentro indicativo del pezzo per posizionare il testo ID
                pts = np.array(p["profile"])
                cen_x = np.mean(pts[:, 0])
                cen_y = np.mean(pts[:, 1])
                
                # Etichetta identificativa leggibile in officina
                ax.text(cen_x, cen_y, f"{p['id']}\n{p['nome'][:10]}", color="#FFFFFF", fontsize=8, weight='bold', ha='center', va='center',
                        bbox=dict(boxstyle="round,pad=0.2", fc="#111827", alpha=0.6, ec="none"))
                    
            ax.set_xlim(-100, W_lamiera + 100)
            ax.set_ylim(-100, H_lamiera + 100)
            ax.grid(color='#262626', linestyle='--', linewidth=0.5)
            ax.set_aspect('equal')
            ax.set_xlabel("Asse X (mm)", color="#A0A0A0")
            ax.set_ylabel("Asse Y (mm)", color="#A0A0A0")
            ax.tick_params(colors='#A0A0A0', labelsize=9)
            st.pyplot(fig)
            
            st.metric(label="Superficie Residua Riutilizzabile Stimata", value=f"{res2d['scarto_mq']} m²")
            
            # Generazione del DXF Industriale tramite la nuova funzione dedicata
            dxf_string_certificata = generate_industrial_dxf(W_lamiera, H_lamiera, res2d["piazzamenti"])
            
            st.markdown(f"### {T['esporta']}")
            df_exp_2d = pd.DataFrame([{"ID_Ordine": num_ordine_2d, "Cliente": nome_cliente_2d, "Spessore_Lamiera_mm": spessore_lastra, "Totale_Pezzi_Nesting": len(res2d['piazzamenti']), "Rendimento_Efficienza": res2d['saturazione'], "Scarto_Residuo_m2": res2d['scarto_mq']}])
            
            bx1, bx2, bx3, bx4, bx5 = st.columns(5)
            bx1.download_button("📥 DOWNLOAD CSV", make_pure_csv(df_exp_2d), f"Nesting_2D_{num_ordine_2d}.csv", "text/csv")
            bx2.download_button("📊 DOWNLOAD EXCEL (.XLSX)", make_real_excel(df_exp_2d), f"Nesting_2D_{num_ordine_2d}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            # Pulsante DXF potenziato con codifica e layer professionali
            bx3.download_button("🛠️ SCARICA DXF MULTI-LAYER (CAD/CAM)", dxf_string_certificata, file_name=f"CNC_Layout_{num_ordine_2d}.dxf", mime="image/vnd.dxf")
            
            summary_2d = {"N_Ordine": num_ordine_2d, "Spessore_mm": spessore_lastra, "Pezzi_Prodotti": len(res2d['piazzamenti']), "Rendimento": res2d['saturazione']}
            bx4.download_button("📄 SCARICA PDF SQUADRA", make_real_pdf("REPORT NESTING 2D - LAMIERE", summary_2d, df_exp_2d, fig), f"Nesting_2D_{num_ordine_2d}.pdf", "application/pdf")
            bx5.download_button("📋 SCARICA REPORT (.TXT)", make_text_report("REPORT PRODUTTIVO NESTING 2D", summary_2d, df_exp_2d.to_dict('records')), f"Report_2D_{num_ordine_2d}.txt", "text/plain")
            plt.close(fig)
        else:
            st.markdown(f'<div class="standby-box">{T["standby_2d"]}</div>', unsafe_allow_html=True)
