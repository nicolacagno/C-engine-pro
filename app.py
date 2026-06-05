import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import ezdxf

REPORTLAB_AVAILABLE = False

# =============================================================================
# STATO DELLA SESSIONE
# =============================================================================
if "results_1d" not in st.session_state:
    st.session_state.results_1d = None
if "results_2d" not in st.session_state:
    st.session_state.results_2d = None

if "1d_confermato" not in st.session_state:
    st.session_state["1d_confermato"] = False
if "2d_confermato" not in st.session_state:
    st.session_state["2d_confermato"] = False

# Inizializzazione magazzini con la nuova colonna CODICE MATERIALE
if "magazzino_1d" not in st.session_state:
    st.session_state.magazzino_1d = pd.DataFrame([
        {"CODICE MATERIALE": "FE360", "LUNGHEZZA (mm)": 6000, "QTY": 10},
        {"CODICE MATERIALE": "INOX304", "LUNGHEZZA (mm)": 6000, "QTY": 5},
        {"CODICE MATERIALE": "FE360", "LUNGHEZZA (mm)": 3000, "QTY": 5}
    ])
if "magazzino_2d" not in st.session_state:
    st.session_state.magazzino_2d = pd.DataFrame([
        {"CODICE MATERIALE": "L_FE_6MM", "LARGHEZZA X (mm)": 3000, "ALTEZZA Y (mm)": 1500, "SPESSORE (mm)": 6.0, "QTY": 5},
        {"CODICE MATERIALE": "L_INOX_4MM", "LARGHEZZA X (mm)": 2440, "ALTEZZA Y (mm)": 1220, "SPESSORE (mm)": 4.0, "QTY": 2}
    ])

