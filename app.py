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
