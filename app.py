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
st.set_page_config(page_title="C-Engine Pro", layout="wide")
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

# =============================================================================
# DIZIONARIO MULTILINGUA COMPLETO (LOCALIZZAZIONE REGIONALE)
# =============================================================================
TRADUZIONI = {
    "IT": {
        "titolo": "📐 MetalHub - Suite Officina", "dati_commessa": "📋 Dati della Commessa / Job Reference",
        "ordine": "Numero Ordine", "cliente": "Nome Cliente", "data": "Data", "sottotitolo": "Piano di Taglio Lamiera",
        "param_lamiera": "⚙️ Dimensioni Lamiera REALI (mm)", "larg": "Larghezza Lamiera X (mm)", "alt": "Altezza Lamiera Y (mm)",
        "param_macchina": "🔧 Parametri Utensile & Tolleranze", "fresa": "Diametro Fresa / Canale Taglio (mm)",
        "sicurezza": "Distanza di Sicurezza tra i pezzi (mm)", "passo": "Passo scansione Incastro (mm)",
        "carica_titolo": "1. Caricamento File dei Particolari (.DXF)", "carica_input": "Trascina qui i tuoi file DXF (Articoli Singoli)",
        "qta_titolo": "### Definisci le Quantità di Produzione", "qta_label": "Quantità per", "errore_chiuso": "Impossibile leggere il profilo. Verifica che sia un contorno chiuso.",
        "btn_calcola": "🚀 Elabora Nesting ad Incastro Reale", "errore_no_file": "Carica almeno un file DXF valido!",
        "resa": "Rendimento Netto Lamiera", "sfrido": "Sfrido / Rottame Totale", "tab_titolo": "📋 Distinta Pezzi Mappati",
        "esporta": "💾 Esporta o Consegna al Reparto", "btn_csv": "📥 Scarica Report in CSV (Excel)", "btn_pdf": "🖨️ Stampa o Esporta Mappa in PDF"
    },
    "GB": {
        "titolo": "📐 MetalHub - Workshop Suite", "dati_commessa": "📋 Job Reference Data",
        "ordine": "Order Number", "cliente": "Customer Name", "data": "Date", "sottotitolo": "Sheet Cutting Plan",
        "param_lamiera": "⚙️ Real Sheet Dimensions (mm)", "larg": "Sheet Width X (mm)", "alt": "Sheet Height Y (mm)",
        "param_macchina": "🔧 Tool Parameters & Tolerances", "fresa": "Cutter Diameter / Kerf (mm)",
        "sicurezza": "Safety Distance between parts (mm)", "passo": "Nesting Scanning Step (mm)",
        "carica_titolo": "1. Upload Part Files (.DXF)", "carica_input": "Drag and drop your DXF files here (Single Parts)",
        "qta_titolo": "### Define Production Quantities", "qta_label": "Quantity for", "errore_chiuso": "Unable to read profile. Verify it is a closed loop.",
        "btn_calcola": "🚀 Run Real Interlock Nesting", "errore_no_file": "Please upload at least one valid DXF file!",
        "resa": "Net Sheet Yield", "sfrido": "Total Scrap / Waste", "tab_titolo": "📋 Mapped Parts List",
        "esporta": "💾 Export or Deliver to Workshop", "btn_csv": "📥 Download CSV Report (Excel)", "btn_pdf": "🖨️ Print or Export Map as PDF"
    },
    "FR": {
        "titolo": "📐 MetalHub - Suite d'Atelier", "dati_commessa": "📋 Données de Commande",
        "ordine": "Numéro de Commande", "cliente": "Nom du Client", "data": "Date", "sottotitolo": "Plan de Découpe de Tôle",
        "param_lamiera": "⚙️ Dimensions Réelles de la Tôle (mm)", "larg": "Largeur de Tôle X (mm)", "alt": "Hauteur de Tôle Y (mm)",
        "param_macchina": "🔧 Paramètres d'Outil & Tolérances", "fresa": "Diamètre de la Fraise / Trait (mm)",
        "sicurezza": "Distance de Sécurité entre pièces (mm)", "passo": "Pas de balayage d'Imbrication (mm)",
        "carica_titolo": "1. Charger des Fichiers de Pièces (.DXF)", "carica_input": "Glissez-déposez vos fichiers DXF ici (Pièces Uniques)",
        "qta_titolo": "### Définir les Quantités de Production", "qta_label": "Quantité pour", "errore_chiuso": "Impossible de lire le profil. Vérifiez qu'il est fermé.",
        "btn_calcola": "🚀 Lancer l'Imbrication Encastrable", "errore_no_file": "Veuillez charger au moins un fichier DXF valide!",
        "resa": "Rendement Net de la Tôle", "sfrido": "Total Déchets / Rebuts", "tab_titolo": "📋 Liste des Pièces Imbriquées",
        "esporta": "💾 Exporter ou Livrer à l'Atelier", "btn_csv": "📥 Télécharger le Rapport CSV", "btn_pdf": "🖨️ Imprimer ou Exporter la Carte en PDF"
    },
    "DE": {
        "titolo": "📐 MetalHub - Werkstatt-Suite", "dati_commessa": "📋 Auftragsdaten",
        "ordine": "Auftragsnummer", "cliente": "Kundenname", "data": "Datum", "sottotitolo": "Blechschneideplan",
        "param_lamiera": "⚙️ Reale Blechabmessungen (mm)", "larg": "Blechbreite X (mm)", "alt": "Blechhöhe Y (mm)",
        "param_macchina": "🔧 Werkzeugparameter & Toleranzen", "fresa": "Fräserdurchmesser / Schnittspalt (mm)",
        "sicurezza": "Sicherheitsabstand zwischen Teilen (mm)", "passo": "Verschachtelungs-Scanschritt (mm)",
        "carica_titolo": "1. Bauteildateien hochladen (.DXF)", "carica_input": "Ziehen Sie Ihre DXF-Dateien hierher (Einzelteile)",
        "qta_titolo": "### Produktionsmengen definieren", "qta_label": "Menge für", "errore_chiuso": "Profil konnte nicht gelesen werden. Überprüfen Sie, ob es geschlossen ist.",
        "btn_calcola": "🚀 Verschachtelung Berechnen", "errore_no_file": "Bitte laden Sie mindestens eine gültige DXF-Datei hoch!",
        "resa": "Netto-Blechausbeute", "sfrido": "Gesamtschrott / Ausschuss", "tab_titolo": "📋 Liste der verschachtelten Teile",
        "esporta": "💾 Exportieren oder an Werkstatt liefern", "btn_csv": "📥 CSV-Bericht herunterladen", "btn_pdf": "🖨️ Karte als PDF drucken/exportieren"
    },
    "ES": {
        "titolo": "📐 MetalHub - Suite de Taller", "dati_commessa": "📋 Datos de la Orden",
        "ordine": "Número de Orden", "cliente": "Nombre del Cliente", "data": "Fecha", "sottotitolo": "Plan de Corte de Chapa",
        "param_lamiera": "⚙️ Dimensiones Reales de la Chapa (mm)", "larg": "Ancho de Chapa X (mm)", "alt": "Alto de Chapa Y (mm)",
        "param_macchina": "🔧 Parámetros de Herramienta & Tolerancias", "fresa": "Diámetro de Fresa / Canal (mm)",
        "sicurezza": "Distancia de Seguridad entre piezas (mm)", "passo": "Paso de escaneamento de Combinación (mm)",
        "carica_titolo": "1. Cargar Archivos de Piezas (.DXF)", "carica_input": "Arrastre sus archivos DXF aquí (Piezas Únicas)",
        "qta_titolo": "### Definir Cantidades de Producción", "qta_label": "Cantidad para", "errore_chiuso": "Imposible leer contorno. Verifique que sea cerrado.",
        "btn_calcola": "🚀 Ejecutar Nesting de Encastre Real", "errore_no_file": "¡Por favor cargue al menos un archivo DXF válido!",
        "resa": "Rendimiento Neto de Chapa", "sfrido": "Total Chatarra / Residuo", "tab_titolo": "📋 Lista de Piezas Mapeadas",
        "esporta": "💾 Exportar o Entregar al Departamento", "btn_csv": "📥 Descargar Reporte CSV", "btn_pdf": "🖨️ Imprimir o Exportar Mapa en PDF"
    },
    "CZ": {
        "titolo": "📐 MetalHub - Dílenská Suite", "dati_commessa": "📋 Údaje o Zakázce",
        "ordine": "Číslo Objednávky", "cliente": "Název Zákazníka", "data": "Datum", "sottotitolo": "Plán Řezání Plechu",
        "param_lamiera": "⚙️ Reálné Rozměry Plechu (mm)", "larg": "Šířka Plechu X (mm)", "alt": "Výška Plechu Y (mm)",
        "param_macchina": "🔧 Parametry Nástroje a Tolerance", "fresa": "Průměr Frézy / Šířka Řezu (mm)",
        "sicurezza": "Bezpečnostní Vzdálenost mezi díly (mm)", "passo": "Krok Skenování Skládání (mm)",
        "carica_titolo": "1. Načíst Soubory Dílů (.DXF)", "carica_input": "Přetáhněte soubory DXF sem (Jednotlivé Díly)",
        "qta_titolo": "### Definovat Výrobní Množství", "qta_label": "Množství pro", "errore_chiuso": "Profil nelze přečíst. Zkontrolujte, zda je uzavřený.",
        "btn_calcola": "🚀 Spustit Skutečné Skládání", "errore_no_file": "Načtěte prosím alespoň jeden platný soubor DXF!",
        "resa": "Čistá Výtěžnost Plechu", "sfrido": "Celkový Odpad / Šrot", "tab_titolo": "📋 Seznam Umístěných Dílů",
        "esporta": "💾 Exportovat nebo Předat do Výroby", "btn_csv": "📥 Stáhnout CSV Report", "btn_pdf": "🖨️ Tisknout nebo Exportovat Mapu do PDF"
    },
    "HU": {
        "titolo": "📐 MetalHub - Műhely Suite", "dati_commessa": "📋 Megrendelés Adatai",
        "ordine": "Rendelésszám", "cliente": "Ügyfél Neve", "data": "Dátum", "sottotitolo": "Lemezvágási Terv",
        "param_lamiera": "⚙️ Valós Lemezméretek (mm)", "larg": "Lemez Szélesség X (mm)", "alt": "Lemez Magasság Y (mm)",
        "param_macchina": "🔧 Szerszámparaméterek és Toleranciák", "fresa": "Maró Átmérő / Vágási Szélesség (mm)",
        "sicurezza": "Biztonsági Távolság az alkatrészek között (mm)", "passo": "Beágyazási Szkennelési Lépés (mm)",
        "carica_titolo": "1. Alkatrész Fájlok Feltöltése (.DXF)", "carica_input": "Húzza ide a DXF fájlokat (Egyedi Alkatrészek)",
        "qta_titolo": "### Gyártási Mennyiségek Meghatározása", "qta_label": "Mennyiség ehhez:", "errore_chiuso": "Profil nem olvasható. Ellenőrizze, hogy zárt hurok-e.",
"btn_calcola": "🚀 Valódi Beágyazás Indítása", "errore_no_file": "Kérjük, töltsön fel legalább egy érvényes DXF fájlt!","resa": "Nettó Lemezkihasználás", "sfrido": "Teljes Hulladék / Selejt", "tab_titolo": "📋 Beágyazott Alkatrészek Listája","esporta": "💾 Exportálás vagy Átadás a Műhelynek", "btn_csv": "📥 CSV Jelentés Letöltése", "btn_pdf": "🖨️ Térkép Nyomtatása vagy PDF-be Mentése"},"RO": {"titolo": "📐 MetalHub - Suite Atelier", "dati_commessa": "📋 Date Comandă","ordine": "Număr Comandă", "cliente": "Nume Client", "data": "Dată", "sottotitolo": "Plan de Tăiere Tablă","param_lamiera": "⚙️ Dimensiuni Reale Tablă (mm)", "larg": "Lățime Tablă X (mm)", "alt": "Înălțime Tablă Y (mm)","param_macchina": "🔧 Parametri Sculă și Toleranțe", "fresa": "Diametru Freză / Canat (mm)","sicurezza": "Distanța de Siguranță între piese (mm)", "passo": "Pas Scanare Imbricare (mm)","carica_titolo": "1. Încărcare Fișiere Piese (.DXF)", "carica_input": "Trageți fișierele DXF aici (Piese Singure)","qta_titolo": "### Definire Cantități de Producție", "qta_label": "Cantitate pentru", "errore_chiuso": "Profilul nu poate fi citit. Verificați să fie închis.","btn_calcola": "🚀 Lansează Imbricarea cu Încastrare Reală", "errore_no_file": "Vă rugăm să încărcați cel puțin un fișier DXF valid!","resa": "Randament Net Tablă", "sfrido": "Total Deșeu / Șrapnel", "tab_titolo": "📋 Listă Piese Imbricate","esporta": "💾 Exportă sau Trimite la Atelier", "btn_csv": "📥 Descarcă Raport CSV", "btn_pdf": "🖨️ Tipărește sau Exportă Harta în PDF"},"PT": {"titolo": "📐 MetalHub - Suite de Oficina", "dati_commessa": "📋 Dados da Encomenda","ordine": "Número do Pedido", "cliente": "Nome do Cliente", "data": "Data", "sottotitolo": "Plano de Corte de Chapa","param_lamiera": "⚙️ Dimensões Reais da Chapa (mm)", "larg": "Largura da Chapa X (mm)", "alt": "Altura da Chapa Y (mm)","param_macchina": "🔧 Parámetros de Ferramenta & Tolerâncias", "fresa": "Diámetro da Fresa / Canal (mm)","sicurezza": "Distância de Segurança entre peças (mm)", "passo": "Passo de escaneamento de Nesting (mm)","carica_titolo": "1. Carregar Arquivos de Peças (.DXF)", "carica_input": "Arraste os arquivos DXF aqui (Peças Únicas)","qta_titolo": "### Definir Quantidades de Produção", "qta_label": "Quantidade para", "errore_chiuso": "Impossível ler o perfil. Verifique se está fechado.","btn_calcola": "🚀 Executar Nesting de Encaixe Real", "errore_no_file": "Por favor, carregue pelo menos um arquivo DXF válido!","resa": "Rendimento Líquido da Chapa", "sfrido": "Total Sucata / Desperdício", "tab_titolo": "📋 Lista de Peças Mapeadas","esporta": "💾 Exportar ou Entregar ao Setor", "btn_csv": "📥 Baixar Relatório CSV", "btn_pdf": "🖨️ Imprimir ou Exportar Mapa em PDF"}}CONFIGURATORE LINGUA MENU ACCOUNT IN ALTO NELLA SIDEBARst.sidebar.markdown("### 👤 User Account & Setup")lingua_codice = st.sidebar.selectbox("🌍 Language / Lingua",options=["IT", "GB", "FR", "DE", "ES", "CZ", "HU", "RO", "PT"],format_func=lambda x: {"IT": "🇮🇹 Italiano", "GB": "🇬🇧 English", "FR": "🇫🇷 Français","DE": "🇩🇪 Deutsch", "ES": "🇪🇸 Español", "CZ": "🇨🇿 Čeština","HU": "🇭🇺 Magyar", "RO": "🇷🇴 Română", "PT": "🇵🇹 Português"}[x])L = TRADUZIONI[lingua_codice]--- DATI SCHEDA ---st.subheader(L["dati_commessa"])col_h1, col_h2, col_h3 = st.columns(3)with col_h1: num_ordine = st.text_input(L["ordine"], value="ORD-2D-001")with col_h2: nome_cliente = st.text_input(L["cliente"], value="Customer Metal SpA")with col_h3: data_commessa = st.date_input(L["data"], date.today())st.markdown(f"""{L["sottotitolo"]}: {num_ordine} | {L["cliente"]}: {nome_cliente} | {L["data"]}: {data_commessa.strftime('%d/%m/%Y')}""", unsafe_allow_html=True)PARAMETRI IN SIDEBARst.sidebar.header(L["param_lamiera"])W_lamiera = st.sidebar.number_input(L["larg"], value=1000, step=100)H_lamiera = st.sidebar.number_input(L["alt"], value=1000, step=100)st.sidebar.header(L["param_macchina"])diametro_utensile = st.sidebar.number_input(L["fresa"], value=6.0, step=1.0)distanza_sicurezza = st.sidebar.number_input(L["sicurezza"], value=4.0, step=1.0)passo_scansione = st.sidebar.slider(L["passo"], min_value=2, max_value=25, value=10, step=1)offset_totale = (diametro_utensile / 2.0) + distanza_sicurezzaFUNZIONE DI PARSING CON TRASLAZIONE AUTOMATICA SULL'ORIGINE (0,0)def estrai_e_azzera_poligono_da_dxf(file_bytes):try:string_io = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))doc = ezdxf.read(string_io)msp = doc.modelspace()linee_e_archi = []for e in msp.query('LINE'):linee_e_archi.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))for e in msp.query('LWPOLYLINE POLYLINE'):punti = [(p, p) for p in e.vertices()]if len(punti) >= 3: linee_e_archi.append(LineString(punti))unione = unary_union(linee_e_archi)poly = Noneif unione.geom_type == 'Polygon': poly = unioneelse:coords = []for line in linee_e_archi: coords.extend(line.coords)if len(coords) >= 3: poly = Polygon(coords)if poly:minx, minny, _, _ = poly.bounds# Sposta l'angolo d'ingombro del pezzo CAD a (0,0) puliti per rimuovere scostamenti remotipoly_centrato = affinity.translate(poly, xoff=-minx, yoff=-minny)return poly_centratoreturn Noneexcept:return NoneSEZIONE CARICAMENTOst.header(L["carica_titolo"])file_caricati = st.file_uploader(L["carica_input"], type=["dxf"], accept_multiple_files=True)lista_particolari = []if file_caricati:st.write(L["qta_titolo"])for f in file_caricati:poly = estrai_e_azzera_poligono_da_dxf(f.getvalue())if poly:minx, minny, maxx, maxy = poly.boundsw_p = maxx - minxh_p = maxy - minnycol_f1, col_f2 = st.columns(2)with col_f1:st.write(f"📄 {f.name}")st.caption(f"Dimensione: {round(w_p)} x {round(h_p)} mm")with col_f2:qta = st.number_input(f"{L['qta_label']} {f.name}", min_value=1, value=10, key=f"q_{f.name}")lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})if st.button(L["btn_calcola"], type="primary"):if not lista_particolari:st.error(L["errore_no_file"])else:coda_pezzi = []for p in lista_particolari:for _ in range(p["qta"]):coda_pezzi.append({"nome": p["nome"], "poly": p["poly"], "area": p["area"]})coda_pezzi.sort(key=lambda x: x["area"], reverse=True)bordo_utile = Polygon([(offset_totale, offset_totale), (W_lamiera - offset_totale, offset_totale),(W_lamiera - offset_totale, H_lamiera - offset_totale), (offset_totale, H_lamiera - offset_totale)])pezzi_piazzati_con_offset = []report_taglio = []area_utilizzata_reale = 0# RENDER GRAFICO MATPLOTLIBfig, ax = plt.subplots(figsize=(10, 10))ax.set_facecolor('#151515')fig.patch.set_facecolor('#111111')ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF4B4B", linewidth=3))nomi_unici = list(set([item["nome"] for item in coda_pezzi]))mappa_colori = cm.get_cmap('tab10', len(nomi_unici))color_dict = {nome: mappa_colori(idx) for idx, nome in enumerate(nomi_unici)}for item in coda_pezzi:poly_originale = item["poly"]piazzato = False# Elenco completo degli angoli cardinali di rotazione (Corretto)angoli_rotazione = [0, 45, 90, 135, 180, 225, 270, 315]for angolo in angoli_rotazione:if piazzato: breakpoly_ruotato = affinity.rotate(poly_originale, angolo, origin='center')poly_ruotato_offset = poly_ruotato.buffer(offset_totale)minx, minny, _, _ = poly_ruotato_offset.boundsfor y_test in range(int(offset_totale), int(H_lamiera), passo_scansione):if piazzato: breakfor x_test in range(int(offset_totale), int(W_lamiera), passo_scansione):x_shift = x_test - minxy_shift = y_test - minnyp_offset_testato = affinity.translate(poly_ruotato_offset, xoff=x_shift, yoff=y_shift)if bordo_utile.contains(p_offset_testato):collisione = Falsefor gia_piazzato_offset in pezzi_piazzati_con_offset:if p_offset_testato.intersects(gia_piazzato_offset):collisione = Truebreakif not collisione:p_reale_posizionato = affinity.translate(poly_ruotato, xoff=x_shift, yoff=y_shift)pezzi_piazzati_con_offset.append(p_offset_testato)area_utilizzata_reale += item["area"]piazzato = Truex_c, y_c = p_reale_posizionato.exterior.xyax.fill(x_c, y_c, alpha=0.8, color=color_dict[item["nome"]], edgecolor='black', linewidth=1.5)ax.text(p_reale_posizionato.centroid.x, p_reale_posizionato.centroid.y, item["nome"][:8],color="black", fontsize=8, weight="bold", ha="center", va="center",bbox=dict(boxstyle='round,pad=0.1', fc='white', alpha=0.6, ec='none'))report_taglio.append({"Articolo": item["nome"], "Rotazione": f"{angolo}°", "Area Pezzo (mm²)": round(item["area"], 1)})break# BLOCCO RIGIDO DEI CONFINIax.set_xlim(-50, W_lamiera + 50)ax.set_ylim(-50, H_lamiera + 50)ax.set_aspect('equal')ax.tick_params(colors='white')st.header("📊 Mappa Grafica del Nesting Ottimizzato")st.pyplot(fig)rendimento = (area_utilizzata_reale / (W_lamiera * H_lamiera)) * 100col_m1, col_m2 = st.columns(2)with col_m1: st.metric(label=L["resa"], value=f"{rendimento:.2f}%")with col_m2: st.metric(label=L["sfrido"], value=f"{100-rendimento:.2f}%")st.subheader(L["tab_titolo"])df_report_2d = pd.DataFrame(report_taglio)st.dataframe(df_report_2d, use_container_width=True)st.header(L["esporta"])col_exp1, col_exp2 = st.columns(2)with col_exp1:csv_2d = df_report_2d.to_csv(index=False).encode('utf-8')st.download_button(label=L["btn_csv"], data=csv_2d, file_name=f'Report_Nesting_{num_ordine}.csv', mime='text/csv')with col_exp2:st.markdown(f'{L["btn_pdf"]}', unsafe_allow_html=True)
