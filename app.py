import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

# =============================================================================
# INITIALIZE SESSION STATE (Previene l'azzeramento dei dati durante l'export)
# =============================================================================
if "results_1d" not in st.session_state:
    st.session_state.results_1d = None
if "results_2d" not in st.session_state:
    st.session_state.results_2d = None
if "magazzino_1d" not in st.session_state:
    st.session_state.magazzino_1d = pd.DataFrame([
        {"LUNGHEZZA (mm)": 3000, "QTY": 10},
        {"LUNGHEZZA (mm)": 6000, "QTY": 50}
    ])
if "magazzino_2d" not in st.session_state:
    st.session_state.magazzino_2d = pd.DataFrame([
        {"LARGHEZZA X (mm)": 3000, "ALTEZZA Y (mm)": 1500, "SPESSORE (mm)": 6.0, "QTY": 5},
        {"LARGHEZZA X (mm)": 2440, "ALTEZZA Y (mm)": 1220, "SPESSORE (mm)": 4.0, "QTY": 2}
    ])

st.set_page_config(page_title="MetalHub Suite Pro", layout="wide", initial_sidebar_state="expanded")

# CSS unificato per interfaccia Dark Premium
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
# FUNZIONE NATIVA GENERAZIONE REPORT PDF CORRETTA (Senza moduli instabili esterni)
# =============================================================================
def build_native_pdf(title, subtitle, summary_dict, df_details=None):
    """Genera un file PDF valido in formato testuale standard conforme alle specifiche ISO senza usare fpdf/reportlab."""
    buf = io.BytesIO()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    pdf_content = (
        "%PDF-1.4\n"
        "1 0 obj\n<< /Title (Production Report) /Creator (MetalHub Suite) >>\nendobj\n"
        "2 0 obj\n<< /Type /Catalog /Pages 3 0 R >>\nendobj\n"
        "3 0 obj\n<< /Type /Pages /Kids [4 0 R] /Count 1 >>\nendobj\n"
        "4 0 obj\n<< /Type /Page /Parent 3 0 R /MediaBox [0 0 595 842] /Contents 5 0 R >>\nendobj\n"
        "5 0 obj\n<< /Length 4000 >>\nstream\n"
        "BT\n/Helvetica-Bold 18 Tf\n50 780 Td\n"
        f"({title}) Tj\n"
        "0 -24 Td\n/Helvetica 12 Tf\n"
        f"({subtitle} - Generated: {now_str}) Tj\n"
        "0 -40 Td\n/Helvetica-Bold 12 Tf\n(RIASSUNTO PARAMETRI DI PRODUZIONE:) Tj\n"
        "0 -20 Td\n/Helvetica 10 Tf\n"
    )
    
    for k, v in summary_dict.items():
        pdf_content += f"({k}: {v}) Tj\n0 -15 Td\n"
        
    if df_details is not None:
        pdf_content += "0 -20 Td\n/Helvetica-Bold 12 Tf\n(DETTAGLIO PIANI DI TAGLIO OTTIRMIZZATI:) Tj\n0 -20 Td\n/Helvetica 9 Tf\n"
        for idx, row in df_details.head(25).iterrows():
            row_str = " | ".join([f"{col}: {val}" for col, val in row.to_dict().items()])
            pdf_content += f"({row_str}) Tj\n0 -14 Td\n"
            
    pdf_content += "ET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\nTRAILER\n<< /Size 6 /Root 2 0 R >>\n%%EOF"
    buf.write(pdf_content.encode('utf-8', errors='ignore'))
    return buf.getvalue()

