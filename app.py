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

# Configurazione interfaccia ad alto contrasto (Testi Bianchi) e regole di stampa PDF
st.set_page_config(page_title="MetalHub - Test Modulo 2 Soluzione", layout="wide")
st.markdown("""
    <style>
    html, body, [data-testid="stWidgetLabel"], p, label, .stMarkdown, h1, h2, h3, h4, span { color: #FFFFFF !important; }
    .stButton>button { color: #FFFFFF !important; background-color: #FF4B4B !important; font-weight: bold; }
    code { color: #00FF00 !important; background-color: #111111 !important; }
    @media print {
        header, [data-testid="stSidebar"], .stButton, [data-testid="stDownloadButton"], button, .stFileUploader { 
            display: none !important; 
        }
        .stMainBlockContainer { background-color: #FFFFFF !important; color: #000000 !important; }
        html, body, p, label, .stMarkdown, h1, h2, h3, h4, span, code { color: #000000 !important; }
    }
    </style>
""", unsafe_allow_html=True)

# FUNZIONE DI PARSING DXF CON AZZERAMENTO DELLE COORDINATE ORIGINE CAD
def estrai_poligono_da_dxf(file_bytes):
    try:
        string_io = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
        doc = ezdxf.read(string_io)
        msp = doc.modelspace()
        linee_e_archi = []
        for e in msp.query('LINE'):
            linee_e_archi.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
        for e in msp.query('LWPOLYLINE POLYLINE'):
            punti = [(p, p) for p in e.vertices()]
            if len(punti) >= 3:
                linee_e_archi.append(LineString(punti))
        unione = unary_union(linee_e_archi)
        
        poly = None
        if unione.geom_type == 'Polygon':
            poly = unione
        else:
            coords = []
            for line in linee_e_archi: coords.extend(line.coords)
            if len(coords) >= 3: poly = Polygon(coords)
            
        # ─── FUNZIONE CRITICA DI CENTRATURA NELL'ORIGINE (0,0) ───
        if poly:
            minx, minny, _, _ = poly.bounds
            # Spostiamo il pezzo a (0,0) sottraendo i minimi nativi del file CAD
            poly_centrato = affinity.translate(poly, xoff=-minx, yoff=-minny)
            return poly_centrato
        return None
    except:
        return None

# --- INTESTAZIONE COMMESSA ---
st.title("📐 MetalHub - COLLAUDO: Modulo Nesting 2D Grafica Visiva")

st.subheader("📋 Dati della Commessa / Job Reference")
col_h1, col_h2, col_h3 = st.columns(3)
with col_h1: num_ordine = st.text_input("Numero Ordine", value="ORD-2D-001")
with col_h2: nome_cliente = st.text_input("Nome Cliente", value="Officina Meccanica Srl")
with col_h3: data_commessa = st.date_input("Data", date.today())

st.markdown(f"""
<div style="border: 1px solid #FF4B4B; padding: 10px; border-radius: 5px; background-color: #222222; margin-bottom: 15px;">
    <p style="margin: 0;"><b>Piano di Taglio Lamiera:</b> {num_ordine} | <b>Cliente:</b> {nome_cliente} | <b>Data:</b> {data_commessa.strftime('%d/%m/%Y')}</p>
</div>
""", unsafe_allow_html=True)

# PARAMETRI FOGLIO E UTENSILE IN SIDEBAR
st.sidebar.header("⚙️ Dimensioni Lamiera REALI (mm)")
W_lamiera = st.sidebar.number_input("Larghezza Lamiera X (mm)", value=1000, step=100)
H_lamiera = st.sidebar.number_input("Altezza Lamiera Y (mm)", value=1000, step=100)

st.sidebar.header("🔧 Parametri Utensile & Tolleranze")
diametro_utensile = st.sidebar.number_input("Diametro Fresa / Canale Taglio (mm)", value=6.0, step=1.0)
distanza_sicurezza = st.sidebar.number_input("Distanza di Sicurezza tra i pezzi (mm)", value=4.0, step=1.0)
passo_scansione = st.sidebar.slider("Passo scansione Incastro (mm)", min_value=2, max_value=25, value=5, step=1)

offset_totale = (diametro_utensile / 2.0) + distanza_sicurezza

# AREA CARICAMENTO FILE
st.header("1. Caricamento File dei Particolari (.DXF)")
file_caricati = st.file_uploader("Trascina qui i tuoi file DXF (Articoli Singoli)", type=["dxf"], accept_multiple_files=True)

lista_particolari = []
if file_caricati:
    st.write("### Definisci le Quantità di Produzione")
    for f in file_caricati:
        poly = estrai_poligono_da_dxf(f.getvalue())
        if poly:
            minx, minny, maxx, maxy = poly.bounds
            w_p = maxx - minx
            h_p = maxy - minny
            
            col_f1, col_f2 = st.columns(2)
            with col_f1: 
                st.write(f"📄 **{f.name}**")
                st.caption(f"Dimensione rilevata: {round(w_p)} x {round(h_p)} mm")
            with col_f2: 
                qta = st.number_input(f"Quantità per {f.name}", min_value=1, value=10, key=f"q_{f.name}")
            
            lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})

