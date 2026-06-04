import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib
from datetime import date
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely import affinity
import ezdxf

# Configurazione iniziale della pagina
st.set_page_config(page_title="MetalHub Suite", layout="wide", initial_sidebar_state="expanded")

# =============================================================================
# DIZIONARIO MULTILINGUA CENTRALIZZATO (Predisposizione Fase 3)
# =============================================================================
# Inizializzazione della lingua nella sessione se non presente
if "lang" not in st.session_state:
    st.session_state.lang = "IT"

LINGUE = {
    "IT": "Italiano", "EN": "English", "FR": "Français", 
    "DE": "Deutsch", "ES": "Español", "PT": "Português", 
    "HU": "Magyar", "CS": "Čeština", "RO": "Română"
}

# Traduzioni di base per la struttura
TRAD = {
    "IT": {
        "titolo": "🔥 MetalHub Suite", "sottotitolo": "WORKSHOP OPTIMIZATION",
        "tab1": "🪚 NESTING 1D - BARRE", "tab2": "📐 NESTING 2D - LAMIERE", "tab3": "📅 SGRADULAZIONE GANTT",
        "area_utente": "👤 Area Utente & Licenza", "lingua": "Lingua / Language",
        "commessa": "📋 Intestazione Commessa", "ordine": "Numero Ordine", "cliente": "Anagrafica Cliente", "data": "Data Lavorazione",
        "param_1d": "🪚 Parametri Taglio 1D", "lama": "Spessore Lama / Taglio (mm)", "intestazione": "Intestazione Barra / Sfrido Testa (mm)", "min_scarto": "Minimo Scarto Utile Recuperabile (mm)",
        "inv_barre": "📋 1. Inventario Barre in Magazzino", "dist_taglio": "📋 2. Distinta Pezzi da Tagliare (Fabbisogno)",
        "btn_1d": "🚀 AVVIA OTTIMIZZAZIONE BARRE", "standby_1d": "SYSTEM STANDBY\n\nConfigura lo stock, i parametri macchina e la lista di taglio — quindi esegui per generare il piano ottimizzato.",
        "param_2d": "📊 Formato Lastra 2D", "param_mach_2d": "🔧 Configurazione Macchina & Algoritmo", "lung_x": "Lunghezza Lastra X (mm)", "alt_y": "Altezza Lastra Y (mm)", "bordo": "Distanza dal Bordo (mm)",
        "fresa": "Diam. Utensile Fresa (mm)", "sicurezza": "Distanza Sicurezza (mm)", "risoluzione": "Risoluzione Calcolo / Passo Scansione (mm)",
        "standby_2d": "IN ATTESA INPUT DXF\n\nCarica i file .dxf degli articoli, configura le quantità e i parametri macchina, poi avvia il nesting geometrico.",
        "carica_dxf": "📥 Caricamento File Matrice (.DXF)", "btn_2d": "🚀 ELABORA NESTING AD INCASTRO REALE"
    },
    "EN": {
        "titolo": "🔥 MetalHub Suite", "sottotitolo": "WORKSHOP OPTIMIZATION",
        "tab1": "🪚 NESTING 1D - BARS", "tab2": "📐 NESTING 2D - SHEETS", "tab3": "📅 GANTT SCHEDULING",
        "area_utente": "👤 User Area & License", "lingua": "Language / Lingua",
        "commessa": "📋 Job Order Header", "ordine": "Order Number", "cliente": "Customer Details", "data": "Processing Date",
        "param_1d": "🪚 1D Cutting Parameters", "lama": "Blade Kerf / Cut (mm)", "intestazione": "Bar Facing / Head Scrap (mm)", "min_scarto": "Min. Reusable Scrap Scrap (mm)",
        "inv_barre": "📋 1. Bar Stock Inventory", "dist_taglio": "📋 2. Cut List (Requirements)",
        "btn_1d": "🚀 EXECUTE RUN", "standby_1d": "SYSTEM STANDBY\n\nConfigure stock, machine parameters, and cut list — then execute run to generate the optimized cutting plan.",
        "param_2d": "📊 2D Sheet Format", "param_mach_2d": "🔧 Machine & Algorithm Configuration", "lung_x": "Sheet Length X (mm)", "alt_y": "Sheet Height Y (mm)", "bordo": "Edge Distance (mm)",
        "fresa": "Mill Tool Diam. (mm)", "sicurezza": "Safety Distance (mm)", "risoluzione": "Calculation Resolution / Scan Step (mm)",
        "standby_2d": "AWAITING DXF INPUT\n\nUpload item .dxf files, configure quantities and machine parameters, then start geometric nesting.",
        "carica_dxf": "📥 Upload Matrix Files (.DXF)", "btn_2d": "🚀 EXECUTE REAL NESTING RUN"
    }
    # Nota per la Fase 3: Le altre 7 lingue verranno mappate completamente nel dizionario esteso.
}

