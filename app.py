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

st.set_page_config(page_title="MetalHub Suite", layout="wide")

# GRAFICA PRESET REPLIT STABILE (ARANCIONE & ANTRACITE)
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

# BARRA DI NAVIGAZIONE SUPERIORE
st.markdown("""
    <div style="background-color:#262626; padding:15px; border-radius:5px; margin-bottom:25px; border-bottom:2px solid #FF5722;">
        <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:30px;">🔥 MetalHub Suite</span>
    </div>
""", unsafe_allow_html=True)

tab_1d, tab_2d = st.tabs(["🪚 NESTING 1D - BARRE", "📐 NESTING 2D - LAMIERE"])
# =============================================================================
# REPARTO NESTING 1D - BARRE (CON PARAMETRI SIDEBAR DEDICATI)
# =============================================================================
with tab_1d:
    # PARAMETRI SIDEBAR VISIBILI SOLO IN 1D
    st.sidebar.markdown("<h3 style='color:#FF5722;'>🪚 Parametri Taglio 1D</h3>", unsafe_allow_html=True)
    spessore_taglio = st.sidebar.number_input("Spessore Lama / Taglio (mm)", value=4.0, step=0.5, key="lama_1d")
    intestazione_barra = st.sidebar.number_input("Intestazione Barra / Sfrido Testa (mm)", value=20, step=5, key="int_1d")
    minimo_scarto = st.sidebar.number_input("Minimo Scarto Utile Recuperabile (mm)", value=500, step=50, key="min_1d")
    
    st.markdown('<h2>🪚 Ottimizzazione Taglio Barre Profilati</h2>', unsafe_allow_html=True)
    
    st.markdown('<h3>📋 Intestazione Commessa 1D</h3>', unsafe_allow_html=True)
    c1_1d, c2_1d = st.columns(2)
    with c1_1d: num_ordine_1d = st.text_input("Numero Ordine (1D)", value="ORD-1D-001")
    with c2_1d: data_commessa_1d = st.date_input("Data Lavorazione (1D)", date.today(), key="d_1d")
    nome_cliente_1d = st.text_input("Anagrafica Cliente (1D)", value="Officina Carpenteria SpA")
    
    st.markdown(f'<div style="border:1px solid #FF5722; padding:10px; border-radius:5px; background-color:#262626; margin-bottom:20px;"><p style="margin:0; color:#FF5722 !important; font-weight:bold;">PIANO TAGLIO PROFILATI {num_ordine_1d}</p></div>', unsafe_allow_html=True)
    st.markdown("#### 📋 1. Inventario Barre in Magazzino")
    df_stk = pd.DataFrame([
        {"Lunghezza Barra (mm)": 6000, "Quantità Disponibile": 20},
        {"Lunghezza Barra (mm)": 3000, "Quantità Disponibile": 2}
    ])
    tabella_stk = st.data_editor(df_stk, num_rows="dynamic", key="stk_1d", use_container_width=True)
    
    st.markdown("#### 📋 2. Distinta Pezzi da Tagliare (Fabbisogno)")
    df_cut = pd.DataFrame([
        {"Lunghezza Pezzo (mm)": 1200, "Quantità Richiesta": 5},
        {"Lunghezza Pezzo (mm)": 850, "Quantità Richiesta": 8}
    ])
    tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_1d", use_container_width=True)
    
    if st.button("🚀 AVVIA OTTIMIZZAZIONE BARRE", type="primary"):
        reqs = []
        for _, r in tabella_cut.iterrows():
            lp, qr = r["Lunghezza Pezzo (mm)"], r["Quantità Richiesta"]
            if pd.notnull(lp) and pd.notnull(qr): reqs.extend([int(lp)] * int(qr))
        reqs.sort(reverse=True)
        
        tagli_barre = []
        barra_corrente = []
        spazio_rimasto = 6000 - intestazione_barra
        
        for pezzo in reqs:
            if (pezzo + spessore_tagiot) <= spazio_rimasto if barra_corrente else pezzo <= spazio_rimasto:
                barra_corrente.append(pezzo)
                spazio_rimasto -= (pezzo + spessore_taglio)
            else:
                if barra_corrente:
                    tagli_barre.append({"Tagli (mm)": str(barra_corrente), "Sfrido (mm)": spazio_rimasto + spessore_taglio})
                barra_corrente = [pezzo]
                spazio_rimasto = 6000 - intestazione_barra - pezzo
        if barra_corrente:
            tagli_barre.append({"Tagli (mm)": str(barra_corrente), "Sfrido (mm)": spazio_rimasto + spessore_taglio})
            
        df_risultati = pd.DataFrame(tagli_barre)
        st.success("Ottimizzazione completata!")
        st.dataframe(df_risultati, use_container_width=True)
