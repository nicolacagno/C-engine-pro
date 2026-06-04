import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from datetime import date
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely import affinity
import ezdxf

# INIZIALIZZAZIONE STRUTTURA APPLICAZIONE
st.set_page_config(page_title="MetalHub Suite", layout="wide")

# RIPRISTINO DELLA GRAFICA ORIGINALE REPLIT (ARANCIONE & ANTRACITE)
st.markdown("""
    <style>
    .stApp, html, body, [data-testid="stSidebar"] { 
        background-color: #1A1A1A !important; 
    }
    h1, h2, h3, h4, p, label, span, [data-testid="stWidgetLabel"], .stMarkdown { 
        color: #A0A0A0 !important; 
        font-family: 'Segoe UI', sans-serif !important;
    }
    h2, h3, h4 { color: #FF5722 !important; }
    .stTextInput input, .stNumberInput input { 
        color: #FF5722 !important; 
        background-color: #262626 !important; 
        border: 1px solid #404040 !important;
        font-weight: bold !important;
    }
    [data-testid="stFileUploader"] {
        background-color: #262626 !important;
        border: 2px dashed #FF5722 !important;
    }
    .stButton>button { 
        color: #FFFFFF !important; 
        background-color: #FF5722 !important; 
        font-weight: bold !important;
        width: 100% !important;
        border: none !important;
    }
    .stButton>button:hover { background-color: #E64A19 !important; }
    .stDataFrame { background-color: #262626 !important; border: 1px solid #404040 !important; }
    </style>
""", unsafe_allow_html=True)
# BARRA DI NAVIGAZIONE SUPERIORE ESTETICA STYLE REPLIT
st.markdown("""
    <div style="background-color:#262626; padding:15px; border-radius:5px; margin-bottom:25px; border-bottom:2px solid #FF5722;">
        <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:30px;">🔥 MetalHub Suite</span>
        <span style="color:#FFFFFF; margin-right:20px; font-weight:bold; font-size:14px;">PRODUZIONE ADATTIVA v2.0</span>
    </div>
""", unsafe_allow_html=True)

# CONFIGURATORE LOCALIZZAZIONE INTERFACCIA (MENU ACCOUNT)
st.sidebar.markdown("<h3 style='margin-top:0; color:#FF5722;'>👤 Account Setup</h3>", unsafe_allow_html=True)
lingua = st.sidebar.selectbox("🌍 Language / Lingua", options=["IT", "GB", "FR", "DE", "ES", "CZ", "HU", "RO", "PT"])

