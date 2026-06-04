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
st.set_page_config(page_title="C-Engine Pro", layout="wide")

# STILE PREMIUM INGEGNERISTICO (STILE MONITOR MACCHINA CNC)
st.markdown("""
    <style>
    /* Sfondo scuro e font tecnica pulita */
    .stApp, html, body { 
        background-color: #0F172A !important; 
    }
    h1, h2, h3, h4, p, label, span, [data-testid="stWidgetLabel"], .stMarkdown { 
        color: #F8FAFC !important; 
        font-family: 'Courier New', Courier, monospace !important;
    }
    /* Barra laterale mimetizzata con bordo di divisione sottile */
    [data-testid="stSidebar"] { 
        background-color: #1E293B !important; 
        border-right: 1px solid #334155 !important;
    }
    /* Campi numerici e di testo stile plancia tecnica */
    .stTextInput input, .stNumberInput input { 
        color: #38BDF8 !important; 
        background-color: #0F172A !important; 
        border: 1px solid #475569 !important;
        border-radius: 4px !important;
        font-weight: bold !important;
    }
    /* Riquadro Drag and Drop per i file CAD */
    [data-testid="stFileUploader"] {
        background-color: #1E293B !important;
        border: 2px dashed #38BDF8 !important;
        border-radius: 6px !important;
    }
    /* Card sollevate per separare i blocchi operativi */
    .industrial-card {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        padding: 18px !important;
        border-radius: 6px !important;
        margin-bottom: 15px !important;
    }
    /* Pulsante primario di elaborazione nesting */
    .stButton>button { 
        color: #0F172A !important; 
        background-color: #38BDF8 !important; 
        border: none !important;
        border-radius: 4px !important;
        padding: 0.6rem 2rem !important;
        font-weight: bold !important;
        width: 100% !important;
        letter-spacing: 1px !important;
    }
    .stButton>button:hover { 
        background-color: #7DD3FC !important; 
    }
    /* Tabelle dei dati di officina */
    .stDataFrame { background-color: #1E293B !important; border: 1px solid #334155 !important; }
    </style>
""", unsafe_allow_html=True)