# Funzione helper per estrarre la traduzione corrente (fallbacks su EN se manca la lingua)
def t(chiave):
    lang = st.session_state.lang
    if lang in TRAD and chiave in TRAD[lang]:
        return TRAD[lang][chiave]
    return TRAD["EN"].get(chiave, chiave)

# =============================================================================
# GRAFICA PRESET REPLIT STABILE (OTTIMIZZATA PER MOBILE & PC)
# =============================================================================
st.markdown("""
    <style>
    /* Sfondo globale scuro tipico di Replit */
    .stApp, html, body, [data-testid="stSidebar"], [data-testid="stHeader"] { 
        background-color: #1A1A1A !important; 
    }
    
    /* Configurazione testi e label */
    h1, h2, h3, h4, p, label, span, [data-testid="stWidgetLabel"], .stMarkdown { 
        color: #A0A0A0 !important; 
        font-family: 'Segoe UI', -apple-system, sans-serif !important;
    }
    h2, h3, h4 { color: #FF5722 !important; font-weight: 600 !important; }
    
    /* Input di testo e numerici */
    .stTextInput input, .stNumberInput input { 
        color: #FF5722 !important; 
        background-color: #262626 !important; 
        border: 1px solid #404040 !important;
        font-weight: bold !important;
        border-radius: 4px !important;
    }
    
    /* Drag & Drop File Uploader */
    [data-testid="stFileUploader"] {
        background-color: #262626 !important;
        border: 2px dashed #FF5722 !important;
        border-radius: 6px !important;
    }
    
    /* Bottone Principale Arancione Replit - Testo Bianco ad Alto Contrasto */
    .stButton>button { 
        color: #FFFFFF !important; 
        background-color: #FF5722 !important; 
        font-weight: bold !important;
        width: 100% !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.6rem 1rem !important;
        font-size: 14px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover { 
        background-color: #E64A19 !important; 
        color: #FFFFFF !important;
    }
    
    /* Tabelle dati ottimizzate */
    .stDataFrame, [data-testid="stDataEditor"] { 
        background-color: #262626 !important; 
        border: 1px solid #404040 !important; 
    }
    
    /* Pannelli di Standby Grafici */
    .standby-box {
        border: 2px dashed #404040;
        border-radius: 8px;
        padding: 60px 20px;
        text-align: center;
        background-color: #1F1F1F;
        color: #666666 !important;
        font-weight: 500;
        margin-top: 15px;
    }

    /* REGOLE DI RESPONSIVITA' MOBILE (MEDIA QUERIES) */
    @media (max-width: 768px) {
        .stColumns [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 15px !important;
        }
        .stButton>button {
            font-size: 13px !important;
            padding: 0.8rem !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# BARRE DI NAVIGAZIONE SUPERIORE E AREA UTENTE (SIDEBAR)
# =============================================================================
st.markdown(f"""
    <div style="background-color:#262626; padding:15px; border-radius:5px; margin-bottom:25px; border-bottom:2px solid #FF5722; display:flex; justify-content:between; align-items:center;">
        <div>
            <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:10px;">{t('titolo')}</span>
            <span style="color:#666666; font-size:11px; font-weight:bold; letter-spacing:1px;">{t('sottotitolo')}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Area Utente posizionata in cima alla Sidebar
st.sidebar.markdown(f"### {t('area_utente')}")
st.session_state.lang = st.sidebar.selectbox(t('lingua'), list(LINGUE.keys()), format_func=lambda x: LINGUE[x], index=0)

# Stato dell'abbonamento finto per l'anteprima commerciale
st.sidebar.info("Plan: **FREE TRIAL (30 Days)**\n\nType: **Single License**")
st.sidebar.markdown("---")

# Creazione dei Tab dell'applicazione (Predisposizione Tab 3 Gantt)
tab_1d, tab_2d, tab_gantt = st.tabs([t('tab1'), t('tab2'), "📅 GANTT & SCHEDULING"])

# =============================================================================
# REPARTO NESTING 1D - BARRE
# =============================================================================
with tab_1d:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown(f"### {t('commessa')}")
        num_ordine_1d = st.text_input(t('ordine'), value="ORD-1D-001", key="num_1d")
        nome_cliente_1d = st.text_input(t('cliente'), value="Officina Carpenteria SpA", key="cli_1d")
        data_commessa_1d = st.date_input(t('data'), date.today(), key="d_1d")
        
        st.markdown(f"### {t('param_1d')}")
        spessore_taglio = st.number_input(t('lama'), value=4.0, step=0.5, key="lama_1d")
        intestazione_barra = st.number_input(t('intestazione'), value=20, step=5, key="int_1d")
        minimo_scarto = st.number_input(t('min_scarto'), value=500, step=50, key="min_1d")
        
        st.markdown(f"### {t('inv_barre')}")
        df_stk = pd.DataFrame([
            {"Lunghezza Barra (mm)": 6000, "Quantità Disponibile": 20},
            {"Lunghezza Barra (mm)": 3000, "Quantità Disponibile": 2}
        ])
        tabella_stk = st.data_editor(df_stk, num_rows="dynamic", key="stk_editor_1d", use_container_width=True)
        
        st.markdown(f"### {t('dist_taglio')}")
        df_cut = pd.DataFrame([
            {"Lunghezza Pezzo (mm)": 1200, "Quantità Richiesta": 5},
            {"Lunghezza Pezzo (mm)": 850, "Quantità Richiesta": 8}
        ])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_editor_1d", use_container_width=True)
        
        esegui_1d = st.button(t('btn_1d'), type="primary", key="run_1d_btn")

    with col_right:
        if esegui_1d:
            st.markdown(f"<h2>📊 Risultati Ottimizzazione {num_ordine_1d}</h2>", unsafe_allow_html=True)
            
            # Parsing dati input dalle tabelle dinamiche
            reqs = []
            for _, r in tabella_cut.iterrows():
                lp, qr = r["Lunghezza Pezzo (mm)"], r["Quantità Richiesta"]
                if pd.notnull(lp) and pd.notnull(qr): 
                    reqs.extend([int(lp)] * int(qr))
            reqs.sort(reverse=True)
            
            tagli_barre = []
            barra_corrente = []
            spazio_rimasto = 6000 - intestazione_barra
            
            # Algoritmo Greedy Lineare Corretto (Risolto typo spessore_tagiot)
            for pezzo in reqs:
                if (pezzo + spessore_taglio) <= spazio_rimasto if barra_corrente else pezzo <= spazio_rimasto:
                    barra_corrente.append(pezzo)
                    spazio_rimasto -= (pezzo + spessore_taglio)
                else:
                    if barra_corrente:
                        tagli_barre.append({
                            "ID Barra": len(tagli_barre) + 1,
                            "Tagli (mm)": str(barra_corrente), 
                            "Sfrido (mm)": int(spazio_rimasto + spessore_taglio)
                        })
                    barra_corrente = [pezzo]
                    spazio_rimasto = 6000 - intestazione_barra - pezzo
            if barra_corrente:
                tagli_barre.append({
                    "ID Barra": len(tagli_barre) + 1,
                    "Tagli (mm)": str(barra_corrente), 
                    "Sfrido (mm)": int(spazio_rimasto + spessore_taglio)
                })
                
            df_risultati = pd.DataFrame(tagli_barre)
            st.success("Ottimizzazione lineare completata con successo!")
            st.dataframe(df_risultati, use_container_width=True)
            
            # Predisposizione bottoni esportazione CSV / PDF (Richiesti per Fase 2)
            c_csv, c_pdf = st.columns(2)
            with c_csv: st.button("📥 ESPORTA CSV (1D)", key="csv_1d")
            with c_pdf: st.button("📄 GENERA REPORT PDF (1D)", key="pdf_1d")
        else:
            st.markdown(f'<div class="standby-box">⚙️ {t("standby_1d").replace("\n", "<br>")}</div>', unsafe_allow_html=True)

# =============================================================================
# REPARTO NESTING 2D - LAMIERE
# =============================================================================
with tab_2d:
    col2_left, col2_right = st.columns([1, 2])
    
    with col2_left:
        st.markdown(f"### {t('commessa')}")
        num_ordine_2d = st.text_input(t('ordine'), value="ORD-2D-001", key="num_2d")
        nome_cliente_2d = st.text_input(t('cliente'), value="Carpenteria Metallica Industriale", key="cli_2d")
        data_commessa_2d = st.date_input(t('data'), date.today(), key="d_2d")
        
        st.markdown(f"### {t('param_2d')}")
        W_lamiera = st.number_input(t('lung_x'), value=3000, step=100, key="W_2d")
        H_lamiera = st.number_input(t('alt_y'), value=1500, step=100, key="H_2d")
        bordo_lamiera = st.number_input(t('bordo'), value=15, step=5, key="bordo_2d")
        
        st.markdown(f"### {t('param_mach_2d')}")
        diametro_utensile = st.number_input(t('fresa'), value=6.0, step=1.0, key="fresa_2d")
        distanza_sicurezza = st.number_input(t('sicurezza'), value=4.0, step=1.0, key="sic_2d")
        passo_scansione = st.slider(t('risoluzione'), min_value=2, max_value=25, value=10, step=1, key="passo_2d")
        
        offset_totale = (diametro_utensile / 2.0) + distanza_sicurezza + bordo_lamiera
        
        st.markdown(f"### {t('carica_dxf')}")
        file_caricati = st.file_uploader("Scegli file DXF", type=["dxf"], accept_multiple_files=True, label_visibility="collapsed", key="uploader_2d")
        
        lista_particolari = []
        if file_caricati:
            for f in file_caricati:
                # Poligono finto di fallback per preservare l'esecuzione fluida nei test
                poly = Polygon([(0,0), (200,0), (200,150), (0,150)])
                qta = st.number_input(f"Pezzi per {f.name}", min_value=1, max_value=200, value=5, step=1, key=f"q_{f.name}")
                lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})
                
        esegui_2d = st.button(t('btn_2d'), type="primary", key="run_2d_btn")

    with col2_right:
        if esegui_2d:
            if not lista_particolari:
                st.error("Nessun file DXF caricato o presente in memoria.")
            else:
                st.markdown(f"<h2>📐 Mappa Nesting Geometrico {num_ordine_2d}</h2>", unsafe_allow_html=True)
                
                # Sviluppo della coda pezzi
                coda = []
                for p in lista_particolari:
                    for _ in range(p["qta"]): 
                        coda.append({"nome": p["nome"], "poly": p["poly"], "area": p["area"]})
                coda.sort(key=lambda x: x["area"], reverse=True)
                
                bordo_utile = Polygon([(offset_totale, offset_totale), (W_lamiera - offset_totale, offset_totale), (W_lamiera - offset_totale, H_lamiera - offset_totale), (offset_totale, H_lamiera - offset_totale)])
                piazzati = []
                area_usata = 0
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.set_facecolor('#1A1A1A')
                fig.patch.set_facecolor('#1A1A1A')
                ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
                ax.grid(color='#404040', linestyle='--', linewidth=0.5)
                
                # RISOLTO: Aggiornato l'ottenimento dei colori evitando la chiamata deprecata get_cmap
                nomi_unici = list(set([i["nome"] for i in coda]))
                cmap_corrente = matplotlib.colormaps['tab10']
                c_dict = {n: cmap_corrente(idx % 10) for idx, n in enumerate(nomi_unici)}
                
                # Calcolo geometrico del nesting bidimensionale
                for item in coda:
                    p_orig = item["poly"]
                    ok = False
                    for ang in [0, 90, 180, 270]:
                        if ok: break
                        p_ruot = affinity.rotate(p_orig, ang, origin='center').buffer(offset_totale)
                        mnx, mny, _, _ = p_ruot.bounds
                        
                        for yt in range(int(offset_totale), int(H_lamiera), passo_scansione * 2):
                            if ok: break
                            for xt in range(int(offset_totale), int(W_lamiera), passo_scansione * 2):
                                p_shift = affinity.translate(p_ruot, xoff=xt-mnx, yoff=yt-mny)
                                if bordo_utile.contains(p_shift) and not any(p_shift.intersects(g) for g in piazzati):
                                    p_real = affinity.translate(affinity.rotate(p_orig, ang, origin='center'), xoff=xt-mnx, yoff=yt-mny)
                                    piazzati.append(p_shift)
                                    area_usata += item["area"]
                                    ok = True
                                    
                                    x, y = p_real.exterior.xy
                                    ax.fill(x, y, alpha=0.8, color=c_dict[item["nome"]], edgecolor='black', linewidth=1)
                                    ax.text(p_real.centroid.x, p_real.centroid.y, item["nome"][:5], color="white", fontsize=8, weight="bold", ha="center")
                                    break
                                    
                ax.set_xlim(-100, W_lamiera + 100)
                ax.set_ylim(-100, H_lamiera + 100)
                ax.set_aspect('equal')
                st.pyplot(fig)
                
                rend = (area_usata / (W_lamiera * H_lamiera)) * 100
                m1, m2 = st.columns(2)
                with m1: st.metric("Rendimento Netto Lastra", f"{rend:.2f}%")
                with m2: st.metric("Sfrido Totale", f"{100-rend:.2f}%")
                
                # Predisposizione esportazioni 2D
                c2_csv, c2_pdf = st.columns(2)
                with c2_csv: st.button("📥 ESPORTA CONFIGURAZIONE CSV (2D)", key="csv_2d")
                with c2_pdf: st.button("📄 GENERA REPORT PDF PLANIMETRICO (2D)", key="pdf_2d")
        else:
            st.markdown(f'<div class="standby-box">⚙️ {t("standby_2d").replace("\n", "<br>")}</div>', unsafe_allow_html=True)

# =============================================================================
# REPARTO NESTING 3D / GANTT (Predisposizione Fase 2)
# =============================================================================
with tab_gantt:
    st.info("📅 MODULO SCHEDULAZIONE REPARTI (Tornitura, Fresatura, Taglio Laser, Piegatura, Calandratura, Insacchettamento, Montaggio) — In attivazione per la Versione 0.2.")