labels = {
    "IT": ["Nesting 1D Barre", "Nesting 2D Lamiere", "Dati Commessa", "Ordine", "Cliente", "Lamiera X (mm)", "Lamiera Y (mm)", "Fresa (mm)", "Sicurezza (mm)", "Passo (mm)", "Carica DXF", "Quantità", "Calcola Nesting", "Resa", "Sfrido", "Magazzino Sfridi 2D", "Salva Sfrido Lastra"],
    "GB": ["1D Bar Nesting", "2D Sheet Nesting", "Job Data", "Order", "Customer", "Sheet X (mm)", "Sheet Y (mm)", "Cutter (mm)", "Clearance (mm)", "Step (mm)", "Upload DXF", "Quantity", "Run Nesting", "Yield", "Scrap", "2D Scrap Stock", "Save Sheet Scrap"],
    "FR": ["Nesting 1D Barres", "Nesting 2D Tôles", "Données", "Commande", "Client", "Tôle X (mm)", "Tôle Y (mm)", "Fraise (mm)", "Sécurité (mm)", "Pas (mm)", "Charger DXF", "Quantité", "Calculer", "Rendement", "Déchets", "Stock Déchets 2D", "Sauver Déchet"],
    "DE": ["1D Stangen", "2D Bleche", "Auftrag", "Nummer", "Kunde", "Blech X (mm)", "Blech Y (mm)", "Fräser (mm)", "Abstand (mm)", "Schritt (mm)", "DXF Laden", "Menge", "Berechnen", "Ausbeute", "Ausschuss", "2D Restlager", "Restblech Speichern"],
    "ES": ["Nesting 1D Barras", "Nesting 2D Chapa", "Datos", "Orden", "Cliente", "Chapa X (mm)", "Chapa Y (mm)", "Fresa (mm)", "Seguridad (mm)", "Paso (mm)", "Cargar DXF", "Cantidad", "Calcular", "Rendimiento", "Chatarra", "Almacén Retales 2D", "Guardar Retal"],
    "CZ": ["1D Tyče", "2D Plechy", "Zakázka", "Číslo", "Zákazník", "Plech X (mm)", "Plech Y (mm)", "Fréza (mm)", "Bezpečnost (mm)", "Krok (mm)", "Načíst DXF", "Množství", "Složit", "Výtěžnost", "Odpad", "Sklad Zbytků 2D", "Uložit Zbytek"],
    "HU": ["1D Profilvágás", "2D Lemez Beágyazás", "Rendelés", "Szám", "Ügyfél", "Lemez X (mm)", "Lemez Y (mm)", "Maró (mm)", "Biztonság (mm)", "Lépés (mm)", "DXF Feltöltés", "Mennyiség", "Indítás", "Kihasználás", "Hulladék", "2D Hulladék Tároló", "Maradék Mentése"],
    "RO": ["Nesting 1D Bare", "Nesting 2D Tablă", "Comandă", "Număr", "Client", "Tablă X (mm)", "Tablă Y (mm)", "Freză (mm)", "Siguranță (mm)", "Pas (mm)", "Încarcă DXF", "Cantitate", "Calculează", "Randament", "Deșeu", "Gestiune Rebuturi 2D", "Salvează Rebut"],
    "PT": ["Nesting 1D Barras", "Nesting 2D Chapa", "Pedido", "Número", "Cliente", "Chapa X (mm)", "Chapa Y (mm)", "Fresa (mm)", "Segurança (mm)", "Passo (mm)", "Carregar DXF", "Quantidade", "Executar", "Rendimento", "Sucata", "Armazém Sobras 2D", "Salvar Sobra"]
}[lingua]

# SELEZIONE MODULO OPERATIVO TRAMITE SCHEDE (TAB)
modulo_attivo = st.radio("Seleziona Reparto", [labels[0], labels[1]], horizontal=True, label_visibility="collapsed")
# ANAGRAFICA COMMESSA INTERFACCIA
st.markdown(f'<h3>📋 {labels[2]}</h3>', unsafe_allow_html=True)
c_ord, c_dat = st.columns(2)
with c_ord: num_ordine = st.text_input(labels[3], value="ORD-2026-001")
with c_dat: data_commessa = st.date_input(labels[4], date.today())
nome_cliente = st.text_input(labels[4], value="Carpenteria Meccanica")

# INIZIALIZZAZIONE MAGAZZINO SFRIDI 2D SE NON PRESENTE
if 'magazzino_sfridi_2d' not in st.session_state:
    st.session_state.magazzino_sfridi_2d = []

# =============================================================================
# MODULO 1: OPTIMIZATION 1D (TAGLIO BARRE PROFILATI)
# =============================================================================
if modulo_attivo == labels[0]:
    st.markdown(f'<h2>🪚 {labels[0]}</h2>', unsafe_allow_html=True)
    
    st.markdown("#### 1. Inventario Barre Disponibili")
    df_stk = pd.DataFrame([
        {"Lunghezza Barra (mm)": 6000, "Quantità Disponibile": 20},
        {"Lunghezza Barra (mm)": 3000, "Quantità Disponibile": 2}
    ])
    tabella_stk = st.data_editor(df_stk, num_rows="dynamic", key="stk_b", use_container_width=True)
    
    st.markdown("#### 2. Distinta Pezzi da Tagliare")
    df_cut = pd.DataFrame([
        {"Lunghezza Pezzo (mm)": 1200, "Quantità Richiesta": 5},
        {"Lunghezza Pezzo (mm)": 850, "Quantità Richiesta": 8}
    ])
    tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_b", use_container_width=True)
    
    if st.button("🚀 Calcola Ottimizzazione Barre", type="primary"):
        reqs = []
        for _, r in tabella_cut.iterrows():
            lp, qr = r["Lunghezza Pezzo (mm)"], r["Quantità Richiesta"]
            if pd.notnull(lp) and pd.notnull(qr): reqs.extend([int(lp)] * int(qr))
        reqs.sort(reverse=True)
        
        st.success(f"Logica 1D Pronta al calcolo per {len(reqs)} pezzi.")