# DIZIONARIO LOCALIZZAZIONE INTERFACCIA
TRADUZIONI = {
    "IT": ["⚙️ MetalHub - Configurazione Commessa", "📋 Parametri Identificativi", "Codice Ordine / Commessa", "Anagrafica Cliente", "Data Lavorazione", "Dettaglio Ordine", "📊 Configurazione Formato Lamiera", "Lunghezza Lastra X (mm)", "Altezza Lastra Y (mm)", "🛠️ Parametri Macchina Utensile", "Diametro Utensile Fresa (mm)", "Distanza Sicurezza Pezzi (mm)", "Risoluzione Calcolo (mm)", "📥 1. Caricamento File Matrice (.DXF)", "Trascina qui i profili DXF da tagliare", "📦 2. Fabbisogno e Quantità di Produzione", "Quantità", "🚀 Elabora Nesting Geometrico Tetris", "Inserisci almeno un file CAD!", "Efficienza Lamiera", "Sfrido Generato", "📋 Report Posizionamento Nodi", "💾 Area Esportazione Dati", "Scarica Tabella (CSV)", "Stampa Scheda Officina (PDF)"],
    "GB": ["⚙️ MetalHub - Job Configuration", "📋 Job Identification", "Order / Job Number", "Customer Name", "Processing Date", "Job Details", "📊 Sheet Format Settings", "Sheet Width X (mm)", "Sheet Height Y (mm)", "🛠️ Machine Tool Parameters", "Cutter Diameter / Kerf (mm)", "Safety Clearance (mm)", "Calculation Resolution (mm)", "📥 1. Upload Template Files (.DXF)", "Drag and drop your DXF files here", "📦 2. Production Volume & Quantities", "Quantity", "🚀 Run Geometric Interlock Nesting", "Please upload a valid CAD file!", "Material Yield", "Total Scrap", "📋 Node Placement Report", "💾 Data Export Center", "Download Table (CSV)", "Print Shop Sheet (PDF)"]
}
# PROSEGUIMENTO DIZIONARIO LINGUE IN VERTICALE SECONDO SPECIFICHE
TRADUZIONI["FR"] = [
    "📐 MetalHub - Suite d'Atelier", "📋 Données Commande", "Numéro", 
    "Client", "Date", "Plan Découpe", "⚙️ Dimensions Tôle (mm)", 
    "Largeur X (mm)", "Hauteur Y (mm)", "🔧 Paramètres Outil", 
    "Diamètre Fraise (mm)", "Distance Sécurité (mm)", "Pas Balayage (mm)", 
    "1. Charger (.DXF)", "Glissez les fichiers DXF", "### Quantités", 
    "Quantité pour", "🚀 Imbrication Réelle", "Charger un DXF!", 
    "Rendement Tôle", "Total Déchets", "📋 Pièces Imbriquées", 
    "💾 Exporter", "📥 CSV", "🖨️ PDF"
]
TRADUZIONI["DE"] = [
    "📐 MetalHub - Werkstatt", "📋 Auftragsdaten", "Nummer", 
    "Kunde", "Datum", "Schneideplan", "⚙️ Blechmaße (mm)", 
    "Breite X (mm)", "Höhe Y (mm)", "🔧 Werkzeugparameter", 
    "Fräser (mm)", "Sicherheitsabstand (mm)", "Scanschritt (mm)", 
    "1. DXF Hochladen", "DXF-Dateien hierher", "### Mengen", 
    "Menge für", "🚀 Nesting Berechnen", "DXF hochladen!", 
    "Blechausbeute", "Ausschuss", "📋 Teileliste", 
    "💾 Export", "📥 CSV", "🖨️ PDF"
]
TRADUZIONI["ES"] = [
    "📐 MetalHub - Suite de Taller", "📋 Datos Orden", "Número", 
    "Cliente", "Fecha", "Plan de Corte", "⚙️ Dimensiones Chapa (mm)", 
    "Ancho X (mm)", "Alto Y (mm)", "🔧 Parámetros", 
    "Diámetro Fresa (mm)", "Distancia Seg. (mm)", "Paso Escaneo (mm)", 
    "1. Cargar (.DXF)", "Arrastre los DXF aquí", "### Cantidades", 
    "Cantidad para", "🚀 Nesting Real", "¡Cargue un DXF!", 
    "Rendimento Chapa", "Chatarra Total", "📋 Piezas Mapeadas", 
    "💾 Exportar", "📥 CSV", "🖨️ PDF"
]
TRADUZIONI["CZ"] = [
    "📐 MetalHub - Dílna", "📋 Údaje Zakázky", "Číslo", 
    "Zákazník", "Datum", "Plán Řezání", "⚙️ Rozměry Plechu (mm)", 
    "Šířka X (mm)", "Výška Y (mm)", "🔧 Nástroj", 
    "Průměr Frézy (mm)", "Bezpečnost (mm)", "Krok (mm)", 
    "1. Načíst (.DXF)", "Sem přetáhněte DXF", "### Množství", 
    "Množství pro", "🚀 Spustit Skládání", "Načtěte DXF!", 
    "Výtěžnost Plechu", "Celkový Odpad", "📋 Umístěné Díly", 
    "💾 Export", "📥 CSV", "🖨️ PDF"
]
TRADUZIONI["HU"] = [
    "📐 MetalHub - Műhely", "📋 Rendelés", "Szám", 
    "Ügyfél", "Dátum", "Vágási Terv", "⚙️ Lemezméretek (mm)", 
    "Szélesség X (mm)", "Magasság Y (mm)", "🔧 Szerszám", 
    "Maró (mm)", "Biztonság (mm)", "Lépés (mm)", 
    "1. DXF Feltöltés", "Húzza ide a DXF-et", "### Mennyiségek", 
    "Mennyiség ehhez:", "🚀 Beágyazás Indítása", "Töltsön fel DXF-et!", 
    "Lemezkihasználás", "Hulladék", "📋 Alkatrészek", 
    "💾 Export", "📥 CSV", "🖨️ PDF"
]
TRADUZIONI["RO"] = [
    "📐 MetalHub - Atelier", "📋 Date Comandă", "Număr", 
    "Client", "Dată", "Plan Tăiere", "⚙️ Dimensiuni Tablă (mm)", 
    "Lățime X (mm)", "Înălțime Y (mm)", "🔧 Parametri Sculă", 
    "Diametru Freză (mm)", "Siguranță (mm)", "Pas Scanare (mm)", 
    "1. Încărcare (.DXF)", "Trageți DXF aici", "### Cantități", 
    "Cantitate pentru", "🚀 Imbricare Reală", "Încărcați DXF!", 
    "Randament Tablă", "Deșeu Total", "📋 Piese Imbricate", 
    "💾 Export", "📥 CSV", "🖨️ PDF"
]
TRADUZIONI["PT"] = [
    "📐 MetalHub - Oficina", "📋 Dados Pedido", "Número", 
    "Cliente", "Data", "Plano Corte", "⚙️ Dimensões Chapa (mm)", 
    "Largura X (mm)", "Altura Y (mm)", "🔧 Ferramenta", 
    "Diâmetro Fresa (mm)", "Segurança (mm)", "Passo (mm)", 
    "1. Carregar (.DXF)", "Arraste os DXF aqui", "### Quantidades", 
    "Quantidade para", "🚀 Nesting Real", "Carregue um DXF!", 
    "Rendimento Chapa", "Sucata Total", "📋 Peças Mapeadas", 
    "💾 Exportar", "📥 CSV", "🖨️ PDF"
]

