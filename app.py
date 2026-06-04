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

# BLOCCO STILE: ABBATTE I RIGUADRI CHIARI E FORZA IL CONTRASTO NETTO
st.markdown("""
    <style>
    html, body, [data-testid="stWidgetLabel"], p, label, .stMarkdown, h1, h2, h3, h4, span { 
        color: #FFFFFF !important; 
    }
    [data-testid="stSidebar"] {
        background-color: #1E1E24 !important;
    }
    .stTextInput input, .stNumberInput input {
        color: #FFFFFF !important;
        background-color: #2D2D34 !important;
    }
    .stButton>button { 
        color: #FFFFFF !important; 
        background-color: #FF4B4B !important; 
        font-weight: bold; 
    }
    code { 
        color: #00FF00 !important; 
        background-color: #111111 !important; 
    }
    @media print {
        header, [data-testid="stSidebar"], .stButton, .stDownloadButton, button, .stFileUploader { display: none !important; }
        .stMainBlockContainer { background-color: #FFFFFF !important; color: #000000 !important; }
    }
    </style>
""", unsafe_allow_html=True)

# DIZIONARIO ESPLICITO PER EVITARE BUG DI STRUTTURA
TRADUZIONI = {
    "IT": {
        "titolo": "📐 MetalHub - Suite Officina", "dati_commessa": "📋 Dati Commessa", "ordine": "Numero Ordine", 
        "cliente": "Nome Cliente", "data": "Data", "sottotitolo": "Piano Taglio Lamiera", "param_lamiera": "⚙️ Dimensioni Lamiera (mm)", 
        "larg": "Larghezza X (mm)", "alt": "Altezza Y (mm)", "param_macchina": "🔧 Parametri Utensile", "fresa": "Diametro Fresa (mm)", 
        "sicurezza": "Distanza Sicurezza (mm)", "passo": "Passo scansione (mm)", "carica_titolo": "1. Carica File (.DXF)", 
        "carica_input": "Trascina i file DXF qui", "qta_titolo": "### Quantità di Produzione", "qta_label": "Quantità per il file:", 
        "btn_calcola": "🚀 Calcola Nesting Reale", "errore_no_file": "Carica un file DXF!", "resa": "Rendimento Lamiera", 
        "sfrido": "Sfrido Totale", "tab_titolo": "📋 Pezzi Mappati", "esporta": "💾 Esporta", "btn_csv": "📥 Scarica CSV", "btn_pdf": "🖨️ Stampa PDF"
    },
    "GB": {
        "titolo": "📐 MetalHub - Workshop Suite", "dati_commessa": "📋 Job Data", "ordine": "Order Number", 
        "cliente": "Customer Name", "data": "Date", "sottotitolo": "Sheet Cut Plan", "param_lamiera": "⚙️ Sheet Dimensions (mm)", 
        "larg": "Width X (mm)", "alt": "Height Y (mm)", "param_macchina": "🔧 Tool Parameters", "fresa": "Cutter Diam. (mm)", 
        "sicurezza": "Safety Distance (mm)", "passo": "Scan Step (mm)", "carica_titolo": "1. Upload Files (.DXF)", 
        "carica_input": "Drag DXF files here", "qta_titolo": "### Production Quantities", "qta_label": "Quantity for file:", 
        "btn_calcola": "🚀 Run Real Nesting", "errore_no_file": "Upload a valid DXF!", "resa": "Sheet Yield", 
        "sfrido": "Total Scrap", "tab_titolo": "📋 Mapped Parts", "esporta": "💾 Export", "btn_csv": "📥 Download CSV", "btn_pdf": "🖨️ Print PDF"
    }
}
# PROSEGUIMENTO DIZIONARIO LINGUE (CORREZIONE APPLICATA)
TRADUZIONI["FR"] = {
    "titolo": "📐 MetalHub - Suite d'Atelier", "dati_commessa": "📋 Données Commande", "ordine": "Numéro", 
    "cliente": "Client", "data": "Date", "sottotitolo": "Plan Découpe", "param_lamiera": "⚙️ Dimensions Tôle (mm)", 
    "larg": "Largeur X (mm)", "alt": "Hauteur Y (mm)", "param_macchina": "🔧 Paramètres Outil", "fresa": "Diamètre Fraise (mm)", 
    "sicurezza": "Distance Sécurité (mm)", "passo": "Pas Balayage (mm)", "carica_titolo": "1. Charger (.DXF)", 
    "carica_input": "Glissez les fichiers DXF", "qta_titolo": "### Quantités", "qta_label": "Quantité pour:", 
    "btn_calcola": "🚀 Imbrication Réelle", "errore_no_file": "Charger un DXF!", "resa": "Rendement Tôle", 
    "sfrido": "Total Déchets", "tab_titolo": "📋 Pièces Imbriquées", "esporta": "💾 Exporter", "btn_csv": "📥 CSV", "btn_pdf": "🖨️ PDF"
}
TRADUZIONI["DE"] = {
    "titolo": "📐 MetalHub - Werkstatt", "dati_commessa": "📋 Auftragsdaten", "ordine": "Nummer", 
    "cliente": "Kunde", "data": "Datum", "sottotitolo": "Schneideplan", "param_lamiera": "⚙️ Blechmaße (mm)", 
    "larg": "Breite X (mm)", "alt": "Höhe Y (mm)", "param_macchina": "🔧 Werkzeugparameter", "fresa": "Fräser (mm)", 
    "sicurezza": "Sicherheitsabstand (mm)", "passo": "Scanschritt (mm)", "carica_titolo": "1. DXF Hochladen", 
    "carica_input": "DXF-Dateien hierher", "qta_titolo": "### Mengen", "qta_label": "Menge für:", 
    "btn_calcola": "🚀 Nesting Berechnen", "errore_no_file": "DXF hochladen!", "resa": "Blechausbeute", 
    "sfrido": "Ausschuss", "tab_titolo": "📋 Teileliste", "esporta": "💾 Export", "btn_csv": "📥 CSV", "btn_pdf": "🖨️ PDF"
}
TRADUZIONI["ES"] = {
    "titolo": "📐 MetalHub - Suite de Taller", "dati_commessa": "📋 Datos Orden", "ordine": "Número", 
    "cliente": "Cliente", "data": "Fecha", "sottotitolo": "Plan de Corte", "param_lamiera": "⚙️ Dimensiones Chapa (mm)", 
    "larg": "Ancho X (mm)", "alt": "Alto Y (mm)", "param_macchina": "🔧 Parámetros", "fresa": "Diámetro Fresa (mm)", 
    "sicurezza": "Distancia Seg. (mm)", "passo": "Paso Escaneo (mm)", "carica_titolo": "1. Cargar (.DXF)", 
    "carica_input": "Arrastre los DXF aquí", "qta_titolo": "### Cantidades", "qta_label": "Cantidad para:", 
    "btn_calcola": "🚀 Nesting Real", "errore_no_file": "¡Cargue un DXF!", "resa": "Rendimiento Chapa", 
    "sfrido": "Chatarra Total", "tab_titolo": "📋 Piezas Mapeadas", "esporta": "💾 Exportar", "btn_csv": "📥 CSV", "btn_pdf": "🖨️ PDF"
}
TRADUZIONI["CZ"] = {
    "titolo": "📐 MetalHub - Dílna", "dati_commessa": "📋 Údaje Zakázky", "ordine": "Číslo", 
    "cliente": "Zákazník", "data": "Datum", "sottotitolo": "Plán Řezání Plechu", "param_lamiera": "⚙️ Rozměry Plechu (mm)", 
    "larg": "Šířka X (mm)", "alt": "Výška Y (mm)", "param_macchina": "🔧 Nástroj", "fresa": "Průměr Frézy (mm)", 
    "sicurezza": "Bezpečnost (mm)", "passo": "Krok (mm)", "carica_titolo": "1. Načíst (.DXF)", 
    "carica_input": "Sem přetáhněte DXF", "qta_titolo": "### Množství", "qta_label": "Množství pro:", 
    "btn_calcola": "🚀 Spustit Skládání", "errore_no_file": "Načtěte DXF!", "resa": "Výtěžnost Plechu", 
    "sfrido": "Celkový Odpad", "tab_titolo": "📋 Umístěné Díly", "esporta": "💾 Export", "btn_csv": "📥 CSV", "btn_pdf": "🖨️ PDF"
}
TRADUZIONI["HU"] = {
    "titolo": "📐 MetalHub - Műhely", "dati_commessa": "📋 Rendelés", "ordine": "Szám", 
    "cliente": "Ügyfél", "data": "Dátum", "sottotitolo": "Vágási Terv", "param_lamiera": "⚙️ Lemezméretek (mm)", 
    "larg": "Szélesség X (mm)", "alt": "Magasság Y (mm)", "param_macchina": "🔧 Szerszám", "fresa": "Maró (mm)", 
    "sicurezza": "Biztonság (mm)", "passo": "Lépés (mm)", "carica_titolo": "1. DXF Feltöltés", 
    "carica_input": "Húzza ide a DXF-et", "qta_titolo": "### Mennyiségek", "qta_label": "Mennyiség ehhez:", 
    "btn_calcola": "🚀 Beágyazás Indítása", "errore_no_file": "Töltsön fel DXF-et!", "resa": "Lemezkihasználás", 
    "sfrido": "Hulladék", "tab_titolo": "📋 Alkatrészek", "esporta": "💾 Export", "btn_csv": "📥 CSV", "btn_pdf": "🖨️ PDF"
}
TRADUZIONI["RO"] = {
    "titolo": "📐 MetalHub - Suite Atelier", "dati_commessa": "📋 Date Comandă", "ordine": "Număr", 
    "cliente": "Client", "data": "Dată", "sottotitolo": "Plan Tăiere", "param_lamiera": "⚙️ Dimensiuni Tablă (mm)", 
    "larg": "Lățime X (mm)", "alt": "Înălțime Y (mm)", "param_macchina": "🔧 Parametri Sculă", "fresa": "Diametru Freză (mm)", 
    "sicurezza": "Siguranță (mm)", "passo": "Pas Scanare (mm)", "carica_titolo": "1. Încărcare (.DXF)", 
    "carica_input": "Trageți DXF aici", "qta_titolo": "### Cantități", "qta_label": "Cantitate pentru:", 
    "btn_calcola": "🚀 Imbricare Reală", "errore_no_file": "Încărcați DXF!", "resa": "Randament Net Tablă", 
    "sfrido": "Deșeu Total", "tab_titolo": "📋 Piese Imbricate", "esporta": "💾 Export", "btn_csv": "📥 Descarcă Raport", "btn_pdf": "🖨️ PDF"
}
TRADUZIONI["PT"] = {
    "titolo": "📐 MetalHub - Suite de Oficina", "dati_commessa": "📋 Dados da Encomenda", "ordine": "Número", 
    "cliente": "Cliente", "data": "Data", "sottotitolo": "Plano Corte", "param_lamiera": "⚙️ Dimensões Chapa (mm)", 
    "larg": "Largura X (mm)", "alt": "Altura Y (mm)", "param_macchina": "🔧 Ferramenta", "fresa": "Diâmetro Fresa (mm)", 
    "sicurezza": "Segurança (mm)", "passo": "Passo (mm)", "carica_titolo": "1. Carregar Arquivos", 
    "carica_input": "Arraste os DXF aqui", "qta_titolo": "### Quantidades", "qta_label": "Quantidade para:", 
    "btn_calcola": "🚀 Executar Nesting Real", "errore_no_file": "Por favor, carregue pelo menos um arquivo DXF válido!",
    "resa": "Rendimento Líquido da Chapa", "sfrido": "Total Sucata / Desperdício", "tab_titolo": "📋 Lista de Peças Mapeadas", "esporta": "💾 Exportar", "btn_csv": "📥 Baixar Relatório", "btn_pdf": "🖨️ PDF"
}