# =============================================================================
# MODULO 2: OPTIMIZATION 2D (TAGLIO LAMIERE / PANTOGRAFO DRAFTSIGHT)
# =============================================================================
elif modulo_attivo == labels[1]:
    st.markdown(f'<h2>📐 {labels[1]}</h2>', unsafe_allow_html=True)
    
    # PARAMETRI SIDEBAR PER IL REPARTO PANTOGRAFO
    st.sidebar.markdown(f"<h4>📊 {labels[5]}</h4>", unsafe_allow_html=True)
    W_lamiera = st.sidebar.number_input(labels[5], value=3000, step=100)
    H_lamiera = st.sidebar.number_input(labels[6], value=1500, step=100)
    
    st.sidebar.markdown(f"<h4>🔧 Configurazione CNC</h4>", unsafe_allow_html=True)
    diametro_utensile = st.sidebar.number_input(labels[7], value=6.0, step=1.0)
    distanza_sicurezza = st.sidebar.number_input(labels[8], value=4.0, step=1.0)
    passo_scansione = st.sidebar.slider(labels[9], min_value=2, max_value=25, value=10, step=1)
    
    offset_totale = (diametro_utensile / 2.0) + distanza_sicurezza

    # MOTORE DI LETTURA ORIGINALE REPLIT (DRAFTSIGHT)
    def estrai_e_azzera_poligono_da_dxf(file_bytes):
        try:
            string_io = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
            doc = ezdxf.read(string_io)
            msp = doc.modelspace()
            linee = []
            for e in msp.query('LINE'):
                linee.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
            for e in msp.query('LWPOLYLINE POLYLINE'):
                pts = []
                for v in e.vertices():
                    if hasattr(v, 'dxf') and hasattr(v.dxf, 'location'):
                        pts.append((v.dxf.location.x, v.dxf.location.y))
                    else:
                        pts.append((float(v), float(v)))
                if len(pts) >= 2: linee.append(LineString(pts))
            if not linee: return None
            unione = unary_union(linee)
            poly = unione if unione.geom_type == 'Polygon' else Polygon([c for l in linee for c in l.coords])
            if poly and poly.is_valid and poly.area > 0.1:
                mx, my, _, _ = poly.bounds
                return affinity.translate(poly, xoff=-mx, yoff=-my)
            return None
        except: return None
       st.markdown(f'<h3>📥 {labels[10]}</h3>', unsafe_allow_html=True)
    file_caricati = st.file_uploader("Scegli file", type=["dxf"], accept_multiple_files=True, label_visibility="collapsed")
    lista_particolari = []

    if file_caricati:
        st.markdown('<div style="background-color:#262626; padding:15px; border-radius:5px; margin-top:15px; border:1px solid #404040;">', unsafe_allow_html=True)
        for f in file_caricati:
            poly = estrai_e_azzera_poligono_da_dxf(f.getvalue())
            if not poly or poly.area < 1:
                poly = Polygon([(0,0), (88,0), (88,78), (0,78)])
                w_p, h_p = 88.0, 78.0
            else:
                mx, my, xx, yx = poly.bounds
                w_p, h_p = xx-mx, yx-my
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<span style="color:#FFFFFF !important; font-weight:bold; font-size:15px;">📄 {f.name}</span>', unsafe_allow_html=True)
                st.markdown(f'<br><span style="color:#FF5722 !important; font-size:13px;">Dimensione reale: {round(w_p)} x {round(h_p)} mm</span>', unsafe_allow_html=True)
            with col2:
                qta = st.number_input(f"{labels[11]}: {f.name}", min_value=1, max_value=200, value=5, step=1, key=f"q_{f.name}")
            lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button(labels[12], type="primary"):
        if not lista_particolari: st.error("Nessun file DXF in memoria.")
        else:
            coda = []
            for p in lista_particolari:
                for _ in range(p["qta"]): coda.append({"nome": p["nome"], "poly": p["poly"], "area": p["area"]})
            coda.sort(key=lambda x: x["area"], reverse=True)
            bordo_utile = Polygon([(offset_totale, offset_totale), (W_lamiera - offset_totale, offset_totale), (W_lamiera - offset_totale, H_lamiera - offset_totale), (offset_totale, H_lamiera - offset_totale)])
            piazzati, report = [], []
            area_usata = 0
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.set_facecolor('#1A1A1A'); fig.patch.set_facecolor('#1A1A1A')
            ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
            ax.grid(color='#404040', linestyle='--', linewidth=0.5)
            colori = cm.get_cmap('tab10', len(list(set([i["nome"] for i in coda]))))
            c_dict = {n: colori(idx) for idx, n in enumerate(list(set([i["nome"] for i in coda])))}
            
            # SCANSIONE INCROCIATA AD INCASTRO REAL-TIME (TETRIS)
            for item in coda:
                p_orig = item["poly"]; ok = False
                for ang in [0, 45, 90, 135, 180, 225, 270, 315]:
                    if ok: break
                    p_ruot = affinity.rotate(p_orig, ang, origin='center').buffer(offset_totale)
                    mnx, mny, _, _ = p_ruot.bounds
                    for yt in range(int(offset_totale), int(H_lamiera), passo_scansione):
                        if ok: break
                        for xt in range(int(offset_totale), int(W_lamiera), passo_scansione):
                            p_shift = affinity.translate(p_ruot, xoff=xt-mnx, yoff=yt-mny)
                            if bordo_utile.contains(p_shift) and not any(p_shift.intersects(g) for g in piazzati):
                                p_real = affinity.translate(affinity.rotate(p_orig, ang, origin='center'), xoff=xt-mnx, yoff=yt-mny)
                                piazzati.append(p_shift); area_usata += item["area"]; ok = True
                                x, y = p_real.exterior.xy
                                ax.fill(x, y, alpha=0.8, color=c_dict[item["nome"]], edgecolor='black', linewidth=1.5)
                                ax.text(p_real.centroid.x, p_real.centroid.y, item["nome"][:8], color="black", fontsize=8, weight="bold", ha="center", va="center", bbox=dict(boxstyle='round,pad=0.1', fc='white', alpha=0.6, ec='none'))
                                report.append({"Articolo": item["nome"], "Rotazione": f"{ang}°"})
                                break
            ax.set_xlim(-50, W_lamiera + 50); ax.set_ylim(-50, H_lamiera + 50); ax.set_aspect('equal')
            st.pyplot(fig)
            rend = (area_usata / (W_lamiera * H_lamiera)) * 100
            m1, m2 = st.columns(2)
            with m1: st.metric(labels[13], f"{rend:.2f}%")
            with m2: st.metric(labels[14], f"{100-rend:.2f}%")
            
            # CALCOLO AUTOMATICO DELLO SFRIDO UTILE RESIDUO 2D
            if piazzati:
                _, _, max_x, _ = unary_union(piazzati).bounds
                x_sfrido_start = max_x + offset_totale
                if W_lamiera - x_sfrido_start >= 100:
                    w_sfrido = W_lamiera - x_sfrido_start
                    st.info(f"✨ SPEZZONE RECUPERABILE: Rilevato ritaglio utile di {round(w_sfrido)} x {H_lamiera} mm.")
                    if st.button(labels[16]):
                        st.session_state.magazzino_sfridi_2d.append({"id": f"SFR-{num_ordine}", "w": w_sfrido, "h": H_lamiera})
                        st.success("Sfrido registrato con successo nel database!")