st.sidebar.markdown("<h3 style='margin-top:0; color:#38BDF8;'>👤 Profilo & Account</h3>", unsafe_allow_html=True)
lingua = st.sidebar.selectbox("🌍 Lingua / Language", options=list(TRADUZIONI.keys()), format_func=lambda x: {"IT":"🇮🇹 Italiano","GB":"🇬🇧 English","FR":"🇫🇷 Français","DE":"🇩🇪 Deutsch","ES":"🇪🇸 Español","CZ":"🇨🇿 Čeština","HU":"🇭🇺 Magyar","RO":"🇷🇴 Română","PT":"🇵🇹 Português"}[x])
Txt = TRADUZIONI[lingua]

st.markdown(f'<div class="industrial-card"><h2>{Txt[0]}</h2><p style="color:#64748B; margin-bottom:0;">{Txt[5]}</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="industrial-card"><h3>{Txt[1]}</h3>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1: num_ordine = st.text_input(Txt[2], value="ORD-2D-001")
with c2: nome_cliente = st.text_input(Txt[3], value="Customer CNC SpA")
with c3: data_commessa = st.date_input(Txt[4], date.today())
st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown(f"<h4 style='color:#38BDF8;'>{Txt[6]}</h4>", unsafe_allow_html=True)
W_lamiera = st.sidebar.number_input(Txt[7], value=1000, step=100)
H_lamiera = st.sidebar.number_input(Txt[8], value=1000, step=100)

st.sidebar.markdown(f"<h4 style='color:#38BDF8;'>{Txt[9]}</h4>", unsafe_allow_html=True)
diametro_utensile = st.sidebar.number_input(Txt[10], value=6.0, step=1.0)
distanza_sicurezza = st.sidebar.number_input(Txt[11], value=4.0, step=1.0)
passo_scansione = st.sidebar.slider(Txt[12], min_value=2, max_value=25, value=10, step=1)
offset_totale = (diametro_utensile / 2.0) + distanza_sicurezza

# MOTORE NUOVO: ESTRATTORE DI COORDINATE CAD ESPLICITO E RIGIDO
def estrai_e_azzera_poligono_da_dxf(file_bytes):
    try:
        string_io = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
        doc = ezdxf.read(string_io)
        msp = doc.modelspace()
        linee = []
        
        # 1. Parsing Linee
        for e in msp.query('LINE'):
            linee.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
            
        # 2. Parsing Polilinee 2D/3D (Lettura esplicita dei punti estratti da ezdxf)
        for e in msp.query('LWPOLYLINE POLYLINE'):
            try:
                punti_lista = []
                for p in e.get_points():
                    punti_lista.append((float(p[0]), float(p[1])))
                if len(punti_lista) >= 2:
                    linee.append(LineString(punti_lista))
            except:
                pass
                
        if not linee: 
            return None
            
        unione = unary_union(linee)
        poly = None
        if unione.geom_type == 'Polygon': 
            poly = unione
        else:
            # Se le entità sono segmenti separati, raccoglie tutte le coordinate per ricreare la mesh
            coords = []
            for line in linee: 
                coords.extend(line.coords)
            if len(coords) >= 3: 
                poly = Polygon(coords)
                
        if poly and poly.is_valid and poly.area > 0.1:
            mx, my, _, _ = poly.bounds
            # Spostamento immediato allo zero (0,0) cartesiano
            return affinity.translate(poly, xoff=-mx, yoff=-my)
        return None
    except: 
        return None
st.markdown(f'<div class="industrial-card"><h3>{Txt}</h3>', unsafe_allow_html=True)
file_caricati = st.file_uploader(Txt, type=["dxf"], accept_multiple_files=True, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

lista_particolari = []

if file_caricati:
    # Contenitore principale scuro con bordo rosso per un contrasto perfetto
    st.markdown(f'<div style="background-color:#111111; padding:20px; border-radius:8px; border:2px solid #FF4B4B; margin-bottom:20px;"><h3 style="color:#FFFFFF !important; margin-top:0;">{Txt}</h3><div style="margin-top:15px;">', unsafe_allow_html=True)
    
    for f in file_caricati:
        poly = estrai_e_azzera_poligono_da_dxf(f.getvalue())
        
        # Rilevamento delle dimensioni reali del pezzo
        if poly:
            mx, my, xx, yx = poly.bounds
            w_p, h_p = xx-mx, yx-my
            is_fallback = False
        else:
            # Fallback intelligente se il DXF ha errori, ma impostato sulle tue misure tipiche (90x80)
            poly = Polygon([(0,0), (90,0), (90,80), (0,80)])
            w_p, h_p = 90.0, 80.0
            is_fallback = True
            
        col1, col2 = st.columns()
        with col1:
            # FORZATURA TESTO BIANCO PURO E AZZURRO TECNICO
            st.markdown(f'<span style="color:#FFFFFF !important; font-weight:bold; font-size:16px; font-family:monospace;">📄 {f.name}</span>', unsafe_allow_html=True)
            tipo_geometria = "fallback" if is_fallback else "polygon"
            st.markdown(f'<br><span style="color:#38BDF8 !important; font-size:14px; font-family:monospace;">Dimensione: {round(w_p)} x {round(h_p)} mm · {tipo_geometria}</span>', unsafe_allow_html=True)
        with col2:
            qta = st.number_input(f"{Txt}: {f.name}", min_value=1, max_value=200, value=5, step=1)
            
        lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})
            
    st.markdown('</div></div>', unsafe_allow_html=True)