st.sidebar.markdown("### 👤 User Account & Setup")
lingua = st.sidebar.selectbox("🌍 Language", options=list(TRADUZIONI.keys()), format_func=lambda x: {"IT":"🇮🇹 IT","GB":"🇬🇧 GB","FR":"🇫🇷 FR","DE":"🇩🇪 DE","ES":"🇪🇸 ES","CZ":"🇨🇿 CZ","HU":"🇭🇺 HU","RO":"🇷🇴 RO","PT":"🇵🇹 PT"}[x])
L = TRADUZIONI[lingua]

st.title(L["titolo"])
st.subheader(L["dati_commessa"])
c1, c2, c3 = st.columns(3)
with c1: num_ordine = st.text_input(L["ordine"], value="ORD-2D-001")
with c2: nome_cliente = st.text_input(L["cliente"], value="Customer SpA")
with c3: data_commessa = st.date_input(L["data"], date.today())

st.markdown(f'<div style="border:1px solid #FF4B4B;padding:10px;border-radius:5px;background-color:#222222;margin-bottom:15px;"><p style="margin:0;"><b>{L["sottotitolo"]}:</b> {num_ordine} | <b>{L["cliente"]}:</b> {nome_cliente}</p></div>', unsafe_allow_html=True)

st.sidebar.header(L["param_lamiera"])
W_lamiera = st.sidebar.number_input(L["larg"], value=1000, step=100)
H_lamiera = st.sidebar.number_input(L["alt"], value=1000, step=100)
st.sidebar.header(L["param_macchina"])
diametro_utensile = st.sidebar.number_input(L["fresa"], value=6.0, step=1.0)
distanza_sicurezza = st.sidebar.number_input(L["sicurezza"], value=4.0, step=1.0)
passo_scansione = st.sidebar.slider(L["passo"], min_value=2, max_value=25, value=10, step=1)
offset_totale = (diametro_utensile / 2.0) + distanza_sicurezza

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
            for p in e.vertices():
                if hasattr(p, 'dxf'): pts.append((p.dxf.location.x, p.dxf.location.y))
                else: pts.append((p, p))
            if len(pts) >= 2: linee.append(LineString(pts))
            
        for e in msp.query('ARC CIRCLE ELLIPSE SPLINE'):
            try:
                vertici_curva = list(e.flattening_paths())
                for path in vertici_curva:
                    pts = [(v.x, v.y) for v in path]
                    if len(pts) >= 2: linee.append(LineString(pts))
            except: pass
                
        if not linee: return None
        unione = unary_union(linee)
        poly = None
        if unione.geom_type == 'Polygon': poly = unione
        elif unione.geom_type in ['MultiPolygon', 'GeometryCollection']:
            for g in unione.geoms:
                if g.geom_type == 'Polygon': 
                    poly = g
                    break
        if not poly:
            coords = []
            for line in linee: coords.extend(line.coords)
            if len(coords) >= 3: poly = Polygon(coords).convex_hull
            
        if poly:
            mx, my, _, _ = poly.bounds
            return affinity.translate(poly, xoff=-mx, yoff=-my)
        return None
    except: return Polygon([(0,0), (100,0), (100,100), (0,100)])
