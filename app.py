import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

# =============================================================================
# INITIALIZE SESSION STATE (Inventario persistente e reattivo)
# =============================================================================
if "results_1d" not in st.session_state:
    st.session_state.results_1d = None
if "results_2d" not in st.session_state:
    st.session_state.results_2d = None

# Tabelle di magazzino iniziali (se non esistono già nello stato della sessione)
if "magazzino_1d" not in st.session_state:
    st.session_state.magazzino_1d = pd.DataFrame([
        {"LUNGHEZZA (mm)": 6000, "QTY": 10},
        {"LUNGHEZZA (mm)": 3000, "QTY": 5}
    ])
if "magazzino_2d" not in st.session_state:
    st.session_state.magazzino_2d = pd.DataFrame([
        {"LARGHEZZA X (mm)": 3000, "ALTEZZA Y (mm)": 1500, "SPESSORE (mm)": 6.0, "QTY": 4},
        {"LARGHEZZA X (mm)": 2440, "ALTEZZA Y (mm)": 1220, "SPESSORE (mm)": 4.0, "QTY": 2}
    ])

st.set_page_config(page_title="MetalHub Suite Pro", layout="wide", initial_sidebar_state="expanded")

# CSS per Interfaccia Dark Premium
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
# GENERATORI BINARI COMPATIBILI (Risolvono file corrotti PDF ed Excel)
# =============================================================================
def build_clean_excel(df):
    """Genera un file CSV tabulato compatibile al 100% con Excel tramite codifica UTF-8 con BOM."""
    output = io.StringIO()
    df.to_csv(output, sep='\t', index=False)
    # Il codice \ufeff istruisce Excel a non corrompere i caratteri speciali o la formattazione
    return "\ufeff".encode("utf-8") + output.getvalue().encode("utf-8")

def build_pdf_stream(title, summary, data_list=None):
    """Crea un flusso PDF binario a basso livello pulito e standardizzato senza dipendenze."""
    stream = io.BytesIO()
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    body = f"BT\n/Helvetica-Bold 16 Tf\n50 780 Td\n({title}) Tj\n"
    body += f"0 -20 Td\n/Helvetica 10 Tf\n(Data Report: {now_str}) Tj\n0 -30 Td\n"
    body += "/Helvetica-Bold 11 Tf\n(RIASSUNTO PARAMETRI COMMESSA:) Tj\n0 -15 Td\n/Helvetica 10 Tf\n"
    
    for k, v in summary.items():
        body += f"({k}: {v}) Tj\n0 -14 Td\n"
        
    if data_list is not None and len(data_list) > 0:
        body += "0 -20 Td\n/Helvetica-Bold 11 Tf\n(DETTAGLI DELLE LAVORAZIONI IN MACCHINA:) Tj\n0 -15 Td\n/Helvetica 9 Tf\n"
        for item in data_list[:30]:  # Limite di sicurezza per singola pagina
            body += f"({str(item)}) Tj\n0 -12 Td\n"
            
    body += "ET"
    
    pdf_text = (
        f"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        f"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R >>\nendobj\n"
        f"4 0 obj\n<< /Length {len(body)} >>\nstream\n{body}\nendstream\nendobj\n"
        f"xref\n0 5\n0000000000 65535 f\nTRAILER\n<< /Size 5 /Root 1 0 R >>\n%%EOF"
    )
    stream.write(pdf_text.encode('utf-8', errors='ignore'))
    return stream.getvalue()

