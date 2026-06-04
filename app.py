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

st.set_page_config(page_title="C-Engine Pro", layout="wide")

# GRAFICA FULL DARK CNC COMPLETA
st.markdown("""
    <style>
    .stApp, html, body, [data-testid="stSidebar"] { 
        background-color: #0F172A !important; 
    }
    h1, h2, h3, h4, p, label, span, [data-testid="stWidgetLabel"], .stMarkdown { 
        color: #FFFFFF !important; 
        font-family: monospace !important;
    }
    .stTextInput input, .stNumberInput input { 
        color: #38BDF8 !important; 
        background-color: #1E293B !important; 
        border: 1px solid #475569 !important;
    }
    [data-testid="stFileUploader"] {
        background-color: #1E293B !important;
        border: 2px dashed #38BDF8 !important;
    }
    .industrial-card {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
    }
    .stButton>button { 
        color: #0F172A !important; 
        background-color: #38BDF8 !important; 
        font-weight: bold !important;
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)
# INTESTAZIONI E STRUTTURA DEL SITO
st.markdown('<div class="industrial-card"><h2>📐 MetalHub - Suite Nesting 2D</h2></div>', unsafe_allow_html=True)

st.markdown('<div class="industrial-card"><h3>📋 Dati Commessa</h3>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1: num_ordine = st.text_input("Codice Ordine", value="COMM-2026-001")
with c2: nome_cliente = st.text_input("Anagrafica Cliente", value="Officina SpA")
with c3: data_commessa = st.date_input("Data Lavorazione", date.today())
st.markdown('</div>', unsafe_allow_html=True)

# PARAMETRI DI CONFIGURAZIONE NELLA BARRA LATERALE
st.sidebar.markdown("<h3 style='color:#38BDF8;'>📊 Formato Lamiera</h3>", unsafe_allow_html=True)
W_lamiera = st.sidebar.number_input("Lunghezza Lastra X (mm)", value=1000, step=100)
H_lamiera = st.sidebar.number_input("Altezza Lastra Y (mm)", value=1000, step=100)

st.sidebar.markdown("<h3 style='color:#38BDF8;'>🔧 Parametri Macchina</h3>", unsafe_allow_html=True)
diametro_utensile = st.sidebar.number_input("Diametro Fresa / Canale (mm)", value=6.0, step=1.0)
distanza_sicurezza = st.sidebar.number_input("Sicurezza tra Pezzi (mm)", value=4.0, step=1.0)
passo_scansione = st.sidebar.slider("Passo Scansione Incastro (mm)", min_value=2, max_value=25, value=10, step=1)

offset_totale = (diametro_utensile / 2.0) + distanza_sicurezza
# MOTORE DI LETTURA DXF RIGIDO ED ESPLICITO
def estrai_e_azzera_poligono_da_dxf(file_bytes):
    try:
        string_io = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
        doc = ezdxf.read(string_io)
        msp = doc.modelspace()
        linee = []
        
        for e in msp.query('LINE'):
            linee.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
            
        for e in msp.query('LWPOLYLINE POLYLINE'):
            try:
                pts = []
                for vertex in e.get_points():
                    pts.append((float(vertex[0]), float(vertex[1])))
                if len(pts) >= 2: 
                    linee.append(LineString(pts))
            except:
                pass
                
        if not linee: return None
        unione = unary_union(linee)
        poly = unione if unione.geom_type == 'Polygon' else Polygon([c for l in linee for c in l.coords])
        
        if poly and poly.is_valid and poly.area > 0.1:
            mx, my, _, _ = poly.bounds
            return affinity.translate(poly, xoff=-mx, yoff=-my)
        return None
    except: 
        return None
st.markdown('<div class="industrial-card"><h3>📥 1. Caricamento File Matrice (.DXF)</h3>', unsafe_allow_html=True)
file_caricati = st.file_uploader("Seleziona file DXF", type=["dxf"], accept_multiple_files=True, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

lista_particolari = []

if file_caricati:
    st.markdown('<div style="background-color:#111111; padding:20px; border-radius:6px; border:1px solid #334155; margin-bottom:20px;"><h3>📦 2. Fabbisogno e Quantità</h3>', unsafe_allow_html=True)
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
            st.markdown(f'<span style="color:#FFFFFF !important; font-weight:bold; font-size:16px;">📄 {f.name}</span>', unsafe_allow_html=True)
            st.markdown(f'<br><span style="color:#38BDF8 !important; font-size:14px;">Dimensione: {round(w_p)} x {round(h_p)} mm</span>', unsafe_allow_html=True)
        with col2:
            qta = st.number_input(f"Pezzi per {f.name}", min_value=1, max_value=200, value=5, step=1, key=f"q_{f.name}")
        lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})
    st.markdown('</div>', unsafe_allow_html=True)
if st.button("🚀 Elabora Nesting Geometrico Tetris", type="primary"):
    if not lista_particolari: st.error("Carica almeno un file DXF.")
    else:
        coda = []
        for p in lista_particolari:
            for _ in range(p["qta"]): coda.append({"nome": p["nome"], "poly": p["poly"], "area": p["area"]})
        coda.sort(key=lambda x: x["area"], reverse=True)
        bordo_utile = Polygon([(offset_totale, offset_totale), (W_lamiera - offset_totale, offset_totale), (W_lamiera - offset_totale, H_lamiera - offset_totale), (offset_totale, H_lamiera - offset_totale)])
        piazzati, report = [], []
        area_usata = 0
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_facecolor('#0F172A')
        fig.patch.set_facecolor('#121214')
        ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#38BDF8", linewidth=2))
        ax.grid(color='#334155', linestyle='--', linewidth=0.5, alpha=0.5)
        colori = cm.get_cmap('tab10', len(list(set([i["nome"] for i in coda]))))
        c_dict = {n: colori(idx) for idx, n in enumerate(list(set([i["nome"] for i in coda])))}
        for item in coda:
            p_orig = item["poly"]
            ok = False
            for ang in [0, 90, 180, 270]:
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
        ax.tick_params(colors='white')
        st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)
        rend = (area_usata / (W_lamiera * H_lamiera)) * 100
        st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1: st.metric("Rendimento Netto Lamiera", f"{rend:.2f}%")
        with m2: st.metric("Sfrido / Rottame Totale", f"{100-rend:.2f}%")
        st.markdown('</div><div class="industrial-card">', unsafe_allow_html=True)
        df_rep = pd.DataFrame(report)
        st.dataframe(df_rep, use_container_width=True)
        st.markdown('</div><div class="industrial-card">', unsafe_allow_html=True)
        e1, e2 = st.columns(2)
        with e1: st.download_button("📥 Scarica Report CSV", data=df_rep.to_csv(index=False).encode('utf-8'), file_name='Nesting.csv', mime='text/csv')
        with e2: st.markdown('<button onclick="window.print()" style="width:100%;height:38px;background-color:#4CAF50;color:white;border:none;border-radius:4px;font-weight:bold;cursor:pointer;">🖨️ Stampa Scheda (PDF)</button>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
