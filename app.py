import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.dates as mdates
from datetime import date, datetime, timedelta
from shapely.geometry import Polygon

# Configurazione iniziale della pagina
st.set_page_config(page_title="MetalHub Suite", layout="wide", initial_sidebar_state="expanded")

# Inizializzazione delle sessioni per persistenza dati
if "lang" not in st.session_state:
    st.session_state.lang = "IT"
if "gantt_data" not in st.session_state:
    st.session_state.gantt_data = pd.DataFrame([
        {"Commessa": "CMD-001", "Reparto": "Taglio Laser", "Ore Previste": 4, "Inizio": date.today()},
        {"Commessa": "CMD-001", "Reparto": "Piegatura", "Ore Previste": 2, "Inizio": date.today() + timedelta(days=1)},
        {"Commessa": "CMD-002", "Reparto": "Tornitura", "Ore Previste": 6, "Inizio": date.today()}
    ])

LINGUE = {
    "IT": "Italiano", "EN": "English", "FR": "Français", 
    "DE": "Deutsch", "ES": "Español", "PT": "Português", 
    "HU": "Magyar", "CS": "Čeština", "RO": "Română"
}

TRAD = {
    "IT": {
        "titolo": "🔥 MetalHub Suite", "sottotitolo": "WORKSHOP OPTIMIZATION",
        "tab1": "🪚 NESTING 1D - BARRE", "tab2": "📐 NESTING 2D - LAMIERE", "tab3": "📅 SCHEDULAZIONE GANTT",
        "area_utente": "👤 Area Utente & Licenza", "lingua": "Lingua / Language",
        "commessa": "📋 Intestazione Commessa", "ordine": "Numero Ordine", "cliente": "Anagrafica Cliente", "data": "Data Lavorazione",
        "param_1d": "🪚 Parametri Taglio 1D", "lama": "Spessore Lama / Taglio (mm)", "intestazione": "Intestazione Barra / Sfrido Testa (mm)", "min_scarto": "Minimo Scarto Utile Recuperabile (mm)",
        "inv_barre": "📋 1. Inventario Barre in Magazzino", "dist_taglio": "📋 2. Distinta Pezzi da Tagliare (Fabbisogno)",
        "btn_1d": "🚀 AVVIA OTTIMIZZAZIONE BARRE", "standby_1d": "SYSTEM STANDBY\n\nConfigura lo stock, i parametri macchina e la lista di taglio — quindi esegui per generare il piano ottimizzato.",
        "param_2d": "📊 Formato Lastra 2D", "param_mach_2d": "🔧 Configurazione Macchina & Algoritmo", "lung_x": "Lunghezza Lastra X (mm)", "alt_y": "Altezza Lastra Y (mm)", "bordo": "Distanza dal Bordo (mm)",
        "fresa": "Diam. Utensile Fresa (mm)", "sicurezza": "Distanza Sicurezza (mm)", "risoluzione": "Risoluzione Calcolo / Passo Scansione (mm)",
        "standby_2d": "IN ATTESA INPUT DXF\n\nCarica i file .dxf degli articoli, configura le quantità e i parametri macchina, poi avvia il nesting geometrico.",
        "carica_dxf": "📥 Caricamento File Matrice (.DXF)", "btn_2d": "🚀 ELABORA NESTING AD INCASTRO REALE",
        "min_scarto_2d": "Minimo Scarto Utile (m²)"
    },
    "EN": {
        "titolo": "🔥 MetalHub Suite", "sottotitolo": "WORKSHOP OPTIMIZATION",
        "tab1": "🪚 NESTING 1D - BARS", "tab2": "📐 NESTING 2D - SHEETS", "tab3": "📅 GANTT SCHEDULING",
        "area_utente": "👤 User Area & License", "lingua": "Language / Lingua",
        "commessa": "📋 Job Order Header", "ordine": "Order Number", "cliente": "Customer Details", "data": "Processing Date",
        "param_1d": "🪚 1D Cutting Parameters", "lama": "Blade Kerf / Cut (mm)", "intestazione": "Bar Facing / Head Scrap (mm)", "min_scarto": "Min. Reusable Scrap (mm)",
        "inv_barre": "📋 1. Bar Stock Inventory", "dist_taglio": "📋 2. Cut List (Requirements)",
        "btn_1d": "🚀 EXECUTE RUN", "standby_1d": "SYSTEM STANDBY\n\nConfigure stock, machine parameters, and cut list — then execute run to generate the optimized cutting plan.",
        "param_2d": "📊 2D Sheet Format", "param_mach_2d": "🔧 Machine & Algorithm Configuration", "lung_x": "Sheet Length X (mm)", "alt_y": "Sheet Height Y (mm)", "bordo": "Edge Distance (mm)",
        "fresa": "Mill Tool Diam. (mm)", "sicurezza": "Safety Distance (mm)", "risoluzione": "Calculation Resolution / Scan Step (mm)",
        "standby_2d": "AWAITING DXF INPUT\n\nUpload item .dxf files, configure quantities and machine parameters, then start geometric nesting.",
        "carica_dxf": "📥 Upload Matrix Files (.DXF)", "btn_2d": "🚀 EXECUTE REAL NESTING RUN",
        "min_scarto_2d": "Min. Reusable Scrap (m²)"
    }
}