if st.button("🚀 Elabora Nesting ad Incastro Reale", type="primary"):
    if not lista_particolari:
        st.error("Carica almeno un file DXF valido!")
    else:
        coda_pezzi = []
        for p in lista_particolari:
            for _ in range(p["qta"]):
                coda_pezzi.append({"nome": p["nome"], "poly": p["poly"], "area": p["area"]})
        coda_pezzi.sort(key=lambda x: x["area"], reverse=True)

        bordo_utile = Polygon([
            (offset_totale, offset_totale), (W_lamiera - offset_totale, offset_totale), 
            (W_lamiera - offset_totale, H_lamiera - offset_totale), (offset_totale, H_lamiera - offset_totale)
        ])

        pezzi_piazzati_con_offset = []
        report_taglio = []
        area_utilizzata_reale = 0

        # RESET GRAFICO
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_facecolor('#151515')
        fig.patch.set_facecolor('#111111')
        ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF4B4B", linewidth=3, label="Bordo Lamiera"))

        nomi_unici = list(set([item["nome"] for item in coda_pezzi]))
        mappa_colori = cm.get_cmap('tab10', len(nomi_unici))
        color_dict = {nome: mappa_colori(idx) for idx, nome in enumerate(nomi_unici)}

        for item in coda_pezzi:
            poly_originale = item["poly"]
            piazzato = False
            
            # Angoli di rotazione (ogni 45°)
            for angolo in:
                if piazzato: break
                poly_ruotato = affinity.rotate(poly_originale, angolo, origin='center')
                poly_ruotato_offset = poly_ruotato.buffer(offset_totale)
                minx, minny, _, _ = poly_ruotato_offset.bounds
                
                for y_test in range(int(offset_totale), int(H_lamiera), passo_scansione):
                    if piazzato: break
                    for x_test in range(int(offset_totale), int(W_lamiera), passo_scansione):
                        x_shift = x_test - minx
                        y_shift = y_test - minny
                        p_offset_testato = affinity.translate(poly_ruotato_offset, xoff=x_shift, yoff=y_shift)
                        
                        if bordo_utile.contains(p_offset_testato):
                            collisione = False
                            for gia_piazzato_offset in pezzi_piazzati_con_offset:
                                if p_offset_testato.intersects(gia_piazzato_offset):
                                    collisione = True
                                    break
                            
                            if not collisione:
                                p_reale_posizionato = affinity.translate(poly_ruotato, xoff=x_shift, yoff=y_shift)
                                pezzi_piazzati_con_offset.append(p_offset_testato)
                                area_utilizzata_reale += item["area"]
                                piazzato = True
                                
                                # Disegno geometrico reale a schermo
                                x_c, y_c = p_reale_posizionato.exterior.xy
                                ax.fill(x_c, y_c, alpha=0.8, color=color_dict[item["nome"]], edgecolor='black', linewidth=1.5)
                                ax.text(p_reale_posizionato.centroid.x, p_reale_posizionato.centroid.y, item["nome"][:8], 
                                        color="black", fontsize=8, weight="bold", ha="center", va="center",
                                        bbox=dict(boxstyle='round,pad=0.1', fc='white', alpha=0.6, ec='none'))
                                
                                report_taglio.append({"Articolo": item["nome"], "Rotazione": f"{angolo}°", "Area Pezzo (mm²)": round(item["area"], 1)})
                                break

        # BLOCCO RIGIDO DEI CONFINI SULLA LAMIERA DA 1000x1000
        ax.set_xlim(-50, W_lamiera + 50)
        ax.set_ylim(-50, H_lamiera + 50)
        ax.set_aspect('equal')
        ax.tick_params(colors='white')
        plt.title(f"Layout Taglio Lamiera - {W_lamiera} x {H_lamiera} mm", color="white", fontsize=14, weight="bold")
        
        st.header("📊 Mappa Grafica del Nesting Ottimizzato")
        st.pyplot(fig)
        
        rendimento = (area_utilizzata_reale / (W_lamiera * H_lamiera)) * 100
        col_m1, col_m2 = st.columns(2)
        with col_m1: st.metric(label="Rendimento Netto Lamiera", value=f"{rendimento:.2f}%")
        with col_m2: st.metric(label="Sfrido / Rottame Totale", value=f"{100-rendimento:.2f}%")
        
        st.subheader("📋 Distinta Pezzi Mappati")
        df_report_2d = pd.DataFrame(report_taglio)
        st.dataframe(df_report_2d, use_container_width=True)
        
        st.header("💾 Esporta o Consegna al Reparto")
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv_2d = df_report_2d.to_csv(index=False).encode('utf-8')