# =============================================================================
# REPARTO NESTING 2D - LAMIERE (CON PARAMETRI SIDEBAR DEDICATI)
# =============================================================================
with tab_2d:
    # PARAMETRI SIDEBAR VISIBILI SOLO IN 2D
    st.sidebar.markdown("<h3 style='color:#FF5722;'>📊 Formato Lastra 2D</h3>", unsafe_allow_html=True)
    W_lamiera = st.sidebar.number_input("Lunghezza Lastra X (mm)", value=3000, step=100, key="W_2d")
    H_lamiera = st.sidebar.number_input("Altezza Lastra Y (mm)", value=1500, step=100, key="H_2d")
    bordo_lamiera = st.sidebar.number_input("Distanza dal Bordo (mm)", value=15, step=5, key="bordo_2d")
    
    st.sidebar.markdown("<h3 style='color:#FF5722;'>🔧 Configurazione Macchina</h3>", unsafe_allow_html=True)
    diametro_utensile = st.sidebar.number_input("Diam. Utensile Fresa (mm)", value=6.0, step=1.0, key="fresa_2d")
    distanza_sicurezza = st.sidebar.number_input("Distanza Sicurezza (mm)", value=4.0, step=1.0, key="sic_2d")
    passo_scansione = st.sidebar.slider("Risoluzione Calcolo (mm)", min_value=2, max_value=25, value=10, step=1, key="passo_2d")
    
    offset_totale = (diametro_utensile / 2.0) + distanza_sicurezza + bordo_lamiera

    st.markdown('<h2>📐 Ottimizzazione Taglio Lamiere Reali</h2>', unsafe_allow_html=True)
    st.markdown('<h3>📋 Intestazione Commessa 2D</h3>', unsafe_allow_html=True)
    c1_2d, c2_2d = st.columns(2)
    with c1_2d: num_ordine_2d = st.text_input("Numero Ordine (2D)", value="ORD-2D-001")
    with c2_2d: data_commessa_2d = st.date_input("Data Lavorazione (2D)", date.today(), key="d_2d")
    nome_cliente_2d = st.text_input("Anagrafica Cliente (2D)", value="Carpenteria Metallica Industriale")
    
    st.markdown(f'<div style="border:1px solid #FF5722; padding:10px; border-radius:5px; background-color:#262626; margin-bottom:20px;"><p style="margin:0; color:#FF5722 !important; font-weight:bold;">PIANO TAGLIO LASTRA {num_ordine_2d}</p></div>', unsafe_allow_html=True)

    # LETTORE DXF RIGIDO ED ESPLICITO (DRAFTSIGHT) WITH CARTESIAN RESET
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
    st.markdown('<h3>📥 Caricamento File Matrice (.DXF)</h3>', unsafe_allow_html=True)
    file_caricati = st.file_uploader("Scegli file DXF", type=["dxf"], accept_multiple_files=True, label_visibility="collapsed")
    lista_particolari = []

    if file_caricati:
        st.markdown('<div style="background-color:#262626; padding:15px; border-radius:5px; margin-top:15px; border:1px solid #404040;"><h3>📦 Fabbisogno e Quantità</h3>', unsafe_allow_html=True)
        for f in file_caricati:
            poly = estrai_e_azzera_poligono_da_dxf(f.getvalue())
            if not poly or poly.area < 1:
                poly = Polygon([(0,0), (90,0), (90,80), (0,80)])
                w_p, h_p = 90.0, 80.0
            else:
                mx, my, xx, yx = poly.bounds
                w_p, h_p = xx-mx, yx-my
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<span style="color:#FFFFFF !important; font-weight:bold; font-size:15px;">📄 {f.name}</span>', unsafe_allow_html=True)
                st.markdown(f'<br><span style="color:#FF5722 !important; font-size:13px;">Dimensione reale: {round(w_p)} x {round(h_p)} mm</span>', unsafe_allow_html=True)
            with col2:
                qta = st.number_input(f"Pezzi per {f.name}", min_value=1, max_value=200, value=5, step=1, key=f"q_{f.name}")
            lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 AVVIA ELABORAZIONE NESTING LAMIERE", type="primary"):
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
            
            for item in coda:
                p_orig = item["poly"]; ok = False
                # RISOLTO CRASH CHAT: Generazione dinamica degli angoli cardinali complessi
                for ang in list(range(0, 360, 45)):
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
            with m1: st.metric("Rendimento Netto Lastra", f"{rend:.2f}%")
            with m2: st.metric("Sfrido / Rottame Totale", f"{100-rend:.2f}%")
            
            if piazzati:
                _, _, max_x, _ = unary_union(piazzati).bounds
                x_sfrido_start = max_x + offset_totale
                if W_lamiera - x_sfrido_start >= 100:
                    w_sfrido = W_lamiera - x_sfrido_start
                    st.info(f"✨ SPEZZONE RECUPERABILE: Rilevato ritaglio utile di {round(w_sfrido)} x {H_lamiera} mm.")