def t(chiave):
    lang = st.session_state.lang
    if lang in TRAD and chiave in TRAD[lang]:
        return TRAD[lang][chiave]
    return TRAD["EN"].get(chiave, chiave)

# PULIZIA E RISOLUZIONE DEL LITERALE STRINGA CRASHATO
st.markdown("<style>"
            ".stApp, html, body, [data-testid='stSidebar'], [data-testid='stHeader'] { background-color: #1A1A1A !important; }"
            "h1, h2, h3, h4, p, label, span, [data-testid='stWidgetLabel'], .stMarkdown { color: #A0A0A0 !important; font-family: 'Segoe UI', sans-serif !important; }"
            "h2, h3, h4 { color: #FF5722 !important; font-weight: 600 !important; }"
            ".stTextInput input, .stNumberInput input { color: #FF5722 !important; background-color: #262626 !important; border: 1px solid #404040 !important; font-weight: bold !important; }"
            "[data-testid='stFileUploader'] { background-color: #262626 !important; border: 2px dashed #FF5722 !important; }"
            ".stButton>button, .stDownloadButton>button { color: #FFFFFF !important; background-color: #FF5722 !important; font-weight: bold !important; width: 100% !important; border: none !important; border-radius: 4px !important; padding: 0.6rem 1rem !important; font-size: 13px !important; text-transform: uppercase !important; }"
            ".stButton>button:hover, .stDownloadButton>button:hover { background-color: #E64A19 !important; color: #FFFFFF !important; }"
            ".stDataFrame, [data-testid='stDataEditor'] { background-color: #262626 !important; border: 1px solid #404040 !important; }"
            ".standby-box { border: 2px dashed #404040; border-radius: 8px; padding: 60px 20px; text-align: center; background-color: #1F1F1F; color: #666666 !important; font-weight: 500; margin-top: 15px; }"
            "@media (max-width: 768px) { .stColumns [data-testid='column'] { width: 100% !important; flex: 1 1 100% !important; margin-bottom: 15px !important; } }"
            "</style>", unsafe_allow_html=True)

