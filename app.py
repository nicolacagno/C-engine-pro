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