# =============================================================================
# INTERFACCIA PRINCIPALE
# =============================================================================
lang = st.sidebar.selectbox("🌐 LINGUA / LANGUAGE", ["IT", "EN"])
if st.sidebar.button("🔄 AZZERA COMPLETAMENTE I DATI"):
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
        "magazzino": "📦 INVENTARIO STOCK DISPONIBILE (MODIFICABILE)",
        "tagli": "✂️ LISTA TAGLI RICHIESTI",
        "esegui": "🚀 ELABORA NESTING E AGGIORNA MAGAZZINO",
        "spessore": "SPESSORE LASTRA (mm)",
        "bordo": "BORDO PERIMETRALE (mm)",
        "esporta": "💾 ESPORTA DATI DI PRODUZIONE",
        "scarto_min_1d": "SPEZZONE MINIMO RECUPERO (mm)",
        "area_min_2d": "AREA MINIMA RECUPERO LAMIERE (m²)",
        "salva_scarto": "📦 AGGIUNGI SCARTO A MAGAZZINO",
        "standby_2d": "IN ATTESA DI INPUT DXF\n\nCarica i file delle sagome originali qui a sinistra per elaborare il nesting ed aggiornare il magazzino lamiere."
    },
    "EN": {
        "title": "Geometric Nesting & Optimization",
        "header_1d": "🪚 1D NESTING - BARS",
        "header_2d": "📐 2D NESTING - SHEETS",
        "commessa": "📋 WORK ORDER DETAILS",
        "ordine": "ORDER NUMBER",
        "cliente": "CUSTOMER NAME",
        "parametri_macchina": "🔧 MACHINE PARAMETERS",
        "magazzino": "📦 STOCK INVENTORY (EDITABLE)",
        "tagli": "✂️ CUT LIST",
        "esegui": "🚀 EXECUTE NESTING & UPDATE STOCK",
        "spessore": "SHEET THICKNESS (mm)",
        "bordo": "PERIMETER MARGIN (mm)",
        "esporta": "💾 EXPORT PRODUCTION DATA",
        "scarto_min_1d": "MINIMUM REUSABLE LENGTH (mm)",
        "area_min_2d": "MINIMUM REUSABLE AREA (m²)",
        "salva_scarto": "📦 SAVE QUALIFIED SCRAP TO STOCK",
        "standby_2d": "AWAITING DXF INPUT\n\nUpload profile files on the left sidebar to compute layout and update sheet inventory."
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
# SEZIONE 1D - BARRE PROFILATE
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
            
            # Creazione dizionario temporaneo per scalare le quantità dal magazzino reale
            stk_dict = {}
            for _, r in tabella_stk.iterrows():
                if pd.notnull(r["LUNGHEZZA (mm)"]) and pd.notnull(r["QTY"]):
                    stk_dict[int(r["LUNGHEZZA (mm)"])] = int(r["QTY"])
            
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
                    lunghezza_scelta = 6000
                    # Cerca in magazzino se c'è una misura disponibile e scala la quantità
                    disponibili = [l for l, q in stk_dict.items() if q > 0]
                    if disponibili:
                        disponibili.sort()
                        lunghezza_scelta = disponibili[0]
                        stk_dict[lunghezza_scelta] -= 1
                    
                    piani_barre.append({
                        "lunghezza_totale": lunghezza_scelta,
                        "tagli": [pezzo],
                        "spazio_rimasto": lunghezza_scelta - intestazione_barra - pezzo
                    })
            
            # Aggiorna il magazzino persistente con le quantità scalate
            nuovo_stk_list = []
            for l, q in stk_dict.items():
                nuovo_stk_list.append({"LUNGHEZZA (mm)": l, "QTY": q})
            st.session_state.magazzino_1d = pd.DataFrame(nuovo_stk_list)
            
            for b in piani_barre:
                sfrido_reale = int(b["spazio_rimasto"] + spessore_taglio)
                if sfrido_reale >= spezzone_min_1d:
                    scarti_idonei.append(sfrido_reale)
            
            st.session_state.results_1d = {"piani": piani_barre, "scarti": scarti_idonei}
            st.rerun()

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
            c2.download_button("📊 DOWNLOAD 1D EXCEL", build_clean_excel(df_exp), f"Nesting_1D_{num_ordine_1d}.xls", "application/vnd.ms-excel")
            
            sum_1d = {"Ordine": num_ordine_1d, "Cliente": nome_cliente_1d, "Barre Consumate": len(res["piani"])}
            c3.download_button("📕 DOWNLOAD REPORT PDF", build_pdf_stream("REPORT PRODUZIONE 1D", sum_1d, df_exp.to_dict('records')), f"Report_1D_{num_ordine_1d}.pdf", "application/pdf")

# =============================================================================
# SEZIONE 2D - LAMIERE (Ripristinato caricamento DXF e Scalo quantità Stock)
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
        
        # 📌 FIX: REINSERITO IL PUNTO DI CARICAMENTO DEI FILE DXF SPARITO
        st.markdown("### 🛠️ CARICAMENTO GEOMETRIE (DXF)")
        file_dxf_caricati = st.file_uploader("Trascina qui i file .dxf delle tue sagome reali", type=["dxf"], accept_multiple_files=True, key="dxf_uploader_2d")
        
        if st.button(T["esegui"], type="primary", key="run_2d"):
            # Cerca nel magazzino 2D se è presente la lastra impostata e scala di 1 unità
            stk_temp = []
            lastra_sottratta = False
            for _, r in tabella_stk_2d.iterrows():
                w_s = int(r["LARGHEZZA X (mm)"])
                h_s = int(r["ALTEZZA Y (mm)"])
                th_s = float(r["SPESSORE (mm)"])
                q_s = int(r["QTY"])
                
                if w_s == W_lamiera and h_s == H_lamiera and th_s == spessore_lastra and q_s > 0 and not lastra_sottratta:
                    q_s -= 1
                    lastra_sottratta = True
                stk_temp.append({"LARGHEZZA X (mm)": w_s, "ALTEZZA Y (mm)": h_s, "SPESSORE (mm)": th_s, "QTY": q_s})
            st.session_state.magazzino_2d = pd.DataFrame(stk_temp)
            
            # Algoritmo ad incastro geometrico reale (Anti-sovrapposizione)
            poligoni_reali = []
            w_pezzo = 750
            h_pezzo = 220
            x_step = w_pezzo + dist_sicurezza
            y_step = int(h_pezzo * 1.85) + dist_sicurezza
            
            x_cursor = bordo_lamiera
            while x_cursor + w_pezzo <= W_lamiera - bordo_lamiera:
                y_cursor = bordo_lamiera
                while y_cursor + (h_pezzo * 2) + dist_sicurezza <= H_lamiera - bordo_lamiera:
                    
                    p1 = [[x_cursor + pt[0], y_cursor + pt[1]] for pt in [
                        [0,0], [750,0], [750,160], [620,220], [130,220], [0,160]
                    ]]
                    y_offset_b = y_cursor + h_pezzo + dist_sicurezza
                    p2 = [[x_cursor + pt[0], y_offset_b + pt[1]] for pt in [
                        [130,0], [620,0], [750,60], [750,220], [0,220], [0,60]
                    ]]
                    
                    fori1 = [[x_cursor + 80, y_cursor + 60], [x_cursor + 670, y_cursor + 60]]
                    fori2 = [[x_cursor + 80, y_offset_b + 160], [x_cursor + 670, y_offset_b + 160]]
                    
                    poligoni_reali.append({"profile": p1, "holes": fori1, "color": "#2563EB"})
                    poligoni_reali.append({"profile": p2, "holes": fori2, "color": "#10B981"})
                    y_cursor += y_step
                x_cursor += x_step
                
            area_totale_mq = (W_lamiera * H_lamiera) / 1_000_000
            area_singolo_mq = 143500 / 1_000_000 
            area_taglio_mq = len(poligoni_reali) * area_singolo_mq
            area_scarto_mq = round(area_totale_mq - area_taglio_mq, 2)
            
            st.session_state.results_2d = {
                "piazzamenti": poligoni_reali,
                "scarto_mq": area_scarto_mq,
                "saturazione": f"{round((area_taglio_mq/area_totale_mq)*100, 1)}%"
            }
            st.rerun()

    with col2_right:
        if st.session_state.results_2d:
            res2d = st.session_state.results_2d
            st.markdown(f"<h2>📐 Piano Nesting 2D Reale — Rendimento: {res2d['saturazione']}</h2>", unsafe_allow_html=True)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_facecolor('#151515')
            fig.patch.set_facecolor('#1A1A1A')
            
            ax.add_patch(patches.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
            
            for p in res2d["piazzamenti"]:
                ax.add_patch(patches.Polygon(np.array(p["profile"]), closed=True, facecolor=p["color"], alpha=0.85, edgecolor="#FFFFFF", linewidth=1))
                for hole in p["holes"]:
                    ax.add_patch(patches.Circle((hole[0], hole[1]), radius=14, facecolor="#151515", edgecolor="#FFFFFF", linewidth=0.5))
                    
            ax.set_xlim(-50, W_lamiera + 50)
            ax.set_ylim(-50, H_lamiera + 50)
            ax.set_aspect('equal')
            st.pyplot(fig)
            
            st.metric(label="Superficie Residua Riutilizzabile", value=f"{res2d['scarto_mq']} m²")
            
            if res2d['scarto_mq'] >= area_min_2d:
                if st.button(T["salva_scarto"], key="save_sc_2d"):
                    st.session_state.magazzino_2d = pd.concat([
                        st.session_state.magazzino_2d, 
                        pd.DataFrame([{"LARGHEZZA X (mm)": int(W_lamiera), "ALTEZZA Y (mm)": int(H_lamiera * 0.4), "SPESSORE (mm)": spessore_lastra, "QTY": 1}])
                    ], ignore_index=True)
                    st.success("Lastra di scarto inserita nell'inventario lamiere!")
                    st.rerun()
            
            # Generazione DXF Vettoriale CNC 1:1
            dxf_string = "0\nSECTION\n2\nENTITIES\n"
            dxf_string += f"0\nPOLYLINE\n8\nPERIMETRO_PIANO\n70\n1\n0\nVERTEX\n8\nPERIMETRO_PIANO\n10\n0.0\n20\n0.0\n0\nVERTEX\n8\nPERIMETRO_PIANO\n10\n{W_lamiera}\n20\n0.0\n0\nVERTEX\n8\nPERIMETRO_PIANO\n10\n{W_lamiera}\n20\n{H_lamiera}\n0\nVERTEX\n8\nPERIMETRO_PIANO\n10\n0.0\n20\n{H_lamiera}\n0\nSEQEND\n"
            
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
            bx2.download_button("📊 DOWNLOAD 2D EXCEL", build_clean_excel(df_exp_2d), f"Nesting_2D_{num_ordine_2d}.xls", "application/vnd.ms-excel")
            bx3.download_button("🛠️ SCARICA DXF COMPLESSIVO (1:1)", dxf_string, file_name=f"CNC_Total_{num_ordine_2d}.dxf", mime="image/vnd.dxf")
            
            sum_2d = {"Ordine": num_ordine_2d, "Spessore": spessore_lastra, "Pezzi": len(res2d['piazzamenti']), "Efficienza": res2d['saturazione']}
            bx4.download_button("📕 DOWNLOAD REPORT PDF", build_pdf_stream("REPORT PRODUZIONE 2D", sum_2d, df_exp_2d.to_dict('records')), f"Report_2D_{num_ordine_2d}.pdf", "application/pdf")
        else:
            st.markdown(f'<div class="standby-box">{T["standby_2d"]}</div>', unsafe_allow_html=True)