if st.button(Txt, type="primary"):
    if not lista_particolari: 
        st.error(Txt)
    else:
        coda = []
        for p in lista_particolari:
            for _ in range(p["qta"]): 
                coda.append({"nome": p["nome"], "poly": p["poly"], "area": p["area"]})
        coda.sort(key=lambda x: x["area"], reverse=True)
        
        bordo_utile = Polygon([
            (offset_totale, offset_totale), 
            (W_lamiera - offset_totale, offset_totale), 
            (W_lamiera - offset_totale, H_lamiera - offset_totale), 
            (offset_totale, H_lamiera - offset_totale)
        ])
        
        piazzati, report = [], []
        area_usata = 0
        
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_facecolor('#0F172A') # Sfondo grafico tecnico scuro ardesia
        fig.patch.set_facecolor('#121214')
        ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF4B4B", linewidth=3))
        
        # Griglia millimetrica ingegneristica di sfondo
        ax.grid(color='#334155', linestyle='--', linewidth=0.5, alpha=0.5)
        
        nomi_unici = list(set([i["nome"] for i in coda]))
        colori = cm.get_cmap('tab10', len(nomi_unici))
        c_dict = {n: colori(idx) for idx, n in enumerate(nomi_unici)}
        
        for item in coda:
            p_orig = item["poly"]
            ok = False
            
            # ELENCO ROTAZIONI GEOMETRICHE DEFINITO
            angoli_rotazione =
            for ang in angoli_rotazione:
                if ok: break
                p_ruot = affinity.rotate(p_orig, ang, origin='center').buffer(offset_totale)
                mnx, mny, _, _ = p_ruot.bounds
                
                for yt in range(int(offset_totale), int(H_lamiera), passo_scansione):
                    if ok: break
                    for xt in range(int(offset_totale), int(W_lamiera), passo_scansione):
                        p_shift = affinity.translate(p_ruot, xoff=xt-mnx, yoff=yt-mny)
                        
                        if bordo_utile.contains(p_shift):
                            if not any(p_shift.intersects(g) for g in piazzati):
                                p_real = affinity.translate(affinity.rotate(p_orig, ang, origin='center'), xoff=xt-mnx, yoff=yt-mny)
                                piazzati.append(p_shift)
                                area_usata += item["area"]
                                ok = True
                                x, y = p_real.exterior.xy
                                
                                # Rendering tecnico: colore di riempimento ad alta visibilità e bordo nero netto
                                ax.fill(x, y, alpha=0.8, color=c_dict[item["nome"]], edgecolor='#000000', linewidth=1.5)
                                ax.text(p_real.centroid.x, p_real.centroid.y, item["nome"][:8], color="black", fontsize=8, weight="bold", ha="center", va="center", bbox=dict(boxstyle='round,pad=0.1', fc='white', alpha=0.7, ec='none'))
                                report.append({"Articolo": item["nome"], "Rotazione": f"{ang}°"})
                                break
                                
        ax.set_xlim(-50, W_lamiera + 50)
        ax.set_ylim(-50, H_lamiera + 50)
        ax.set_aspect('equal')
        ax.tick_params(colors='white')
        
        st.markdown(f'<div class="industrial-card">', unsafe_allow_html=True)
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)
        
        rend = (area_usata / (W_lamiera * H_lamiera)) * 100
        
        st.markdown(f'<div class="industrial-card">', unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1: st.metric(L["resa"], f"{rend:.2f}%")
        with m2: st.metric(L["sfrido"], f"{100-rend:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f'<div class="industrial-card"><h3 style="color:#FFFFFF;">{L["tab_titolo"]}</h3>', unsafe_allow_html=True)
        df_rep = pd.DataFrame(report)
        st.dataframe(df_rep, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f'<div class="industrial-card"><h3 style="color:#FFFFFF;">{L["esporta"]}</h3>', unsafe_allow_html=True)
        e1, e2 = st.columns(2)
        with e1: 
            st.download_button(L["btn_csv"], data=df_rep.to_csv(index=False).encode('utf-8'), file_name='Nesting.csv', mime='text/csv')
        with e2: 
            st.markdown(f'<button onclick="window.print()" style="width:100%;height:38px;background-color:#4CAF50;color:white;border:none;border-radius:4px;font-weight:bold;cursor:pointer;">{L["btn_pdf"]}</button>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