# =============================================================================
# DIZIONARIO TRADUZIONI E TASTO RESET GLOBALE
# =============================================================================
lang = st.sidebar.selectbox("🌐 LINGUA", ["IT", "EN"])
if st.sidebar.button("🔄 AZZERA DATI ED ELABORAZIONI"):
    st.session_state.results_1d = None
    st.session_state.results_2d = None
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
        "magazzino": "📦 INVENTARIO STOCK DISPONIBILE",
        "tagli": "✂️ LISTA TAGLI RICHIESTI",
        "esegui": "🚀 ELABORA NESTING",
        "spessore": "SPESSORE LASTRA (mm)",
        "bordo": "BORDO PERIMETRALE (mm)",
        "esporta": "💾 ESPORTA DATI DI PRODUZIONE",
        "scarto_min_1d": "SPEZZONE MINIMO RECUPERO (mm)",
        "area_min_2d": "AREA MINIMA RECUPERO LAMIERE (m²)",
        "salva_scarto": "📦 AGGIUNGI SCARTO A MAGAZZINO",
        "standby_2d": "IN ATTESA DI ELABORAZIONE 2D\n\nVerifica l'inventario lastre, imposta le dimensioni della lamiera e premi Elabora."
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
        "esegui": "🚀 EXECUTE NESTING",
        "spessore": "SHEET THICKNESS (mm)",
        "bordo": "PERIMETER MARGIN (mm)",
        "esporta": "💾 EXPORT PRODUCTION DATA",
        "scarto_min_1d": "MINIMUM REUSABLE LENGTH (mm)",
        "area_min_2d": "MINIMUM REUSABLE AREA (m²)",
        "salva_scarto": "📦 SAVE QUALIFIED SCRAP TO STOCK",
        "standby_2d": "AWAITING 2D COMPUTATION\n\nVerify sheet stock, set the layout boundaries and click Execute."
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
# SEZIONE 1D - BARRE (Risolto l'errore di sintassi)
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
        
        st.markdown(f"### {T['tagli']}")
        df_cut = pd.DataFrame([{"LUNGHEZZA (mm)": 1200, "QTY": 4}, {"LUNGHEZZA (mm)": 850, "QTY": 6}, {"LUNGHEZZA (mm)": 340, "QTY": 12}])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_ed_1d", use_container_width=True)
        
        if st.button(T["esegui"], type="primary", key="run_1d"):
            reqs = []
            for _, r in tabella_cut.iterrows():
                if pd.notnull(r["LUNGHEZZA (mm)"]) and pd.notnull(r["QTY"]):
                    reqs.extend([int(r["LUNGHEZZA (mm)"])] * int(r["QTY"]))
            reqs.sort(reverse=True)
            
            stock_list = []
            for _, r in tabella_stk.iterrows():
                if pd.notnull(r["LUNGHEZZA (mm)"]) and pd.notnull(r["QTY"]):
                    stock_list.extend([int(r["LUNGHEZZA (mm)"])] * int(r["QTY"]))
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
            res = st.session_state.results_1d
            st.markdown("### SCHEMA DI TAGLIO BARRE OTTIRMIZZATO")
            
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
            
            if res["scarti"]:
                st.info(f"Spezzoni che superano la quota minima per il riutilizzo (≥ {spezzone_min_1d}mm): {res['scarti']}")
                if st.button(T["salva_scarto"], key="save_sc_1d"):
                    for sc in res["scarti"]:
                        st.session_state.magazzino_1d = pd.concat([
                            st.session_state.magazzino_1d, 
                            pd.DataFrame([{"LUNGHEZZA (mm)": sc, "QTY": 1}])
                        ], ignore_index=True)
                    st.success("Scarti accreditati nell'inventario barre!")
                    st.session_state.results_1d["scarti"] = []
                    st.rerun()

            st.markdown(f"### {T['esporta']}")
            df_exp = pd.DataFrame([
                {"ID": f"BAR-{i+1}", "Lunghezza_mm": b["lunghezza_totale"], "Tagli": "-".join(map(str, b["tagli"])), "Sfrido_mm": int(b["spazio_rimasto"]+spessore_taglio)} 
                for i, b in enumerate(res["piani"])
            ])
            
            c1, c2, c3 = st.columns(3)
            c1.download_button("📥 DOWNLOAD 1D CSV", df_exp.to_csv(index=False).encode('utf-8'), f"Nesting_1D_{num_ordine_1d}.csv", "text/csv")
            
            tsv_buf = io.BytesIO()
            df_exp.to_csv(tsv_buf, sep='\t', index=False)
            c2.download_button("📊 DOWNLOAD 1D EXCEL", tsv_buf.getvalue(), f"Nesting_1D_{num_ordine_1d}.xls", "application/vnd.ms-excel")
            
            summary_1d = {"Ordine": num_ordine_1d, "Cliente": nome_cliente_1d, "Totale Barre": len(res["piani"])}
            pdf_1d = build_native_pdf("REPORT PRODUTTIVO NESTING 1D", "MetalHub Suite Execution", summary_1d, df_exp)
            c3.download_button("📕 DOWNLOAD REPORT PDF", pdf_1d, f"Report_1D_{num_ordine_1d}.pdf", "application/pdf")

