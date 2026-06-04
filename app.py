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
        <span style="color:#FFFFFF; margin-right:20px; font-weight:bold; font-size:14px; border-bottom:2px solid #FF5722; padding-bottom:5px;">NESTING 2D · OFFICINA</span>
    </div>
""", unsafe_allow_html=True)

# SEZIONE INTESTAZIONE COMMESSA
st.markdown('<h3>📋 Intestazione Commessa</h3>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1: num_ordine = st.text_input("Numero Ordine", value="ORD-2D-001")
with c2: data_commessa = st.date_input("Data Lavorazione", date.today())
nome_cliente = st.text_input("Anagrafica Cliente", value="Carpenteria Metallica Industriale")

st.markdown(f'<div style="border:1px solid #FF5722; padding:10px; border-radius:5px; background-color:#262626; margin-bottom:20px;"><p style="margin:0; color:#FF5722 !important; font-weight:bold;">PIANO TAGLIO LASTRA {num_ordine} - {data_commessa.strftime("%d/%m/%Y")}</p></div>', unsafe_allow_html=True)

# PARAMETRI FOGLIO LAMIERE E CONFIGURAZIONE MACCHINA
st.sidebar.markdown("<h3 style='color:#FF5722;'>📊 Formato Lamiera</h3>", unsafe_allow_html=True)
W_lamiera = st.sidebar.number_input("Larghezza Lastra X (mm)", value=3000, step=100)
H_lamiera = st.sidebar.number_input("Altezza Lastra Y (mm)", value=1500, step=100)
bordo_lamiera = st.sidebar.number_input("Distanza dal Bordo (mm)", value=15, step=5)

st.sidebar.markdown("<h3 style='color:#FF5722;'>🔧 Configurazione Macchina</h3>", unsafe_allow_html=True)
diametro_utensile = st.sidebar.number_input("Diam. Utensile Fresa (mm)", value=6.0, step=1.0)
distanza_sicurezza = st.sidebar.number_input("Distanza Sicurezza Pezzi (mm)", value=4.0, step=1.0)
passo_scansione = st.sidebar.slider("Risoluzione Calcolo (mm)", min_value=2, max_value=25, value=10, step=1)

offset_totale = (diametro_utensile / 2.0) + distanza_sicurezza + bordo_lamiera

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

# CARICAMENTO FILE E SEZIONE QUANTITÀ
st.markdown('<h3>📥 Caricamento File Matrice (.DXF)</h3>', unsafe_allow_html=True)
file_caricati = st.file_uploader("Scegli file DXF", type=["dxf"], accept_multiple_files=True, label_visibility="collapsed")
lista_particolari = []

if file_caricati:
    st.markdown('<div style="background-color:#262626; padding:15px; border-radius:5px; margin-top:15px; border:1px solid #404040;"><h3>📦 Fabbisogno e Quantità</h3>', unsafe_allow_html=True)
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
            qta = st.number_input(f"Pezzi: {f.name}", min_value=1, max_value=200, value=5, step=1, key=f"q_{f.name}")
        lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})
    st.markdown('</div>', unsafe_allow_html=True)

# CALCOLO E DISEGNO DEL NESTING TETRIS REAL-TIME
if st.button("🚀 AVVIA ELABORAZIONE NESTING", type="primary"):
    if not lista_particolari: 
        st.error("Nessun file DXF caricato nello slot.")
    else:
        coda = []
        for p in lista_particolari:
            for _ in range(p["qta"]): coda.append({"nome": p["nome"], "poly": p["poly"], "area": p["area"]})
        coda.sort(key=lambda x: x["area"], reverse=True)
        
        bordo_utile = Polygon([(offset_totale, offset_totale), (W_lamiera - offset_totale, offset_totale), (W_lamiera - offset_totale, H_lamiera - offset_totale), (offset_totale, H_lamiera - offset_totale)])
        piazzati, report = [], []
        area_usata = 0
        
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_facecolor('#1A1A1A')
        fig.patch.set_facecolor('#1A1A1A')
        ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
        ax.grid(color='#404040', linestyle='--', linewidth=0.5)
        
        colori = cm.get_cmap('tab10', len(list(set([i["nome"] for i in coda]))))
        c_dict = {n: colori(idx) for idx, n in enumerate(list(set([i["nome"] for i in coda])))}
        
        for item in coda:
            p_orig = item["poly"]
            ok = False
            
            # ELENCO ROTAZIONI INIETTATO IN LINEA (0, 45, 90, 135, 180, 225, 270, 315)
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
                            piazzati.append(p_shift)
                            area_usata += item["area"]
                            ok = True
                            x, y = p_real.exterior.xy
                            ax.fill(x, y, alpha=0.8, color=c_dict[item["nome"]], edgecolor='black', linewidth=1.5)
                            ax.text(p_real.centroid.x, p_real.centroid.y, item["nome"][:8], color="black", fontsize=8, weight="bold", ha="center", va="center", bbox=dict(boxstyle='round,pad=0.1', fc='white', alpha=0.6, ec='none'))
                            report.append({"Articolo": item["nome"], "Rotazione": f"{ang}°"})
                            break
                            
        ax.set_xlim(-50, W_lamiera + 50)
        ax.set_ylim(-50, H_lamiera + 50)
        ax.set_aspect('equal')
        st.pyplot(fig)
        
        rend = (area_usata / (W_lamiera * H_lamiera)) * 100
        m1, m2 = st.columns(2)
        with m1: st.metric("Rendimento Netto Lastra", f"{rend:.2f}%")
        with m2: st.metric("Sfrido / Rottame Totale", f"{100-rend:.2f}%")
        
        st.subheader("📋 Elenco Pezzi Mappati")
        df_rep = pd.DataFrame(report)
        st.dataframe(df_rep, use_container_width=True)