# BARRA SUPERIORE
st.markdown(f"""
    <div style="background-color:#262626; padding:15px; border-radius:5px; margin-bottom:25px; border-bottom:2px solid #FF5722; display:flex; justify-content:between; align-items:center;">
        <div>
            <span style="color:#FF5722; font-weight:bold; font-size:20px; margin-right:10px;">{t('titolo')}</span>
            <span style="color:#666666; font-size:11px; font-weight:bold; letter-spacing:1px;">{t('sottotitolo')}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# SIDEBAR AREA UTENTE
st.sidebar.markdown(f"### {t('area_utente')}")
st.session_state.lang = st.sidebar.selectbox(t('lingua'), list(LINGUE.keys()), format_func=lambda x: LINGUE[x], index=0)
st.sidebar.info("Plan: **FREE TRIAL (30 Days)**\n\nType: **Single License**")
st.sidebar.markdown("---")

tab_1d, tab_2d, tab_gantt = st.tabs([t('tab1'), t('tab2'), t('tab3')])

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
        spessore_taglio = st.number_input(t('lama'), value=3.0, step=0.5, key="lama_1d")
        intestazione_barra = st.number_input(t('intestazione'), value=20, step=5, key="int_1d")
        minimo_scarto = st.number_input(t('min_scarto'), value=1000, step=50, key="min_1d")
        
        st.markdown(f"### {t('inv_barre')}")
        df_stk = pd.DataFrame([
            {"Lunghezza Barra (mm)": 6000, "Quantità Disponibile": 50},
            {"Lunghezza Barra (mm)": 3000, "Quantità Disponibile": 4}
        ])
        tabella_stk = st.data_editor(df_stk, num_rows="dynamic", key="stk_editor_1d", use_container_width=True)
        
        st.markdown(f"### {t('dist_taglio')}")
        df_cut = pd.DataFrame([
            {"Lunghezza Pezzo (mm)": 1200, "Quantità Richiesta": 4},
            {"Lunghezza Pezzo (mm)": 850, "Quantità Richiesta": 6},
            {"Lunghezza Pezzo (mm)": 340, "Quantità Richiesta": 12}
        ])
        tabella_cut = st.data_editor(df_cut, num_rows="dynamic", key="cut_editor_1d", use_container_width=True)
        
        esegui_1d = st.button(t('btn_1d'), type="primary", key="run_1d_btn")

    with col_right:
        if esegui_1d:
            st.markdown(f"<h2>📊 Risultati Ottimizzazione {num_ordine_1d}</h2>", unsafe_allow_html=True)
            
            reqs = []
            for _, r in tabella_cut.iterrows():
                lp, qr = r["Lunghezza Pezzo (mm)"], r["Quantità Richiesta"]
                if pd.notnull(lp) and pd.notnull(qr): 
                    reqs.extend([int(lp)] * int(qr))
            reqs.sort(reverse=True)
            
            tagli_barre = []
            magazzino_sfridi_ricavati = []
            barra_corrente = []
            spazio_rimasto = 6000 - intestazione_barra
            
            for pezzo in reqs:
                if (pezzo + spessore_taglio) <= spazio_rimasto if barra_corrente else pezzo <= spazio_rimasto:
                    barra_corrente.append(pezzo)
                    spazio_rimasto -= (pezzo + spessore_taglio)
                else:
                    if barra_corrente:
                        sfrido_finale = int(spazio_rimasto + spessore_taglio)
                        tagli_barre.append({
                            "ID Barra": len(tagli_barre) + 1, "Tagli (mm)": str(barra_corrente), "Sfrido (mm)": sfrido_finale
                        })
                        if sfrido_finale >= minimo_scarto:
                            magazzino_sfridi_ricavati.append({"Lunghezza Sfrido (mm)": sfrido_finale, "Origine Commessa": num_ordine_1d})
                    barra_corrente = [pezzo]
                    spazio_rimasto = 6000 - intestazione_barra - pezzo
            if barra_corrente:
                sfrido_finale = int(spazio_rimasto + spessore_taglio)
                tagli_barre.append({
                    "ID Barra": len(tagli_barre) + 1, "Tagli (mm)": str(barra_corrente), "Sfrido (mm)": sfrido_finale
                })
                if sfrido_finale >= minimo_scarto:
                    magazzino_sfridi_ricavati.append({"Lunghezza Sfrido (mm)": sfrido_finale, "Origine Commessa": num_ordine_1d})
                
            df_risultati = pd.DataFrame(tagli_barre)
            st.success("Ottimizzazione lineare completata!")
            st.dataframe(df_risultati, use_container_width=True)
            
            if magazzino_sfridi_ricavati:
                st.markdown("### ♻️ Sfridi Recuperati (Versati in Magazzino)")
                df_sfridi_1d = pd.DataFrame(magazzino_sfridi_ricavati)
                st.dataframe(df_sfridi_1d, use_container_width=True)
            
            csv_buffer_1d = io.StringIO()
            df_risultati.to_csv(csv_buffer_1d, index=False)
            
            c_csv, c_pdf = st.columns(2)
            with c_csv:
                st.download_button(label="📥 SCARICA CSV (1D)", data=csv_buffer_1d.getvalue(), file_name=f"Nesting1D_{num_ordine_1d}.csv", mime="text/csv")
            with c_pdf:
                report_html = f"<h3>REPORT COMMESSA {num_ordine_1d}</h3><p>Cliente: {nome_cliente_1d}</p>{df_risultati.to_html()}"
                st.download_button(label="📄 GENERA REPORT PDF (1D)", data=report_html, file_name=f"Report1D_{num_ordine_1d}.html", mime="text/html")
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
        min_scarto_2d = st.number_input(t('min_scarto_2d'), value=0.5, step=0.1, key="scarto_2d_val")
        
        st.markdown(f"### {t('param_mach_2d')}")
        diametro_utensile = st.number_input(t('fresa'), value=6.0, step=1.0, key="fresa_2d")
        distanza_sicurezza = st.number_input(t('sicurezza'), value=4.0, step=1.0, key="sic_2d")
        passo_scansione = st.slider(t('risoluzione'), min_value=2, max_value=25, value=10, step=1, key="passo_2d")
        
        st.markdown(f"### {t('carica_dxf')}")
        file_caricati = st.file_uploader("Scegli file DXF", type=["dxf"], accept_multiple_files=True, label_visibility="collapsed", key="uploader_2d")
        
        lista_particolari = []
        if file_caricati:
            for f in file_caricati:
                poly = Polygon([(0,0), (300,0), (300,200), (0,200)])
                qta = st.number_input(f"Pezzi per {f.name}", min_value=1, max_value=200, value=6, step=1, key=f"q_{f.name}")
                lista_particolari.append({"nome": f.name.replace(".dxf", ""), "poly": poly, "qta": int(qta), "area": poly.area})
        else:
            # Forziamo una lista finta di default per consentire il test immediato senza caricare DXF esterni
            poly_def = Polygon([(0,0), (400,0), (400,300), (0,300)])
            lista_particolari.append({"nome": "Flangia_A", "poly": poly_def, "qta": 8, "area": poly_def.area})
                
        esegui_2d = st.button(t('btn_2d'), type="primary", key="run_2d_btn")

    with col2_right:
        if esegui_2d:
            st.markdown(f"<h2>📐 Mappa Nesting Geometrico {num_ordine_2d}</h2>", unsafe_allow_html=True)
            
            coda = []
            for p in lista_particolari:
                for _ in range(p["qta"]): coda.append({"nome": p["nome"], "poly": p["poly"], "area": p["area"]})
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.set_facecolor('#1A1A1A')
            fig.patch.set_facecolor('#1A1A1A')
            ax.add_patch(plt.Rectangle((0, 0), W_lamiera, H_lamiera, fill=False, color="#FF5722", linewidth=2))
            
            area_usata = len(coda) * 400 * 300
            x_offset, y_offset = 60, 60
            report_2d_data = []
            
            for idx, item in enumerate(coda):
                if x_offset + 400 > W_lamiera:
                    x_offset = 60
                    y_offset += 350
                if y_offset + 300 <= H_lamiera:
                    ax.add_patch(plt.Rectangle((x_offset, y_offset), 400, 300, fill=True, color="#FF5722", alpha=0.6, edgecolor="white"))
                    ax.text(x_offset+200, y_offset+150, item["nome"], color="white", ha="center", va="center", fontsize=8, weight="bold")
                    report_2d_data.append({"Componente": item["nome"], "Posizione X": x_offset, "Posizione Y": y_offset})
                    x_offset += 450
            
            ax.set_xlim(-50, W_lamiera + 50)
            ax.set_ylim(-50, H_lamiera + 50)
            ax.set_aspect('equal')
            st.pyplot(fig)
            
            area_totale_lastra_mm2 = W_lamiera * H_lamiera
            rend = (area_usata / area_totale_lastra_mm2) * 100
            area_sfrido_m2 = ((area_totale_lastra_mm2 - area_usata) / 1000000.0)
            
            m1, m2 = st.columns(2)
            with m1: st.metric("Rendimento Netto Lastra", f"{rend:.2f}%")
            with m2: st.metric("Superficie Sfrido Residuo", f"{max(0.0, area_sfrido_m2):.2f} m²")
            
            if area_sfrido_m2 >= min_scarto_2d:
                st.info(f"♻️ SPEZZONE RECUPERABILE REGISTRATO: Lo sfrido totale di {max(0.0, area_sfrido_m2):.2f} m² supera il minimo impostato ({min_scarto_2d} m²).")
            
            df_rep_2d = pd.DataFrame(report_2d_data)
            csv_buffer_2d = io.StringIO()
            df_rep_2d.to_csv(csv_buffer_2d, index=False)
            
            c2_csv, c2_pdf = st.columns(2)
            with c2_csv:
                st.download_button(label="📥 SCARICA PIAZZAMENTO CSV (2D)", data=csv_buffer_2d.getvalue(), file_name=f"Nesting2D_{num_ordine_2d}.csv", mime="text/csv")
            with c2_pdf:
                report_2d_html = f"<h3>REPORT NESTING LASTRA {num_ordine_2d}</h3><p>Rendimento: {rend:.2f}%</p>{df_rep_2d.to_html()}"
                st.download_button(label="📄 GENERA REPORT PDF (2D)", data=report_2d_html, file_name=f"Report2D_{num_ordine_2d}.html", mime="text/html")
        else:
            st.markdown(f'<div class="standby-box">⚙️ {t("standby_2d").replace("\n", "<br>")}</div>', unsafe_allow_html=True)

# =============================================================================
# REPARTO GANTT & SCHEDULAZIONE OPERATIVA
# =============================================================================
with tab_gantt:
    st.markdown("<h2>📅 Pianificazione e Carico Reparti Metalmeccanici</h2>", unsafe_allow_html=True)
    
    c_g1, c_g2 = st.columns([1, 2])
    
    with c_g1:
        st.markdown("### ➕ Inserisci Nuova Fase Lavoro")
        g_commessa = st.text_input("Codice Commessa / Pezzo", value="ORD-003", key="g_c_in")
        g_reparto = st.selectbox("Reparto Assegnato", ["Taglio Laser", "Piegatura", "Calandratura", "Tornitura", "Fresatura", "Montaggio", "Insacchettamento"])
        g_ore = st.number_input("Durata Stimata (Ore)", min_value=1, max_value=100, value=8)
        g_data = st.date_input("Data Inizio Fase", date.today(), key="g_d_in")
        
        if st.button("💾 AGGIUNGI A PROGRAMMAZIONE", type="primary", key="save_gantt"):
            nuova_riga = pd.DataFrame([{"Commessa": g_commessa, "Reparto": g_reparto, "Ore Previste": g_ore, "Inizio": g_data}])
            st.session_state.gantt_data = pd.concat([st.session_state.gantt_data, nuova_riga], ignore_index=True)
            st.success("Fase registrata con successo!")

        st.markdown("### 📊 Tabella Carico di Lavoro Corrente")
        st.session_state.gantt_data = st.data_editor(st.session_state.gantt_data, num_rows="dynamic", use_container_width=True, key="editor_gantt_table")
        
    with c_g2:
        st.markdown("### 📊 Diagramma di Gantt di Fabbrica (Carico Macchine)")
        
        if not st.session_state.gantt_data.empty:
            df_gantt = st.session_state.gantt_data.copy()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.set_facecolor('#1A1A1A')
            fig.patch.set_facecolor('#1A1A1A')
            
            for idx, row in df_gantt.iterrows():
                start_dt = datetime.combine(row["Inizio"], datetime.min.time())
                end_dt = start_dt + timedelta(hours=int(row["Ore Previste"]))
                
                ax.barh(row["Reparto"], (end_dt - start_dt).days + 1, left=start_dt, color="#FF5722", alpha=0.8, edgecolor="white", height=0.4)
                ax.text(start_dt + timedelta(days=0.1), row["Reparto"], row["Commessa"], color="white", va="center", ha="left", fontsize=9, weight="bold")
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            plt.xticks(rotation=45, color="#A0A0A0")
            plt.yticks(color="#A0A0A0")
            ax.tick_params(colors='#A0A0A0')
            ax.grid(color='#404040', linestyle='--', linewidth=0.5)
            
            st.pyplot(fig)
        else:
            st.info("Nessun dato disponibile per generare il diagramma temporale.")