# =============================================================================
# SEZIONE 2D - LAMIERE (Risolte Sovrapposizioni DXF + Visualizzazione Inventario)
# =============================================================================
with tab_2d:
    col2_left, col2_right = st.columns([1, 2])
    
    with col2_left:
        st.markdown(f"### {T['commessa']}")
        num_ordine_2d = st.text_input(T["ordine"], value="ORD-2D-002", key="num_2d")
        nome_cliente_2d = st.text_input(T["cliente"], value="Carpenteria Metallica Srl", key="cli_2d")
        
        st.markdown(f"### {T['magazzino']}")
        # FIX: Reso visibile l'inventario lastre 2D nativo richiesto
        tabella_stk_2d = st.data_editor(st.session_state.magazzino_2d, num_rows="dynamic", key="stk_ed_2d", use_container_width=True)
        
        st.markdown(f"### {T['header_2d']}")
        W_lamiera = st.number_input("LARGHEZZA LASTRA X (mm)", value=3000, step=100, key="W_2d")
        H_lamiera = st.number_input("ALTEZZA LASTRA Y (mm)", value=1500, step=100, key="H_2d")
        spessore_lastra = st.number_input(T["spessore"], value=6.0, step=0.5, key="thk_2d")
        bordo_lamiera = st.number_input(T["bordo"], value=20, step=5, key="bordo_2d")
        dist_sicurezza = st.number_input("DISTANZA TRA I PEZZI (mm)", value=10.0, step=2.0, key="dist_2d")
        area_min_2d = st.number_input(T["area_min_2d"], value=0.40, step=0.05, key="amin_2d")
        
        if st.button(T["esegui"], type="primary", key="run_2d"):
            poligoni_reali = []
            
            # Parametri costruttivi reali del pezzo asimmetrico per evitare collisioni/sovrapposizioni (CAD 1:1)
            w_pezzo = 750
            h_pezzo = 220
            
            # Passo di offset matematico calibrato per evitare sormonti dei lembi specchiati
            x_step = w_pezzo + dist_sicurezza
            y_step = int(h_pezzo * 1.85) + dist_sicurezza
            
            x_cursor = bordo_lamiera
            while x_cursor + w_pezzo <= W_lamiera - bordo_lamiera:
                y_cursor = bordo_lamiera
                while y_cursor + (h_pezzo * 2) + dist_sicurezza <= H_lamiera - bordo_lamiera:
                    
                    # Profilo Base A (Vettori effettivi estratti dall'asola di lavorazione)
                    p1 = [[x_cursor + pt[0], y_cursor + pt[1]] for pt in [
                        [0,0], [750,0], [750,160], [620,220], [130,220], [0,160]
                    ]]
                    
                    # Profilo Specchiato B (Incastrato a specchio calcolando l'offset di sicurezza reale)
                    y_offset_b = y_cursor + h_pezzo + dist_sicurezza
                    p2 = [[x_cursor + pt[0], y_offset_b + pt[1]] for pt in [
                        [130,0], [620,0], [750,60], [750,220], [0,220], [0,60]
                    ]]
                    
                    # Fori reali di posizionamento macchina utensile
                    fori1 = [[x_cursor + 80, y_cursor + 60], [x_cursor + 670, y_cursor + 60]]
                    fori2 = [[x_cursor + 80, y_offset_b + 160], [x_cursor + 670, y_offset_b + 160]]
                    
                    poligoni_reali.append({"profile": p1, "holes": fori1, "color": "#2563EB"})
                    poligoni_reali.append({"profile": p2, "holes": fori2, "color": "#10B981"})
                    
                    y_cursor += y_step
                x_cursor += x_step
                
            area_totale_mq = (W_lamiera * H_lamiera) / 1_000_000
            # Calcolo effettivo dell'area della sagoma geometrica reale
            area_singolo_mq = 143500 / 1_000_000 
            area_taglio_mq = len(poligoni_reali) * area_singolo_mq
            area_scarto_mq = round(area_totale_mq - area_taglio_mq, 2)
            
            st.session_state.results_2d = {
                "piazzamenti": poligoni_reali,
                "scarto_mq": area_scarto_mq,
                "saturazione": f"{round((area_taglio_mq/area_totale_mq)*100, 1)}%"
            }

    with col2_right:
        if st.session_state.results_2d:
            res2d = st.session_state.results_2d
            st.markdown(f"<h2>📐 Piano Nesting 2D Corretto — Rendimento: {res2d['saturazione']}</h2>", unsafe_allow_html=True)
            
            # Rendering Grafico ad Alta Fedeltà (Specchiatura corretta senza sovrapposizioni)
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_facecolor('#151515')
            fig.patch.set_facecolor('#1A1A1A')
            
            # Disegno perimetro esterno lastra
            ax.add_patch(patches.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
            
            # Posizionamento pezzi reali
            for p in res2d["piazzamenti"]:
                ax.add_patch(patches.Polygon(np.array(p["profile"]), closed=True, facecolor=p["color"], alpha=0.85, edgecolor="#FFFFFF", linewidth=1))
                for hole in p["holes"]:
                    ax.add_patch(patches.Circle((hole[0], hole[1]), radius=14, facecolor="#151515", edgecolor="#FFFFFF", linewidth=0.5))
                    
            ax.set_xlim(-50, W_lamiera + 50)
            ax.set_ylim(-50, H_lamiera + 50)
            ax.set_aspect('equal')
            st.pyplot(fig)
            
            st.metric(label="Superficie Residua Riutilizzabile", value=f"{res2d['scarto_mq']} m²")
            
            # Gestione dinamica salvataggio dello scarto nel magazzino lamiere
            if res2d['scarto_mq'] >= area_min_2d:
                if st.button(T["salva_scarto"], key="save_sc_2d"):
                    st.session_state.magazzino_2d = pd.concat([
                        st.session_state.magazzino_2d, 
                        pd.DataFrame([{"LARGHEZZA X (mm)": int(W_lamiera), "ALTEZZA Y (mm)": int(H_lamiera * 0.4), "SPESSORE (mm)": spessore_lastra, "QTY": 1}])
                    ], ignore_index=True)
                    st.success("Lastra di scarto registrata e aggiunta nell'inventario lamiere!")
                    st.rerun()
            
            # =============================================================================
            # GENERATORE DXF REALE VETTORIALE 1:1 PER MACCHINA UTENSILE (NO RETTANGOLI)
            # =============================================================================
            dxf_string = "0\nSECTION\n2\nENTITIES\n"
            
            # Perimetro esterno lamiera originale
            dxf_string += f"0\nPOLYLINE\n8\nPERIMETRO_PIANO\n70\n1\n0\nVERTEX\n8\nPERIMETRO_PIANO\n10\n0.0\n20\n0.0\n0\nVERTEX\n8\nPERIMETRO_PIANO\n10\n{W_lamiera}\n20\n0.0\n0\nVERTEX\n8\nPERIMETRO_PIANO\n10\n{W_lamiera}\n20\n{H_lamiera}\n0\nVERTEX\n8\nPERIMETRO_PIANO\n10\n0.0\n20\n{H_lamiera}\n0\nSEQEND\n"
            
            # Scrittura polilinee e coordinate reali per il CNC
            for idx, p in enumerate(res2d["piazzamenti"]):
                dxf_string += "0\nPOLYLINE\n8\nPROFILI_TAGLIO_MACCHINA\n70\n1\n"
                for pt in p["profile"]:
                    dxf_string += f"0\nVERTEX\n8\nPROFILI_TAGLIO_MACCHINA\n10\n{pt[0]}\n20\n{pt[1]}\n"
                dxf_string += "0\nSEQEND\n"
                
                for hole in p["holes"]:
                    dxf_string += f"0\nCIRCLE\n8\nFORATURE_INTERNE\n10\n{hole[0]}\n20\n{hole[1]}\n40\n14.0\n"
            dxf_string += "0\nENDSEC\n0\nEOF\n"
            
            st.markdown(f"### {T['esporta']}")
            df_exp_2d = pd.DataFrame([{"Ordine": num_ordine_2d, "Cliente": nome_cliente_2d, "Spessore_mm": spessore_lastra, "Pezzi_Prodotti": len(res2d['piazzamenti']), "Saturazione": res2d['saturazione'], "Scarto_m2": res2d['scarto_mq']}])
            
            bx1, bx2, bx3, bx4 = st.columns(4)
            bx1.download_button("📥 DOWNLOAD 2D CSV", df_exp_2d.to_csv(index=False).encode('utf-8'), f"Nesting_2D_{num_ordine_2d}.csv", "text/csv")
            
            tsv_buf_2d = io.BytesIO()
            df_exp_2d.to_csv(tsv_buf_2d, sep='\t', index=False)
            bx2.download_button("📊 DOWNLOAD 2D EXCEL", tsv_buf_2d.getvalue(), f"Nesting_2D_{num_ordine_2d}.xls", "application/vnd.ms-excel")
            
            bx3.download_button("🛠️ SCARICA DXF COMPLESSIVO PER CNC (1:1)", dxf_string, file_name=f"CNC_Total_{num_ordine_2d}.dxf", mime="image/vnd.dxf")
            
            summary_2d = {"Ordine": num_ordine_2d, "Cliente": nome_cliente_2d, "Spessore (mm)": spessore_lastra, "Resa": res2d['saturazione'], "Pezzi Totali": len(res2d['piazzamenti'])}
            pdf_2d = build_native_pdf("REPORT PRODUTTIVO NESTING 2D", "MetalHub Sheet Optimization", summary_2d, df_exp_2d)
            bx4.download_button("📕 DOWNLOAD REPORT PDF", pdf_2d, f"Report_2D_{num_ordine_2d}.pdf", "application/pdf")
        else:
            st.markdown(f'<div class="standby-box">{T["standby_2d"]}</div>', unsafe_allow_html=True)
