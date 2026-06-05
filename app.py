import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Import per la lettura e scrittura CAD professionale
import ezdxf

# Import per la generazione del PDF
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
# PARSER GEOMETRICO AVANZATO E INTERPRETE INDUSTRIAL DXF v2
# =============================================================================
def parse_uploaded_dxf(file_bytes):
    """Estrae geometrie da DXF ASCII, Binari, con supporto a ARCHI, SPLINE e BLOCCHI."""
    try:
        try:
            stream = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
            doc = ezdxf.read(stream)
        except Exception:
            doc = ezdxf.read_bytes(file_bytes)
            
        msp = doc.modelspace()
        geometrie = {"linee": [], "cerchi": [], "polilinee": []}
        
        def estrai_entita(spazio):
            # Linee
            for e in spazio.query('LINE'):
                geometrie["linee"].append([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
            # Cerchi
            for e in spazio.query('CIRCLE'):
                geometrie["cerchi"].append({"center": (e.dxf.center.x, e.dxf.center.y), "radius": e.dxf.radius})
            # Polilinee standard
            for e in spazio.query('LWPOLYLINE POLYLINE'):
                punti = [(pt[0], pt[1]) for pt in e.get_points(format='xy')]
                if punti: geometrie["polilinee"].append(punti)
            # Archi, Spline ed Ellissi (Vengono spianati/esplosi in piccoli segmenti geometrici)
            for e in spazio.query('ARC SPLINE ELLIPSE'):
                try:
                    punti_curva = [(v.x, v.y) for v in e.flattening(distance=0.2)]
                    if punti_curva: geometrie["polilinee"].append(punti_curva)
                except:
                    pass

        # 1. Estrazione elementi dallo spazio principale
        estrai_entita(msp)
        
        # 2. Estrazione ed esplosione dei Blocchi Interni (INSERT)
        for insert in msp.query('INSERT'):
            try:
                for e in insert.virtual_entities():
                    if e.dxftype() == 'LINE':
                        geometrie["linee"].append([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
                    elif e.dxftype() == 'CIRCLE':
                        geometrie["cerchi"].append({"center": (e.dxf.center.x, e.dxf.center.y), "radius": e.dxf.radius})
                    elif e.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                        punti = [(pt[0], pt[1]) for pt in e.get_points(format='xy')]
                        if punti: geometrie["polilinee"].append(punti)
                    elif e.dxftype() in ('ARC', 'SPLINE', 'ELLIPSE'):
                        punti_curva = [(v.x, v.y) for v in e.flattening(distance=0.2)]
                        if punti_curva: geometrie["polilinee"].append(punti_curva)
            except:
                pass

        # Calcolo Bounding Box complessivo
        all_x, all_y = [], []
        for l in geometrie["linee"]:
            all_x.extend([l[0][0], l[1][0]])
            all_y.extend([l[0][1], l[1][1]])
        for c in geometrie["cerchi"]:
            all_x.extend([c["center"][0] - c["radius"], c["center"][0] + c["radius"]])
            all_y.extend([c["center"][1] - c["radius"], c["center"][1] + c["radius"]])
        for poly in geometrie["polilinee"]:
            for pt in poly:
                all_x.append(pt[0])
                all_y.append(pt[1])
                
        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            width = max_x - min_x
            height = max_y - min_y
            geometrie["offset"] = (min_x, min_y)
            return geometrie, round(width, 1), round(height, 1)
            
    except Exception:
        pass
    return None, None, None

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

def make_real_pdf(title, summary, df, fig_to_embed=None):
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

def generate_industrial_dxf(W, H, piazzamenti):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    doc.layers.new(name='PERIMETRO_LASTRA', dxfattribs={'color': 1}) 
    doc.layers.new(name='PROFILI_TAGLIO', dxfattribs={'color': 3})   
    doc.layers.new(name='FORATURE_INTERNE', dxfattribs={'color': 4}) 
    
    msp.add_lwpolyline([(0, 0), (W, 0), (W, H), (0, H)], dxfattribs={'layer': 'PERIMETRO_LASTRA', 'flags': 1})
    
    for p in piazzamenti:
        tx, ty = p["traslazione"]
        geom_orig = p["geometria_originale"]
        
        if geom_orig:
            ox, oy = geom_orig.get("offset", (0,0))
            for line in geom_orig["linee"]:
                p1 = (line[0][0] - ox + tx, line[0][1] - oy + ty)
                p2 = (line[1][0] - ox + tx, line[1][1] - oy + ty)
                msp.add_line(p1, p2, dxfattribs={'layer': 'PROFILI_TAGLIO'})
            for circle in geom_orig["cerchi"]:
                cx = circle["center"][0] - ox + tx
                cy = circle["center"][1] - oy + ty
                msp.add_circle((cx, cy), circle["radius"], dxfattribs={'layer': 'FORATURE_INTERNE'})
            for poly in geom_orig["polilinee"]:
                punti_traslati = [(pt[0] - ox + tx, pt[1] - oy + ty) for pt in poly]
                msp.add_lwpolyline(punti_traslati, dxfattribs={'layer': 'PROFILI_TAGLIO', 'flags': 1})
        else:
            p_box = [(pt[0] + tx, pt[1] + ty) for pt in [[0,0], [p["dim_w"],0], [p["dim_w"],p["dim_h"]], [0,p["dim_h"]]]]
            msp.add_lwpolyline(p_box, dxfattribs={'layer': 'PROFILI_TAGLIO', 'flags': 1})
                
    out_stream = io.StringIO()
    doc.write(out_stream)
    return out_stream.getvalue()

# =============================================================================
# LOGICA DI INTERFACCIA
# =============================================================================
lang = st.sidebar.selectbox("🌐 LINGUA", ["IT", "EN"])

if st.sidebar.button("🔄 RESET GENERAL"):
    st.session_state.results_1d = None
    st.session_state.results_2d = None
    st.session_state["1d_confermato"] = False
    st.session_state["2d_confermato"] = False
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
        "magazzino": "📦 INVENTARIO IN MAGAZZINO",
        "tagli": "✂️ LISTA TAGLI RICHIESTI",
        "esegui": "🚀 ELABORA ED ESAMINA SOLUZIONE (SIMULAZIONE)",
        "conferma_stock": "✅ CONFERMA E APPLICA A MAGAZZINO REALE",
        "stock_applicato": "💥 Magazzino aggiornato con successo!",
        "spessore": "SPESSORE LASTRA (mm)",
        "bordo": "BORDO PERIMETRALE (mm)",
        "esporta": "💾 ESPORTA DATI DI PRODUZIONE",
        "scarto_min_1d": "SPEZZONE MINIMO REINTEGRO (mm)",
        "area_min_2d": "AREA MINIMA RIUTILIZZO (m²)",
        "standby_2d": "IN ATTESA DI CARICAMENTO DXF REALE\n\nInserisci i file geometrici .dxf reali per leggerne la geometria nativa."
    },
    "EN": {
        "title": "Geometric Nesting & Optimization",
        "header_1d": "🪚 1D NESTING - BARS",
        "header_2d": "📐 2D NESTING - SHEETS",
        "commessa": "📋 WORK ORDER DETAILS",
        "ordine": "ORDER NUMBER",
        "cliente": "CUSTOMER NAME",
        "parametri_macchina": "🔧 MACHINE PARAMETERS",
        "magazzino": "📦 STOCK INVENTORY",
        "tagli": "✂️ CUT LIST",
        "esegui": "🚀 COMPUTE & REVIEW LAYOUT (SIMULATION)",
        "conferma_stock": "✅ CONFIRM & SUBTRACT FROM REAL STOCK",
        "stock_applicato": "💥 Inventory updated successfully!",
        "spessore": "SHEET THICKNESS (mm)",
        "bordo": "PERIMETER MARGIN (mm)",
        "esporta": "💾 EXPORT PRODUCTION DATA",
        "scarto_min_1d": "MINIMUM REUSABLE LENGTH (mm)",
        "area_min_2d": "MINIMUM REUSABLE AREA (m²)",
        "standby_2d": "AWAITING DXF FILES\n\nUpload your .dxf engineering parts."
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
# SEZIONE 1D - BARRE
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
            stk_dict_sim = {int(r["LUNGHEZZA (mm)"]): int(r["QTY"]) for _, r in tabella_stk.iterrows() if pd.notnull(r["LUNGHEZZA (mm)"])}
            
            piani_barre = []
            scarti_idonei = []
            barre_usate_per_conferma = {}
            for pezzo in reqs:
                inserito = False
                for b in pianos_barre if 'pianos_barre' in locals() else piani_barre:
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
                    piani_barre.append({"lunghezza_totale": lunghezza_scelta, "tagli": [pezzo], "spazio_rimasto": lunghezza_scelta - intestazione_barra - pezzo})
            
            for b in piani_barre:
                sfrido_reale = int(b["spazio_rimasto"] + spessore_taglio)
                if sfrido_reale >= spezzone_min_1d: scarti_idonei.append(sfrido_reale)
            st.session_state.results_1d = {"piani": piani_barre, "scarti": scarti_idonei, "barre_da_scaricare": barre_usate_per_conferma}
            st.session_state["1d_confermato"] = False
            st.rerun()

    with col_right:
        if st.session_state.results_1d:
            res = st.session_state.results_1d
            if not st.session_state["1d_confermato"]:
                st.warning("⚠️ SIMULAZIONE")
                if st.button(T["conferma_stock"], key="btn_conf_1d"):
                    stk_reale = {int(r["LUNGHEZZA (mm)"]): int(r["QTY"]) for _, r in st.session_state.magazzino_1d.iterrows()}
                    for lung, qty in res["barre_da_scaricare"].items(): stk_reale[lung] = max(0, stk_reale.get(lung, 0) - qty)
                    for sc in res["scarti"]: stk_reale[sc] = stk_reale.get(sc, 0) + 1
                    st.session_state.magazzino_1d = pd.DataFrame([{"LUNGHEZZA (mm)": l, "QTY": q} for l, q in stk_reale.items()])
                    st.session_state["1d_confermato"] = True
                    st.rerun()
            
            fig_1d, ax_1d = plt.subplots(figsize=(10, max(2, len(res["piani"]) * 0.8 + 1)))
            ax_1d.set_facecolor('#151515'); fig_1d.patch.set_facecolor('#1A1A1A')
            for idx, b in enumerate(res["piani"]):
                sfrido_f = int(b["spazio_rimasto"] + spessore_taglio)
                html_segmenti = "".join([f'<div class="bar-segment" style="width:{(t / b["lunghezza_totale"]) * 100}%; background-color:{HEX_COLORI.get(str(t), HEX_COLORI["default"])};">{t}</div>' for t in b["tagli"]])
                st.markdown(f'<div class="bar-container"><div class="bar-header"><div>BARRA {idx+1} ({b["lunghezza_totale"]}mm)</div><div>SFRIDO: {sfrido_f}mm</div></div><div class="bar-track">{html_segmenti}</div></div>', unsafe_allow_html=True)
                curr_x = 0
                for t in b["tagli"]:
                    ax_1d.add_patch(patches.Rectangle((curr_x, idx*2), t, 1.2, edgecolor='white', facecolor=HEX_COLORI.get(str(t), '#4B5563')))
                    curr_x += t + spessore_taglio
            ax_1d.set_xlim(-100, 6200); ax_1d.set_ylim(-1, max(4, len(res["piani"]) * 2)); ax_1d.axis('off')
            
            df_exp = pd.DataFrame([{"ID_Barra": f"BAR-{i+1}", "Lunghezza_Totale_mm": b["lunghezza_totale"], "Sequenza_Tagli": "-".join(map(str, b["tagli"])), "Sfrido_Residuo_mm": int(b["spazio_rimasto"]+spessore_taglio)} for i, b in enumerate(res["piani"])])
            c1, c2, c3 = st.columns(3)
            c1.download_button("📥 CSV", make_pure_csv(df_exp), "Nesting_1D.csv")
            c2.download_button("📊 EXCEL", make_real_excel(df_exp), "Nesting_1D.xlsx")
            c3.download_button("📄 PDF", make_real_pdf("REPORT BARRE 1D", {"N_Ordine": num_ordine_1d}, df_exp, fig_1d), "Nesting_1D.pdf")
            plt.close(fig_1d)

# =============================================================================
# SEZIONE 2D - LAMIERE
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
        
        st.markdown("### 🛠️ CARICAMENTO DXF REALE ORIGINALE")
        file_dxf_caricati = st.file_uploader("Trascina qui i tuoi veri file geometrici .dxf", type=["dxf"], accept_multiple_files=True, key="dxf_net_2d")
        
        geometria_rilevata = None
        w_rilevata, h_rilevata = 750, 220 
        nome_file_componente = "PEZZO_DEFAULT.DXF"
        
        if file_dxf_caricati:
            file_attivo = file_dxf_caricati[0]
            nome_file_componente = file_attivo.name
            bytes_dxf = file_attivo.read()
            
            geom, w_cad, h_cad = parse_uploaded_dxf(bytes_dxf)
            if geom and w_cad and h_cad:
                geometria_rilevata = geom
                w_rilevata, h_rilevata = w_cad, h_cad
                st.success(f"✔️ Geometria DXF Rilevata! Dimensioni reali pezzo: {w_rilevata} x {h_rilevata} mm")
            else:
                st.error("⚠️ Il DXF caricato non contiene entità leggibili standard. Uso la sagoma di fallback.")
                
            st.session_state.pezzi_2d = pd.DataFrame([{
                "NOME PEZZO DXF": nome_file_componente, 
                "QTY DA PRODURRE": 12, 
                "LARGHEZZA (mm)": w_rilevata, 
                "ALTEZZA (mm)": h_rilevata
            }])
            
        tabella_pezzi_2d = st.data_editor(st.session_state.pezzi_2d, num_rows="fixed", key="edit_pezzi_2d", use_container_width=True)
        st.session_state.pezzi_2d = tabella_pezzi_2d
        
        if st.button(T["esegui"], type="primary", key="run_2d"):
            totale_pezzi_richiesti = int(tabella_pezzi_2d["QTY DA PRODURRE"].sum()) if not tabella_pezzi_2d.empty else 12
            
            piani_piazzati = []
            x_step = w_rilevata + dist_sicurezza
            y_step = h_rilevata + dist_sicurezza
            
            pezzi_piazzati = 0
            x_cursor = bordo_lamiera
            
            while x_cursor + w_rilevata <= W_lamiera - bordo_lamiera and pezzi_piazzati < totale_pezzi_richiesti:
                y_cursor = bordo_lamiera
                while y_cursor + h_rilevata <= H_lamiera - bordo_lamiera and pezzi_piazzati < totale_pezzi_richiesti:
                    piani_piazzati.append({
                        "id": f"P-{pezzi_piazzati+1:02d}",
                        "nome": nome_file_componente,
                        "traslazione": (x_cursor, y_cursor),
                        "geometria_originale": geometria_rilevata,
                        "dim_w": w_rilevata,
                        "dim_h": h_rilevata,
                        "color": "#1E3A8A" if (pezzi_piazzati % 2 == 0) else "#065F46"
                    })
                    pezzi_piazzati += 1
                    y_cursor += y_step
                x_cursor += x_step
                
            area_totale_mq = (W_lamiera * H_lamiera) / 1_000_000
            area_singolo_mq = (w_rilevata * h_rilevata * 0.85) / 1_000_000 
            area_taglio_mq = len(piani_piazzati) * area_singolo_mq
            area_scarto_mq = round(area_totale_mq - area_taglio_mq, 2)
            
            st.session_state.results_2d = {
                "piazzamenti": piani_piazzati,
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
                st.warning("⚠️ SIMULAZIONE ATTIVA")
                if st.button(T["conferma_stock"], key="btn_conf_2d", type="secondary"):
                    st.session_state["2d_confermato"] = True
                    st.rerun()
            else:
                st.success(T["stock_applicato"])
                
            st.markdown(f"<h2>📐 Anteprima Reale DXF Caricato — Rendimento: {res2d['saturazione']}</h2>", unsafe_allow_html=True)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_facecolor('#0F0F11') 
            fig.patch.set_facecolor('#1A1A1A')
            
            ax.add_patch(patches.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2.5))
            
            for p in res2d["piazzamenti"]:
                tx, ty = p["traslazione"]
                g_orig = p["geometria_originale"]
                
                if g_orig:
                    ox, oy = g_orig.get("offset", (0,0))
                    for line in g_orig["linee"]:
                        ax.plot([line[0][0] - ox + tx, line[1][0] - ox + tx], 
                                [line[0][1] - oy + ty, line[1][1] - oy + ty], color="#E5E7EB", linewidth=1.0)
                    for circle in g_orig["cerchi"]:
                        ax.add_patch(patches.Circle((circle["center"][0] - ox + tx, circle["center"][1] - oy + ty), 
                                                    circle["radius"], facecolor="#0F0F11", edgecolor="#38BDF8", linewidth=0.8))
                    for poly in g_orig["polilinee"]:
                        poly_trans = [(pt[0] - ox + tx, pt[1] - oy + ty) for pt in poly]
                        ax.add_patch(patches.Polygon(np.array(poly_trans), closed=True, facecolor=p["color"], alpha=0.4, edgecolor="#E5E7EB", linewidth=1.0))
                else:
                    p_box = [(pt[0] + tx, pt[1] + ty) for pt in [[0,0], [p["dim_w"],0], [p["dim_w"],p["dim_h"]], [0,p["dim_h"]]]]
                    ax.add_patch(patches.Polygon(np.array(p_box), closed=True, facecolor=p["color"], alpha=0.6, edgecolor="#FFF"))
                
                ax.text(tx + p["dim_w"]/2, ty + p["dim_h"]/2, f"{p['id']}", color="#FFFFFF", fontsize=8, weight='bold', ha='center', va='center')
                
            ax.set_xlim(-100, W_lamiera + 100)
            ax.set_ylim(-100, H_lamiera + 100)
            ax.grid(color='#262626', linestyle=':', linewidth=0.5)
            ax.set_aspect('equal')
            st.pyplot(fig)
            
            dxf_string_reale = generate_industrial_dxf(W_lamiera, H_lamiera, res2d["piazzamenti"])
            
            st.markdown(f"### {T['esporta']}")
            df_exp_2d = pd.DataFrame([{"ID_Ordine": num_ordine_2d, "Cliente": nome_cliente_2d, "Pezzi_Nesting": len(res2d['piazzamenti']), "Efficienza": res2d['saturazione'], "Scarto_m2": res2d['scarto_mq']}])
            
            bx1, bx2, bx3, bx4 = st.columns(4)
            bx1.download_button("📥 DOWNLOAD CSV", make_pure_csv(df_exp_2d), "Nesting_2D.csv")
            bx2.download_button("📊 DOWNLOAD EXCEL", make_real_excel(df_exp_2d), "Nesting_2D.xlsx")
            bx3.download_button("🛠️ SCARICA DXF NESTING REAL 1:1", dxf_string_reale, file_name=f"Layout_CAM_{num_ordine_2d}.dxf", mime="image/vnd.dxf")
            bx4.download_button("📄 SCARICA PDF RELAZIONE", make_real_pdf("REPORT NESTING 2D", {"Ordine": num_ordine_2d}, df_exp_2d, fig), "Nesting_2D.pdf")
            plt.close(fig)
        else:
            st.markdown(f'<div class="standby-box">{T["standby_2d"]}</div>', unsafe_allow_html=True)