if "pezzi_2d" not in st.session_state:
    st.session_state.pezzi_2d = pd.DataFrame(columns=["NOME PEZZO DXF", "CODICE RICHIESTO", "QTY DA PRODURRE", "LARGHEZZA (mm)", "ALTEZZA (mm)"])

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
# PARSER GEOMETRICO DXF
# =============================================================================
def parse_uploaded_dxf(file_bytes):
    try:
        stream = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
        doc = ezdxf.read(stream)
        geometrie = {"linee": [], "cerchi": [], "polilinee": []}
        
        def estrai_da_contenitore(spazio):
            for e in spazio.query('LINE'):
                geometrie["linee"].append([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
            for e in spazio.query('CIRCLE'):
                geometrie["cerchi"].append({"center": (e.dxf.center.x, e.dxf.center.y), "radius": e.dxf.radius})
            for e in spazio.query('LWPOLYLINE POLYLINE'):
                try:
                    punti = [(pt[0], pt[1]) for pt in e.get_points(format='xy')]
                    if punti: geometrie["polilinee"].append(punti)
                except: pass
            for e in spazio.query('ARC SPLINE ELLIPSE'):
                try:
                    punti_curva = [(v.x, v.y) for v in e.flattening(distance=0.25)]
                    if punti_curva: geometrie["polilinee"].append(punti_curva)
                except: pass

        msp = doc.modelspace()
        estrai_da_contenitore(msp)
        if len(geometrie["linee"]) == 0 and len(geometrie["cerchi"]) == 0 and len(geometrie["polilinee"]) == 0:
            for blocco in doc.blocks:
                if not blocco.name.startswith('*'):
                    estrai_da_contenitore(blocco)

        all_x, all_y = [], []
        for l in geometrie["linee"]:
            all_x.extend([l[0][0], l[1][0]])
            all_y.extend([l[0][1], l[1][1]])
        for c in geometrie["cerchi"]:
            all_x.extend([c["center"][0] - c["radius"], c["center"][0] + c["radius"]])
            all_y.extend([c["center"][1] - c["radius"], c["center"][1] + c["radius"]])
        for poly in geometrie["polilinee"]:
            for pt in poly:
                all_x.append(pt[0]); all_y.append(pt[1])
                
        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            return geometrie, round(max_x - min_x, 1), round(max_y - min_y, 1)
    except: pass
    return None, None, None

# =============================================================================
# ESPORTAZIONE FILE
# =============================================================================
def make_pure_csv(df):
    return df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

def make_real_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Nesting_Report')
    return output.getvalue()

def generate_industrial_dxf(W, H, piazzamenti):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    doc.layers.new(name='PERIMETRO_LASTRA', dxfattribs={'color': 1}) 
    doc.layers.new(name='PROFILI_TAGLIO', dxfattribs={'color': 3})   
    msp.add_lwpolyline([(0, 0), (W, 0), (W, H), (0, H)], dxfattribs={'layer': 'PERIMETRO_LASTRA', 'flags': 1})
    
    for p in piazzamenti:
        tx, ty = p["traslazione"]
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
    st.session_state.pezzi_2d = pd.DataFrame(columns=["NOME PEZZO DXF", "CODICE RICHIESTO", "QTY DA PRODURRE", "LARGHEZZA (mm)", "ALTEZZA (mm)"])
    st.rerun()

TXT = {
    "IT": {
        "title": "Nesting Multi-Codice Geometrico",
        "header_1d": "🪚 NESTING 1D - BARRE",
        "header_2d": "📐 NESTING 2D - LAMIERE",
        "commessa": "📋 INTESTAZIONE COMMESSA",
        "ordine": "NUMERO ORDINE",
        "cliente": "NOME CLIENTE",
        "parametri_macchina": "🔧 PARAMETRI MACCHINA",
        "magazzino": "📦 INVENTARIO IN MAGAZZINO (CON CODICE)",
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
        "title": "Multi-Code Nesting Engine",
        "header_1d": "🪚 1D NESTING - BARS",
        "header_2d": "📐 2D NESTING - SHEETS",
        "commessa": "📋 WORK ORDER DETAILS",
        "ordine": "ORDER NUMBER",
        "cliente": "CUSTOMER NAME",
        "parametri_macchina": "🔧 MACHINE PARAMETERS",
        "magazzino": "📦 STOCK INVENTORY (WITH CODE)",
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
        <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:10px;">🔥 MetalHub Suite v2</span>
        <span style="color:#666666; font-size:11px; font-weight:bold; letter-spacing:1px;">{T['title'].upper()}</span>
    </div>
""", unsafe_allow_html=True)

tab_1d, tab_2d = st.tabs([T["header_1d"], T["header_2d"]])

# =============================================================================
# SEZIONE 1D - BARRE MULTI-CODICE
# =============================================================================
with tab_1d:
    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.markdown(f"### {T['commessa']}")
        num_ordine_1d = st.text_input(T["ordine"], value="ORD-1D-MULTI", key="num_1d")
        nome_cliente_1d = st.text_input(T["cliente"], value="Carpenteria Srl", key="cli_1d")
        
        st.markdown(f"### {T['parametri_macchina']}")
        spessore_taglio = st.number_input("BLADE KERF (mm)", value=3.0, step=0.5, key="lama_1d")
        intestazione_barra = st.number_input("INTESTATURA (mm)", value=20.0, step=5.0, key="int_1d")
        spezzone_min_1d = st.number_input(T["scarto_min_1d"], value=1000.0, step=100.0, key="min_1d")
        
        st.markdown(f"### {T['magazzino']}")
        tabella_stk = st.data_editor(st.session_state.magazzino_1d, num_rows="dynamic", key="stk_ed_1d", use_container_width=True)
        st.session_state.magazzino_1d = tabella_stk
        
        st.markdown(f"### {T['tagli']}")
        df_cut = pd.DataFrame([
            {"CODICE RICHIESTO": "FE360", "LUNGHEZZA (mm)": 1200, "QTY": 4},
            {"CODICE RICHIESTO": "FE360", "LUNGHEZZA (mm)": 850, "QTY": 3},
            {"CODICE RICHIESTO": "INOX304", "LUNGHEZZA (mm)": 1200, "QTY": 3}
        ])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_ed_1d", use_container_width=True)
        
        if st.button(T["esegui"], type="primary", key="run_1d"):
            # Generazione dizionario magazzino suddiviso per Codici
            stk_struttura = {}
            for _, r in tabella_stk.iterrows():
                if pd.notnull(r["CODICE MATERIALE"]) and pd.notnull(r["LUNGHEZZA (mm)"]):
                    cod = str(r["CODICE MATERIALE"]).strip()
                    lung = int(r["LUNGHEZZA (mm)"])
                    qty = int(r["QTY"])
                    if cod not in stk_struttura: stk_struttura[cod] = {}
                    stk_struttura[cod][lung] = stk_struttura[cod].get(lung, 0) + qty

            piani_barre = []
            scarti_idonei_da_reintegrare = []
            barre_usate_per_conferma = [] # lista di tuple (codice, lunghezza)
            
            # Raggruppa le richieste per codice richiesto
            for _, cut_row in tabella_cut.iterrows():
                if pd.notnull(cut_row["CODICE RICHIESTO"]) and pd.notnull(cut_row["LUNGHEZZA (mm)"]) and pd.notnull(cut_row["QTY"]):
                    cod_req = str(cut_row["CODICE RICHIESTO"]).strip()
                    lung_pezzo = int(cut_row["LUNGHEZZA (mm)"])
                    qty_pezzo = int(cut_row["QTY"])
                    
                    for _ in range(qty_pezzo):
                        inserito = False
                        # Cerca se tra i piani già aperti per QUESTO SPECIFICO CODICE c'è spazio
                        for b in piani_barre:
                            if b["codice"] == cod_req and (lung_pezzo + spessore_taglio) <= b["spazio_rimasto"]:
                                b["tagli"].append(lung_pezzo)
                                b["spazio_rimasto"] -= (lung_pezzo + spessore_taglio)
                                inserito = True
                                break
                        
                        # Se non c'è spazio, preleva una nuova barra adatta dal magazzino per quel codice
                        if not inserito:
                            lunghezza_scelta = 6000
                            sub_stock = stk_struttura.get(cod_req, {})
                            disponibili = [l for l, q in sub_stock.items() if q > 0]
                            
                            if disponibili:
                                disponibili.sort()
                                lunghezza_scelta = disponibili[0]
                                stk_struttura[cod_req][lunghezza_scelta] -= 1
                            
                            barre_usate_per_conferma.append({"CODICE": cod_req, "LUNGHEZZA": lunghezza_scelta})
                            piani_barre.append({
                                "codice": cod_req,
                                "lunghezza_totale": lunghezza_scelta,
                                "tagli": [lung_pezzo],
                                "spazio_rimasto": lunghezza_scelta - intestazione_barra - lung_pezzo
                            })
            
            for b in piani_barre:
                sfrido_reale = int(b["spazio_rimasto"] + spessore_taglio)
                if sfrido_reale >= spezzone_min_1d:
                    scarti_idonei_da_reintegrare.append({"CODICE MATERIALE": b["codice"], "LUNGHEZZA (mm)": sfrido_reale, "QTY": 1})
                    
            st.session_state.results_1d = {"piani": piani_barre, "scarti": scarti_idonei_da_reintegrare, "scarico": barre_usate_per_conferma}
            st.session_state["1d_confermato"] = False
            st.rerun()

    with col_right:
        if st.session_state.results_1d:
            res = st.session_state.results_1d
            if not st.session_state["1d_confermato"]:
                st.warning("⚠️ SIMULAZIONE MULTI-MATERIALE")
                if st.button(T["conferma_stock"], key="btn_conf_1d"):
                    # Logica di scarico/carico reale
                    df_stk_attuale = st.session_state.magazzino_1d.copy()
                    for item in res["scarico"]:
                        idx = df_stk_attuale[(df_stk_attuale["CODICE MATERIALE"] == item["CODICE"]) & (df_stk_attuale["LUNGHEZZA (mm)"] == item["LUNGHEZZA"])].index
                        if len(idx) > 0:
                            df_stk_attuale.loc[idx[0], "QTY"] = max(0, df_stk_attuale.loc[idx[0], "QTY"] - 1)
                    
                    if res["scarti"]:
                        df_stk_attuale = pd.concat([df_stk_attuale, pd.DataFrame(res["scarti"])], ignore_index=True)
                    
                    st.session_state.magazzino_1d = df_stk_attuale
                    st.session_state["1d_confermato"] = True
                    st.rerun()
            
            for idx, b in enumerate(res["piani"]):
                sfrido_f = int(b["spazio_rimasto"] + spessore_taglio)
                html_segmenti = "".join([f'<div class="bar-segment" style="width:{(t / b["lunghezza_totale"]) * 100}%; background-color:{HEX_COLORI.get(str(t), HEX_COLORI["default"])};">{t}</div>' for t in b["tagli"]])
                st.markdown(f'<div class="bar-container"><div class="bar-header"><div>[ {b["codice"]} ] BARRA {idx+1} ({b["lunghezza_totale"]}mm)</div><div>SFRIDO: {sfrido_f}mm</div></div><div class="bar-track">{html_segmenti}</div></div>', unsafe_allow_html=True)
            
            df_exp = pd.DataFrame([{"ID_Barra": f"BAR-{i+1}", "Codice_Materiale": b["codice"], "Lunghezza_Totale_mm": b["lunghezza_totale"], "Sequenza_Tagli": "-".join(map(str, b["tagli"])), "Sfrido_Residuo_mm": int(b["spazio_rimasto"]+spessore_taglio)} for i, b in enumerate(res["piani"])])
            c1, c2 = st.columns(2)
            c1.download_button("📥 SCARICA REPORT CSV", make_pure_csv(df_exp), "Nesting_Barre_MultiCodice.csv")
            c2.download_button("📊 SCARICA REPORT EXCEL", make_real_excel(df_exp), "Nesting_Barre_MultiCodice.xlsx")

# =============================================================================
# SEZIONE 2D - LAMIERE MULTI-CODICE
# =============================================================================
with tab_2d:
    col2_left, col2_right = st.columns([1, 2])
    with col2_left:
        st.markdown(f"### {T['commessa']}")
        num_ordine_2d = st.text_input(T["ordine"], value="ORD-2D-MULTI", key="num_2d")
        nome_cliente_2d = st.text_input(T["cliente"], value="Laser Tech Srl", key="cli_2d")
        
        st.markdown(f"### {T['magazzino']}")
        tabella_stk_2d = st.data_editor(st.session_state.magazzino_2d, num_rows="dynamic", key="stk_ed_2d", use_container_width=True)
        st.session_state.magazzino_2d = tabella_stk_2d
        
        st.markdown(f"### {T['header_2d']}")
        bordo_lamiera = st.number_input(T["bordo"], value=20, step=5, key="bordo_2d")
        dist_sicurezza = st.number_input("DISTANZA TRA I PEZZI (mm)", value=15.0, step=2.0, key="dist_2d")
        
        st.markdown("### 🛠️ CARICAMENTO DXF REALE ORIGINALE")
        file_dxf_caricati = st.file_uploader("Trascina qui i tuoi veri file geometrici .dxf", type=["dxf"], accept_multiple_files=True, key="dxf_net_2d")
        
        w_rilevata, h_rilevata = 500, 300
        nome_file_componente = "PIASTRA_DI_BASE.DXF"
        
        if file_dxf_caricati:
            file_attivo = file_dxf_caricati[-1]
            nome_file_componente = file_attivo.name
            bytes_dxf = file_attivo.getvalue()
            _, w_cad, h_cad = parse_uploaded_dxf(bytes_dxf)
            if w_cad and h_cad:
                w_rilevata, h_rilevata = w_cad, h_cad
                st.success(f"✔️ Geometria DXF Rilevata: {w_rilevata} x {h_rilevata} mm")
            else:
                st.error("⚠️ Errore lettura geometrica standard. Sagoma generica applicata.")
            
            # Pre-popoliamo la tabella legando il pezzo al primo codice disponibile in magazzino
            codice_predefinito = str(tabella_stk_2d.iloc[0]["CODICE MATERIALE"]) if not tabella_stk_2d.empty else "L_FE_6MM"
            st.session_state.pezzi_2d = pd.DataFrame([{
                "NOME PEZZO DXF": nome_file_componente, 
                "CODICE RICHIESTO": codice_predefinito,
                "QTY DA PRODURRE": 6, 
                "LARGHEZZA (mm)": w_rilevata, 
                "ALTEZZA (mm)": h_rilevata
            }])
            
        tabella_pezzi_2d = st.data_editor(st.session_state.pezzi_2d, num_rows="dynamic", key="edit_pezzi_2d", use_container_width=True)
        st.session_state.pezzi_2d = tabella_pezzi_2d
        
        if st.button(T["esegui"], type="primary", key="run_2d"):
            piani_piazzati = []
            lastre_usate_report = []
            
            # Eseguiamo il nesting separando per ogni riga/codice inserito dall'utente
            for idx_riga, riga_pezzo in tabella_pezzi_2d.iterrows():
                if pd.isnull(riga_pezzo["CODICE RICHIESTO"]) or pd.isnull(riga_pezzo["QTY DA PRODURRE"]): continue
                
                cod_mat_richiesto = str(riga_pezzo["CODICE RICHIESTO"]).strip()
                qty_da_fare = int(riga_pezzo["QTY DA PRODURRE"])
                w_p = float(riga_pezzo["LARGHEZZA (mm)"])
                h_p = float(riga_pezzo["ALTEZZA (mm)"])
                
                # Trova la prima lastra compatibile con questo codice nel magazzino
                lastra_selezionata = None
                for _, l_row in tabella_stk_2d.iterrows():
                    if str(l_row["CODICE MATERIALE"]).strip() == cod_mat_richiesto and int(l_row["QTY"]) > 0:
                        lastra_selezionata = l_row
                        break
                
                # Se non trova la lastra, usa dimensioni standard di fallback
                W_l = float(lastra_selezionata["LARGHEZZA X (mm)"]) if lastra_selezionata is not None else 3000.0
                H_l = float(lastra_selezionata["ALTEZZA Y (mm)"]) if lastra_selezionata is not None else 1500.0
                
                # Piazzamento a griglia sulla lastra individuata
                x_step = w_p + dist_sicurezza
                y_step = h_p + dist_sicurezza
                pezzi_messi = 0
                x_cursor = bordo_lamiera
                
                while x_cursor + w_p <= W_l - bordo_lamiera and pezzi_messi < qty_da_fare:
                    y_cursor = bordo_lamiera
                    while y_cursor + h_p <= H_l - bordo_lamiera and pezzi_messi < qty_da_fare:
                        piani_piazzati.append({
                            "id": f"P-{cod_mat_richiesto}-{pezzi_messi+1}",
                            "codice": cod_mat_richiesto,
                            "traslazione": (x_cursor, y_cursor),
                            "dim_w": w_p,
                            "dim_h": h_p,
                            "W_lastra": W_l,
                            "H_lastra": H_l,
                            "color": "#1E3A8A" if "FE" in cod_mat_richiesto else "#065F46"
                        })
                        pezzi_messi += 1
                        y_cursor += y_step
                    x_cursor += x_step
                
                lastre_usate_report.append({
                    "CODICE": cod_mat_richiesto, 
                    "W": W_l, "H": H_l, 
                    "PEZZI_PRODOTTI": pezzi_messi,
                    "RICHIESTI": qty_da_fare
                })
            
            st.session_state.results_2d = {"piazzamenti": piani_piazzati, "report_lastre": lastre_usate_report}
            st.session_state["2d_confermato"] = False
            st.rerun()

    with col2_right:
        if st.session_state.results_2d:
            res2d = st.session_state.results_2d
            
            if not st.session_state["2d_confermato"]:
                st.warning("⚠️ SIMULAZIONE DISPOSIZIONE LAMIERE")
                if st.button(T["conferma_stock"], key="btn_conf_2d"):
                    # Scarica reali lamiere
                    df_stk_2d_attuale = st.session_state.magazzino_2d.copy()
                    for l_usata in res2d["report_lastre"]:
                        if l_usata["PEZZI_PRODOTTI"] > 0:
                            idx = df_stk_2d_attuale[df_stk_2d_attuale["CODICE MATERIALE"] == l_usata["CODICE"]].index
                            if len(idx) > 0:
                                df_stk_2d_attuale.loc[idx[0], "QTY"] = max(0, df_stk_2d_attuale.loc[idx[0], "QTY"] - 1)
                    st.session_state.magazzino_2d = df_stk_2d_attuale
                    st.session_state["2d_confermato"] = True
                    st.rerun()
            else:
                st.success(T["stock_appllicato"])
            
            # Rappresentazione Grafica di ciascuna lastra elaborata
            for l_rep in res2d["report_lastre"]:
                st.markdown(f"#### Lastra Codice: **{l_rep['CODICE']}** ({l_rep['W']}x{l_rep['H']} mm) — Piazzati {l_rep['PEZZI_PRODOTTI']}/{l_rep['RICHIESTI']} pezzi")
                
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.set_facecolor('#0F0F11'); fig.patch.set_facecolor('#1A1A1A')
                ax.add_patch(patches.Rectangle((0, 0), l_rep['W'], l_rep['H'], fill=False, color="#FF5722", linewidth=2))
                
                # Filtra e disegna solo i rettangoli appartenenti a questa specifica lastra/codice
                for p in res2d["piazzamenti"]:
                    if p["codice"] == l_rep["CODICE"]:
                        tx, ty = p["traslazione"]
                        ax.add_patch(patches.Rectangle((tx, ty), p["dim_w"], p["dim_h"], facecolor=p["color"], edgecolor="#FFF", alpha=0.7))
                        ax.text(tx + p["dim_w"]/2, ty + p["dim_h"]/2, p["id"].split('-')[-1], color="white", fontsize=8, ha='center', va='center')
                
                ax.set_xlim(-50, l_rep['W'] + 50); ax.set_ylim(-50, l_rep['H'] + 50)
                ax.set_aspect('equal'); ax.axis('off')
                st.pyplot(fig)
                plt.close(fig)