st.header(L["carica_titolo"])
file_caricati = st.file_uploader(L["carica_input"], type=["dxf"], accept_multiple_files=True)
lista_particolari = []

if file_caricati:
    # Contenitore ad alto contrasto per le quantità dei pezzi
    st.markdown(f'<div style="background-color:#111111; padding:20px; border-radius:8px; border:2px solid #FF4B4B; margin-bottom:20px;"><h4>{L["qta_titolo"]}</h4>', unsafe_allow_html=True)
    
    for f in file_caricati:
        poly = estrai_e_azzera_poligono_da_dxf(f.getvalue())
        if poly:
            mx, my, xx, yx = poly.bounds
            w_p, h_p = xx-mx, yx-my
            
            # Layout pulito a tre colonne dentro la scatola nera per evitare conflitti con la lingua
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f'<p style="color:#00FFCD !important; font-weight:bold; margin-top:5px; margin-bottom:0;">📄 {f.name}</p>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<p style="color:#FFFFFF !important; margin-top:5px; margin-bottom:0;">📐 {round(w_p)} x {round(h_p)} mm</p>', unsafe_allow_html=True)
            with col3:
                # Campo di input numerico stabile con chiave univoca
                qta = st.number_input(f"Qta_{f.name}", min_value=1, max_value=200, value=5, step=1, label_visibility="collapsed")
                
            lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})
            
    st.markdown('</div>', unsafe_allow_html=True)

if st.button(L["btn_calcola"], type="primary"):
    if not lista_particolari: 
        st.error(L["errore_no_file"])
    else:
        coda = []
        for p in lista_particolari:
            for _ in range(p["qta"]): coda.append({"nome": p["nome"], "poly": p["poly"], "area": p["area"]})
        coda.sort(key=lambda x: x["area"], reverse=True)
        
        bordo_utile = Polygon([(offset_totale, offset_totale), (W_lamiera - offset_totale, offset_totale), (W_lamiera - offset_totale, H_lamiera - offset_totale), (offset_totale, H_lamiera - offset_totale)])
        piazzati, report = [], []
        area_usata = 0
        
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_facecolor('#151515')
        fig.patch.set_facecolor('#111111')
        ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF4B4B", linewidth=3))
        
        nomi_unici = list(set([i["nome"] for i in coda]))
        colori = cm.get_cmap('tab10', len(nomi_unici))
        c_dict = {n: colori(idx) for idx, n in enumerate(nomi_unici)}
        
        for item in coda:
            p_orig = item["poly"]
            ok = False
            angoli_rotazione = [0, 45, 90, 135, 180, 225, 270, 315]
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
        with m1: st.metric(L["resa"], f"{rend:.2f}%")
        with col_m2 if 'col_m2' in locals() else m2: st.metric(L["sfrido"], f"{100-rend:.2f}%")
        
        st.subheader(L["tab_titolo"])
        df_rep = pd.DataFrame(report)
        st.dataframe(df_rep, use_container_width=True)
        
        st.header(L["esporta"])
        e1, e2 = st.columns(2)
        with e1: st.download_button(L["btn_csv"], data=df_rep.to_csv(index=False).encode('utf-8'), file_name='Nesting.csv', mime='text/csv')
        with e2: st.markdown(f'<button onclick="window.print()" style="width:100%;height:38px;background-color:#4CAF50;color:white;border:none;border-radius:4px;font-weight:bold;cursor:pointer;">{L["btn_pdf"]}</button>', unsafe_allow_html=True)
