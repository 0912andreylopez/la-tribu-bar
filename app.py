# -*- coding: utf-8 -*-
"""
Bar & Licorera — Sistema de gestión integral
Módulos: Dashboard · Mesas · Inventario · Caja · Nómina · Gastos · Proveedores · Balance · Reportes
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import os, hashlib, base64

# ─── RUTAS ───────────────────────────────────────────────────────────────────
# En Railway: variable de entorno DATA_DIR=/data  (volumen persistente)
# En local  : mismo directorio del script
DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(DATA_DIR, "bar.db")

st.set_page_config(
    page_title="La Tribu · Cafe Bar",
    page_icon="🪶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── LOGO HELPER ─────────────────────────────────────────────────────────────
def get_logo_b64():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ─── CSS PREMIUM — LA TRIBU ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Fondo global ── */
.stApp { background: #12141f; }
.main .block-container { padding-top: 1.5rem; }

/* ── Sidebar premium ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0f1a 0%, #12141f 60%, #0d0f1a 100%) !important;
    border-right: 1px solid #c8941a33;
}
[data-testid="stSidebar"] * { color: #e2c97e !important; }
[data-testid="stSidebar"] .stRadio label { color: #d1c5a0 !important; font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] hr { border-color: #c8941a44 !important; }

/* ── Marca en sidebar ── */
.tribu-brand {
    text-align: center;
    padding: 12px 0 8px 0;
    border-bottom: 1px solid #c8941a44;
    margin-bottom: 12px;
}
.tribu-brand .brand-name {
    font-family: 'Cinzel', serif;
    font-size: 22px;
    font-weight: 900;
    background: linear-gradient(135deg, #c8941a, #f5d07a, #c8941a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 3px;
    margin: 6px 0 2px 0;
    display: block;
}
.tribu-brand .brand-sub {
    font-size: 10px;
    color: #8a7450 !important;
    letter-spacing: 4px;
    text-transform: uppercase;
}
.tribu-logo-sidebar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 2px solid #c8941a66;
    object-fit: cover;
    display: block;
    margin: 0 auto;
}

/* ── KPI cards ── */
.kpi {
    background: linear-gradient(135deg, #1a1d2e 0%, #1e2135 100%);
    border-left: 4px solid #c8941a;
    padding: 14px 18px;
    border-radius: 12px;
    margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.kpi.green  { border-left-color: #22c55e; }
.kpi.red    { border-left-color: #ef4444; }
.kpi.yellow { border-left-color: #f59e0b; }
.kpi.purple { border-left-color: #a855f7; }
.kpi.orange { border-left-color: #f97316; }
.kpi.blue   { border-left-color: #3b82f6; }
.kpi.gold   { border-left-color: #c8941a; }
.kpi h4 { margin:0; font-size:10px; color:#8a7450; text-transform:uppercase; letter-spacing:.08em; font-family:'Inter',sans-serif; }
.kpi p  { margin:4px 0 0; font-size:26px; font-weight:800; color:#f5d07a; font-family:'Inter',sans-serif; }
.kpi small { color:#5a5033; font-size:11px; }

/* ── Mesas cards ── */
.mesa-card {
    background: linear-gradient(135deg, #1a1d2e, #1e2135);
    border-radius: 14px;
    padding: 20px 14px;
    margin: 6px 0;
    border: 2px solid #2a2d40;
    text-align: center;
    transition: transform 0.15s;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5);
}
.mesa-card:hover { transform: translateY(-2px); }
.mesa-titulo { font-size:19px; font-weight:800; color:#f5d07a; margin:0; font-family:'Inter',sans-serif; }
.mesa-estado { font-size:12px; margin:4px 0; font-weight:600; }
.mesa-info   { font-size:12px; color:#8a7450; margin:2px 0; }

/* ── Chips de persona ── */
.persona-chip {
    display:inline-block;
    background: #2a1e0a;
    border: 1px solid #c8941a66;
    color: #f5d07a !important;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    margin: 3px;
}

/* ── Badges ── */
.badge-admin  { background:#2a1e0a; color:#f5d07a; border:1px solid #c8941a; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-cajero { background:#0a2a15; color:#86efac; border:1px solid #22c55e66; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-barman { background:#2a0a0a; color:#fca5a5; border:1px solid #ef444466; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {
    color: #8a7450;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    color: #f5d07a !important;
    border-bottom: 2px solid #c8941a !important;
}

/* ── Botones ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #c8941a, #a87515) !important;
    border: none !important;
    color: #12141f !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    letter-spacing: 0.5px;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #f5d07a, #c8941a) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(200,148,26,0.4) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: #1a1d2e !important;
    border: 1px solid #2a2d40 !important;
    color: #e2c97e !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #c8941a !important;
    box-shadow: 0 0 0 2px rgba(200,148,26,0.2) !important;
}

/* ── Dataframe ── */
.stDataFrame { border-radius: 10px; overflow: hidden; }
[data-testid="stDataFrameResizable"] { border: 1px solid #2a2d40 !important; }

/* ── Divider ── */
hr { border-color: #2a2d4066 !important; }

/* ── Página de login ── */
.login-box {
    background: linear-gradient(145deg, #1a1d2e, #0d0f1a);
    border: 1px solid #c8941a33;
    border-radius: 20px;
    padding: 40px 36px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.7), 0 0 40px rgba(200,148,26,0.08);
    margin-top: 40px;
}
.login-titulo {
    font-family: 'Cinzel', serif;
    font-size: 34px;
    font-weight: 900;
    background: linear-gradient(135deg, #c8941a 0%, #f5d07a 50%, #c8941a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    letter-spacing: 5px;
    margin: 10px 0 4px 0;
}
.login-sub {
    text-align: center;
    color: #5a5033;
    font-size: 11px;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 24px;
}
.login-logo {
    display: block;
    margin: 0 auto 16px auto;
    width: 110px;
    border-radius: 50%;
    border: 3px solid #c8941a66;
    box-shadow: 0 0 30px rgba(200,148,26,0.3);
}
.ornament {
    text-align: center;
    color: #c8941a44;
    font-size: 14px;
    letter-spacing: 8px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── DB ──────────────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hsh(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'cajero',
            activo INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS categorias(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#3b82f6'
        );
        CREATE TABLE IF NOT EXISTS proveedores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL, contacto TEXT, telefono TEXT,
            email TEXT, nit TEXT, activo INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS productos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL,
            categoria_id INTEGER REFERENCES categorias(id),
            proveedor_id INTEGER REFERENCES proveedores(id),
            precio_venta REAL DEFAULT 0, precio_costo REAL DEFAULT 0,
            stock REAL DEFAULT 0, stock_minimo REAL DEFAULT 5,
            unidad TEXT DEFAULT 'unidad', activo INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS empleados(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL, cedula TEXT UNIQUE NOT NULL,
            cargo TEXT DEFAULT 'mesero', telefono TEXT,
            tarifa_hora REAL DEFAULT 0, activo INTEGER DEFAULT 1,
            fecha_ingreso TEXT
        );
        CREATE TABLE IF NOT EXISTS horas_trabajo(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id INTEGER REFERENCES empleados(id),
            fecha TEXT NOT NULL, hora_entrada TEXT, hora_salida TEXT,
            horas_trabajadas REAL DEFAULT 0, tipo TEXT DEFAULT 'normal',
            nota TEXT, pagado INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS pagos_nomina(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id INTEGER REFERENCES empleados(id),
            periodo_inicio TEXT NOT NULL, periodo_fin TEXT NOT NULL,
            horas_totales REAL NOT NULL, monto_total REAL NOT NULL,
            fecha_pago TEXT NOT NULL, metodo_pago TEXT DEFAULT 'efectivo',
            usuario TEXT
        );
        CREATE TABLE IF NOT EXISTS gastos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL, categoria TEXT NOT NULL,
            descripcion TEXT, monto REAL NOT NULL,
            metodo_pago TEXT DEFAULT 'efectivo', usuario TEXT
        );
        CREATE TABLE IF NOT EXISTS ventas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL, hora TEXT NOT NULL,
            total REAL NOT NULL, descuento REAL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'efectivo',
            usuario TEXT, nota TEXT, anulada INTEGER DEFAULT 0,
            origen TEXT DEFAULT 'caja'
        );
        CREATE TABLE IF NOT EXISTS detalle_ventas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER REFERENCES ventas(id),
            producto_id INTEGER REFERENCES productos(id),
            nombre_producto TEXT, cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL, subtotal REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS compras(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL, proveedor_id INTEGER REFERENCES proveedores(id),
            total REAL NOT NULL, nota TEXT, usuario TEXT
        );
        CREATE TABLE IF NOT EXISTS detalle_compras(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id INTEGER REFERENCES compras(id),
            producto_id INTEGER REFERENCES productos(id),
            nombre_producto TEXT, cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL, subtotal REAL NOT NULL
        );

        -- ── MESAS ─────────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS mesas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER NOT NULL,
            nombre TEXT,
            capacidad INTEGER DEFAULT 4,
            estado TEXT DEFAULT 'libre',   -- libre | ocupada | cuenta
            fecha_apertura TEXT,
            hora_apertura TEXT,
            usuario_apertura TEXT
        );
        CREATE TABLE IF NOT EXISTS personas_mesa(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mesa_id INTEGER REFERENCES mesas(id),
            nombre TEXT NOT NULL,
            activo INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS pedidos_mesa(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mesa_id INTEGER REFERENCES mesas(id),
            persona_id INTEGER REFERENCES personas_mesa(id),  -- NULL = compartido
            producto_id INTEGER REFERENCES productos(id),
            nombre_producto TEXT NOT NULL,
            cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            usuario TEXT,
            anulado INTEGER DEFAULT 0,
            ronda INTEGER DEFAULT 1
        );
        """)

        cur = c.cursor()
        cur.execute("SELECT COUNT(*) FROM usuarios")
        if cur.fetchone()[0] == 0:
            c.execute("INSERT INTO usuarios(username,password,rol) VALUES(?,?,?)",
                      ("admin", hsh("admin123"), "admin"))

        cur.execute("SELECT COUNT(*) FROM categorias")
        if cur.fetchone()[0] == 0:
            for cat, color in [
                ("Licores", "#8b5cf6"), ("Cervezas", "#f59e0b"),
                ("Vinos", "#ef4444"), ("Cócteles", "#ec4899"),
                ("Gaseosas y Jugos", "#22c55e"), ("Agua y Energizantes", "#06b6d4"),
                ("Snacks y Comida", "#f97316"), ("Otros", "#64748b"),
            ]:
                c.execute("INSERT INTO categorias(nombre,color) VALUES(?,?)", (cat, color))

        # Crear 12 mesas por defecto si no existen
        cur.execute("SELECT COUNT(*) FROM mesas")
        if cur.fetchone()[0] == 0:
            for i in range(1, 13):
                c.execute("INSERT INTO mesas(numero,nombre,capacidad,estado) VALUES(?,?,?,?)",
                           (i, f"Mesa {i}", 4, "libre"))
        c.commit()

init_db()

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def kpi(titulo, valor, sub="", color=""):
    cls = f"kpi {color}" if color else "kpi"
    return f'<div class="{cls}"><h4>{titulo}</h4><p>{valor}</p><small>{sub}</small></div>'

def fmt(v):
    try:    return f"$ {float(v):,.0f}"
    except: return "$ 0"

def qry(sql, p=(), one=False):
    with get_conn() as c:
        cur = c.execute(sql, p)
        return cur.fetchone() if one else cur.fetchall()

def exe(sql, p=()):
    with get_conn() as c:
        c.execute(sql, p)
        c.commit()

def df(sql, p=()):
    with get_conn() as c:
        return pd.read_sql_query(sql, c, params=list(p))

# ─── LOGIN ───────────────────────────────────────────────────────────────────
def login():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        logo_b64 = get_logo_b64()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="login-logo">' if logo_b64 else '<div style="text-align:center;font-size:48px;margin-bottom:8px;">🪶</div>'

        st.markdown(f"""
        <div class="login-box">
            {logo_html}
            <div class="login-titulo">LA TRIBU</div>
            <div class="login-sub">Cafe · Bar · Sistema de gestión</div>
            <div class="ornament">◆ · · · ◆ · · · ◆</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        u = st.text_input("👤  Usuario")
        p = st.text_input("🔒  Contraseña", type="password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INGRESAR", use_container_width=True, type="primary"):
            row = qry("SELECT username,rol FROM usuarios WHERE username=? AND password=? AND activo=1",
                      (u, hsh(p)), one=True)
            if row:
                st.session_state.user = row[0]
                st.session_state.rol  = row[1]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("🔑 Acceso inicial: admin · admin123")

# ─── DASHBOARD ───────────────────────────────────────────────────────────────
def page_dashboard():
    hoy = date.today().isoformat()
    st.markdown("## 🏠 Dashboard")
    st.caption(f"Hoy: {date.today().strftime('%A %d de %B de %Y')}")

    v_hoy  = qry("SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha=? AND anulada=0",(hoy,),one=True)[0]
    n_v    = qry("SELECT COUNT(*) FROM ventas WHERE fecha=? AND anulada=0",(hoy,),one=True)[0]
    g_hoy  = qry("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE fecha=?",(hoy,),one=True)[0]
    costo  = qry("""SELECT COALESCE(SUM(dv.cantidad*p.precio_costo),0)
                    FROM detalle_ventas dv JOIN ventas v ON dv.venta_id=v.id
                    JOIN productos p ON dv.producto_id=p.id
                    WHERE v.fecha=? AND v.anulada=0""",(hoy,),one=True)[0]
    util   = v_hoy - costo - g_hoy
    bajos  = qry("SELECT COUNT(*) FROM productos WHERE stock<=stock_minimo AND activo=1",one=True)[0]
    mesas_ocu = qry("SELECT COUNT(*) FROM mesas WHERE estado IN ('ocupada','cuenta')",one=True)[0]

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(kpi("Ventas hoy", fmt(v_hoy), f"{n_v} transacciones","green"),unsafe_allow_html=True)
    with c2: st.markdown(kpi("Gastos hoy", fmt(g_hoy), "operativos","red"),unsafe_allow_html=True)
    with c3: st.markdown(kpi("Utilidad estimada", fmt(util), "ventas-costo-gastos","green" if util>=0 else "red"),unsafe_allow_html=True)
    with c4: st.markdown(kpi("Mesas ocupadas", str(mesas_ocu), "en este momento","orange"),unsafe_allow_html=True)
    with c5: st.markdown(kpi("Alertas stock", str(bajos), "productos bajo mínimo","red" if bajos>0 else "green"),unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_izq, c_der = st.columns(2)

    with c_izq:
        st.markdown("#### 📈 Ventas últimos 7 días")
        d7 = df("""SELECT fecha, SUM(total) as total FROM ventas
                   WHERE anulada=0 AND fecha>=date('now','-6 days')
                   GROUP BY fecha ORDER BY fecha""")
        if not d7.empty:
            fig = px.bar(d7, x="fecha", y="total", color_discrete_sequence=["#3b82f6"],
                         labels={"fecha":"Fecha","total":"Total ($)"})
            fig.update_layout(paper_bgcolor="#1e293b",plot_bgcolor="#1e293b",
                              font_color="#cbd5e1",showlegend=False,margin=dict(t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin ventas registradas aún.")

    with c_der:
        st.markdown("#### 🏆 Más vendidos hoy")
        top = df("""SELECT dv.nombre_producto, SUM(dv.cantidad) as u, SUM(dv.subtotal) as t
                    FROM detalle_ventas dv JOIN ventas v ON dv.venta_id=v.id
                    WHERE v.fecha=? AND v.anulada=0
                    GROUP BY dv.nombre_producto ORDER BY u DESC LIMIT 8""", (hoy,))
        if not top.empty:
            fig2 = px.bar(top, x="u", y="nombre_producto", orientation="h",
                          color_discrete_sequence=["#22c55e"],
                          labels={"nombre_producto":"","u":"Unidades"})
            fig2.update_layout(paper_bgcolor="#1e293b",plot_bgcolor="#1e293b",
                               font_color="#cbd5e1",showlegend=False,margin=dict(t=10,b=10))
            st.plotly_chart(fig2, use_container_width=True)
        else: st.info("Sin ventas hoy.")

    if bajos > 0:
        st.divider()
        st.markdown("#### ⚠️ Productos con stock bajo")
        bajo_df = df("""SELECT p.codigo,p.nombre,c.nombre as cat,p.stock,p.stock_minimo,p.unidad
                        FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id
                        WHERE p.stock<=p.stock_minimo AND p.activo=1 ORDER BY p.stock""")
        st.dataframe(bajo_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  MESAS
# ═══════════════════════════════════════════════════════════════════════════════
def _estado_badge(estado):
    if estado == "libre":    return "🟢 Libre"
    if estado == "ocupada":  return "🟡 Ocupada"
    if estado == "cuenta":   return "🔴 Pidiendo cuenta"
    return estado

def _ronda_actual(mesa_id):
    r = qry("SELECT MAX(ronda) FROM pedidos_mesa WHERE mesa_id=? AND anulado=0",(mesa_id,),one=True)
    return (r[0] or 0)

def page_mesas():
    """Vista principal de mesas o detalle de una mesa abierta."""
    if "mesa_vista" not in st.session_state:
        st.session_state.mesa_vista = None

    if st.session_state.mesa_vista:
        _detalle_mesa(st.session_state.mesa_vista)
    else:
        _grid_mesas()

# ─── GRID DE MESAS ───────────────────────────────────────────────────────────
def _grid_mesas():
    st.markdown("## 🪑 Mesas")

    mesas_db = qry("""
        SELECT m.id, m.numero, m.nombre, m.estado, m.hora_apertura,
               (SELECT COUNT(*) FROM pedidos_mesa pm WHERE pm.mesa_id=m.id AND pm.anulado=0) as pedidos,
               (SELECT COALESCE(SUM(pm.subtotal),0) FROM pedidos_mesa pm WHERE pm.mesa_id=m.id AND pm.anulado=0) as total
        FROM mesas m ORDER BY m.numero""")

    col_add, col_esp = st.columns([1, 5])
    with col_add:
        with st.popover("➕ Agregar mesa"):
            with st.form("add_mesa_form"):
                num_m = st.number_input("Número", min_value=1, step=1)
                nom_m = st.text_input("Nombre (ej: Mesa VIP)")
                cap_m = st.number_input("Capacidad", min_value=1, value=4)
                if st.form_submit_button("Crear"):
                    exe("INSERT INTO mesas(numero,nombre,capacidad,estado) VALUES(?,?,?,'libre')",
                        (num_m, nom_m or f"Mesa {num_m}", cap_m))
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Mostrar en grilla de 4 columnas
    cols = st.columns(4)
    for idx, m in enumerate(mesas_db):
        mid, mnum, mnombre, mestado, mahora, mpedidos, mtotal = m
        col = cols[idx % 4]
        with col:
            color = {"libre":"#22c55e", "ocupada":"#f59e0b", "cuenta":"#ef4444"}.get(mestado,"#64748b")
            info  = f"{mpedidos} ítems · {fmt(mtotal)}" if mestado != "libre" else "Sin pedidos"
            hora  = f"Desde {mahora[:5]}" if mahora else ""

            st.markdown(f"""
            <div class="mesa-card" style="border-color:{color}">
              <p class="mesa-titulo" style="color:{color}">{mnombre}</p>
              <p class="mesa-estado" style="color:{color}">{_estado_badge(mestado)}</p>
              <p class="mesa-info">{info}</p>
              <p class="mesa-info">{hora}</p>
            </div>
            """, unsafe_allow_html=True)

            if mestado == "libre":
                if st.button("🔓 Abrir", key=f"abr_{mid}", use_container_width=True):
                    hoy = date.today().isoformat()
                    ahora = datetime.now().strftime("%H:%M:%S")
                    exe("UPDATE mesas SET estado='ocupada',fecha_apertura=?,hora_apertura=?,usuario_apertura=? WHERE id=?",
                        (hoy, ahora, st.session_state.user, mid))
                    st.session_state.mesa_vista = mid
                    st.rerun()
            else:
                if st.button("🔍 Ver / Gestionar", key=f"ver_{mid}", use_container_width=True):
                    st.session_state.mesa_vista = mid
                    st.rerun()

# ─── DETALLE DE MESA ─────────────────────────────────────────────────────────
def _detalle_mesa(mesa_id):
    mesa = qry("SELECT id,numero,nombre,estado,fecha_apertura,hora_apertura FROM mesas WHERE id=?",
               (mesa_id,), one=True)
    if not mesa:
        st.session_state.mesa_vista = None
        st.rerun()
        return

    mid, mnum, mnombre, mestado, mfecha, mahora = mesa

    # Cabecera
    col_back, col_title, col_estado = st.columns([1, 4, 2])
    with col_back:
        if st.button("← Volver a mesas"):
            st.session_state.mesa_vista = None
            st.rerun()
    with col_title:
        st.markdown(f"## 🪑 {mnombre}")
        st.caption(f"Abierta: {mfecha or ''} {mahora[:5] if mahora else ''}")
    with col_estado:
        color_e = {"ocupada":"orange","cuenta":"red","libre":"green"}.get(mestado,"blue")
        st.markdown(kpi("Estado", _estado_badge(mestado), "", color_e), unsafe_allow_html=True)

    st.divider()

    # Obtener personas de la mesa
    personas = qry("SELECT id,nombre FROM personas_mesa WHERE mesa_id=? AND activo=1 ORDER BY id", (mesa_id,))
    personas_dict = {p[1]: p[0] for p in personas}  # nombre -> id

    # Obtener total actual
    total_actual = qry("SELECT COALESCE(SUM(subtotal),0) FROM pedidos_mesa WHERE mesa_id=? AND anulado=0",
                       (mesa_id,), one=True)[0]
    ronda_actual = _ronda_actual(mesa_id) + 1

    tab_pedido, tab_personas, tab_cuenta = st.tabs(
        ["🍺 Agregar pedido", "👤 Personas en mesa", "🧾 Cuenta y cobro"])

    # ── TAB 1: AGREGAR PEDIDO ────────────────────────────────────────────────
    with tab_pedido:
        # Resumen rápido
        c1, c2 = st.columns(2)
        with c1: st.markdown(kpi("Total acumulado", fmt(total_actual), "todos los pedidos","green"), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Ronda actual", f"#{ronda_actual}", f"{len(personas)} personas en mesa","blue"), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"**Agregar pedido — Ronda #{ronda_actual}**")

        prods_disp = df("""SELECT p.id,p.nombre,p.precio_venta,c.nombre as cat
                           FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id
                           WHERE p.activo=1 AND p.stock>0 ORDER BY c.nombre,p.nombre""")

        if prods_disp.empty:
            st.warning("No hay productos disponibles en inventario.")
        else:
            # Inicializar carrito de mesa en session_state
            key_cart = f"cart_mesa_{mesa_id}"
            if key_cart not in st.session_state:
                st.session_state[key_cart] = []

            cats_disp = ["Todas"] + sorted(prods_disp["cat"].dropna().unique().tolist())
            cat_f = st.selectbox("Filtrar categoría", cats_disp, key=f"catf_{mesa_id}")
            pdf = prods_disp if cat_f == "Todas" else prods_disp[prods_disp["cat"] == cat_f]

            c1, c2, c3, c4 = st.columns([3, 1.5, 2, 1])
            opciones_prod = [f"{r['nombre']} — {fmt(r['precio_venta'])}" for _, r in pdf.iterrows()]
            sel_prod  = c1.selectbox("Producto", opciones_prod, key=f"sp_{mesa_id}")
            cant_item = c2.number_input("Cant.", min_value=1, value=1, step=1, key=f"ci_{mesa_id}")
            opciones_persona = ["Mesa (compartido)"] + [p[1] for p in personas]
            pers_sel  = c3.selectbox("Para quién", opciones_persona, key=f"ps_{mesa_id}")

            if c4.button("➕ Añadir", key=f"add_{mesa_id}", type="primary"):
                prod_nombre = sel_prod.split(" — ")[0]
                prod_row    = pdf[pdf["nombre"] == prod_nombre].iloc[0]
                pid         = int(prod_row["id"])
                precio      = float(prod_row["precio_venta"])
                persona_id  = personas_dict.get(pers_sel) if pers_sel != "Mesa (compartido)" else None
                st.session_state[key_cart].append({
                    "producto_id":  pid,
                    "nombre":       prod_nombre,
                    "cantidad":     cant_item,
                    "precio":       precio,
                    "subtotal":     cant_item * precio,
                    "persona_id":   persona_id,
                    "persona_nombre": pers_sel,
                })

            # Mostrar carrito pendiente
            cart = st.session_state[key_cart]
            if cart:
                st.markdown(f"**Carrito de esta ronda ({len(cart)} ítems):**")
                cart_df = pd.DataFrame([{
                    "Producto": i["nombre"],
                    "Cant.":    i["cantidad"],
                    "Precio":   fmt(i["precio"]),
                    "Subtotal": fmt(i["subtotal"]),
                    "Para":     i["persona_nombre"],
                } for i in cart])
                st.dataframe(cart_df, use_container_width=True, hide_index=True)
                total_cart = sum(i["subtotal"] for i in cart)
                st.markdown(f"**Total ronda: {fmt(total_cart)}**")

                c_env, c_vac = st.columns(2)
                with c_env:
                    if st.button("✅ Enviar pedido a mesa", type="primary", use_container_width=True):
                        hoy   = date.today().isoformat()
                        ahora = datetime.now().strftime("%H:%M:%S")
                        ronda = _ronda_actual(mesa_id) + 1
                        with get_conn() as conn:
                            for item in cart:
                                conn.execute("""INSERT INTO pedidos_mesa
                                    (mesa_id,persona_id,producto_id,nombre_producto,
                                     cantidad,precio_unitario,subtotal,fecha,hora,usuario,ronda)
                                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                                    (mesa_id, item["persona_id"], item["producto_id"],
                                     item["nombre"], item["cantidad"], item["precio"],
                                     item["subtotal"], hoy, ahora,
                                     st.session_state.user, ronda))
                                conn.execute("UPDATE productos SET stock=stock-? WHERE id=?",
                                             (item["cantidad"], item["producto_id"]))
                            conn.commit()
                        st.session_state[key_cart] = []
                        st.success(f"¡Ronda #{ronda} enviada a {mnombre}!")
                        st.rerun()
                with c_vac:
                    if st.button("🗑 Vaciar carrito", use_container_width=True):
                        st.session_state[key_cart] = []
                        st.rerun()

            # Historial de pedidos de esta mesa
            st.markdown("---")
            st.markdown("**Historial de pedidos de esta mesa:**")
            hist = df("""SELECT pm.ronda, pm.hora,
                                COALESCE(pe.nombre,'Mesa (compartido)') as para,
                                pm.nombre_producto, pm.cantidad,
                                pm.precio_unitario, pm.subtotal, pm.id
                         FROM pedidos_mesa pm
                         LEFT JOIN personas_mesa pe ON pm.persona_id=pe.id
                         WHERE pm.mesa_id=? AND pm.anulado=0
                         ORDER BY pm.ronda, pm.id""", (mesa_id,))
            if not hist.empty:
                hist.columns = ["Ronda","Hora","Para","Producto","Cant.","Precio","Subtotal","id"]
                st.dataframe(hist.drop(columns=["id"]), use_container_width=True, hide_index=True)

                if st.session_state.rol == "admin":
                    ianu = st.number_input("Anular pedido ID (ver columna id)", min_value=1, step=1, key=f"anu_{mesa_id}")
                    if st.button("🚫 Anular ítem", key=f"btn_anu_{mesa_id}"):
                        row_anu = qry("SELECT producto_id,cantidad FROM pedidos_mesa WHERE id=? AND mesa_id=?",
                                      (ianu, mesa_id), one=True)
                        if row_anu:
                            exe("UPDATE pedidos_mesa SET anulado=1 WHERE id=?", (ianu,))
                            exe("UPDATE productos SET stock=stock+? WHERE id=?", (row_anu[1], row_anu[0]))
                            st.success("Ítem anulado y stock repuesto.")
                            st.rerun()

    # ── TAB 2: PERSONAS ──────────────────────────────────────────────────────
    with tab_personas:
        st.markdown("**Personas en esta mesa**")
        st.caption("Agregar personas permite asignar pedidos individuales y dividir la cuenta.")

        if personas:
            for pid_p, pnom in personas:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f'<span class="persona-chip">👤 {pnom}</span>', unsafe_allow_html=True)
                if c2.button("Quitar", key=f"qp_{pid_p}"):
                    exe("UPDATE personas_mesa SET activo=0 WHERE id=?", (pid_p,))
                    st.rerun()
        else:
            st.info("No hay personas registradas. Los pedidos van a la mesa completa.")

        st.markdown("---")
        with st.form(f"add_persona_{mesa_id}"):
            nom_p = st.text_input("Nombre de la persona")
            if st.form_submit_button("➕ Agregar persona"):
                if nom_p.strip():
                    exe("INSERT INTO personas_mesa(mesa_id,nombre) VALUES(?,?)", (mesa_id, nom_p.strip()))
                    st.success(f"'{nom_p}' agregado/a.")
                    st.rerun()

        # Resumen de consumo por persona
        if personas:
            st.markdown("---")
            st.markdown("**Consumo por persona (hasta ahora):**")
            _tabla_cuenta_personas(mesa_id, personas, solo_resumen=True)

    # ── TAB 3: CUENTA Y COBRO ────────────────────────────────────────────────
    with tab_cuenta:
        st.markdown("### 🧾 Cuenta detallada")
        _mostrar_cuenta_completa(mesa_id, personas, mnombre, mestado)

# ─── LÓGICA DE CUENTA ────────────────────────────────────────────────────────
def _tabla_cuenta_personas(mesa_id, personas, solo_resumen=False):
    """Muestra desglose por persona. Compartidos se dividen a partes iguales."""
    n_personas = max(len(personas), 1)

    # Pedidos con persona asignada
    pers_df = df("""SELECT pe.nombre, SUM(pm.subtotal) as total,
                           COUNT(pm.id) as items
                    FROM pedidos_mesa pm
                    JOIN personas_mesa pe ON pm.persona_id=pe.id
                    WHERE pm.mesa_id=? AND pm.anulado=0
                    GROUP BY pe.nombre""", (mesa_id,))

    # Pedidos compartidos
    comp = qry("SELECT COALESCE(SUM(subtotal),0) FROM pedidos_mesa WHERE mesa_id=? AND persona_id IS NULL AND anulado=0",
               (mesa_id,), one=True)[0]
    cuota_compartida = comp / n_personas

    # Armar tabla resumen
    resumen = {}
    for _, pnom in personas:
        resumen[pnom] = {"propio": 0.0, "items_propios": 0}
    if not pers_df.empty:
        for _, row in pers_df.iterrows():
            if row["nombre"] in resumen:
                resumen[row["nombre"]]["propio"]       = row["total"]
                resumen[row["nombre"]]["items_propios"] = row["items"]

    rows_tabla = []
    for pnom, data in resumen.items():
        total_p = data["propio"] + cuota_compartida
        rows_tabla.append({
            "Persona":        pnom,
            "Pedidos propios": fmt(data["propio"]),
            "Cuota compartida": fmt(cuota_compartida),
            "TOTAL A PAGAR":  fmt(total_p),
        })

    if rows_tabla:
        st.dataframe(pd.DataFrame(rows_tabla), use_container_width=True, hide_index=True)
        if not solo_resumen:
            st.markdown(f"**Compartido total: {fmt(comp)}** ÷ {n_personas} personas = {fmt(cuota_compartida)} c/u")

def _mostrar_cuenta_completa(mesa_id, personas, mnombre, mestado):
    # Total general
    total_mesa = qry("SELECT COALESCE(SUM(subtotal),0) FROM pedidos_mesa WHERE mesa_id=? AND anulado=0",
                     (mesa_id,), one=True)[0]
    n_ped = qry("SELECT COUNT(*) FROM pedidos_mesa WHERE mesa_id=? AND anulado=0", (mesa_id,), one=True)[0]

    if total_mesa == 0:
        st.info("No hay pedidos registrados en esta mesa.")
        return

    c1, c2 = st.columns(2)
    with c1: st.markdown(kpi("Total mesa", fmt(total_mesa), f"{n_ped} ítems","green"), unsafe_allow_html=True)
    with c2: st.markdown(kpi("Personas", str(len(personas)), "en esta mesa","blue"), unsafe_allow_html=True)

    # Detalle por ronda
    with st.expander("📋 Ver detalle por ronda"):
        rondas = df("""SELECT pm.ronda, pm.nombre_producto,
                              COALESCE(pe.nombre,'Mesa (compartido)') as para,
                              pm.cantidad, pm.precio_unitario, pm.subtotal
                       FROM pedidos_mesa pm
                       LEFT JOIN personas_mesa pe ON pm.persona_id=pe.id
                       WHERE pm.mesa_id=? AND pm.anulado=0
                       ORDER BY pm.ronda, pm.id""", (mesa_id,))
        rondas.columns = ["Ronda","Producto","Para","Cant.","Precio","Subtotal"]
        st.dataframe(rondas, use_container_width=True, hide_index=True)

    # Desglose por persona
    if personas:
        st.markdown("---")
        st.markdown("#### 👥 Cuenta por persona")
        _tabla_cuenta_personas(mesa_id, personas, solo_resumen=False)

        # Detalle granular por persona
        with st.expander("🔍 Ver pedidos individuales por persona"):
            n_personas = max(len(personas), 1)
            comp_total = qry("SELECT COALESCE(SUM(subtotal),0) FROM pedidos_mesa WHERE mesa_id=? AND persona_id IS NULL AND anulado=0",
                             (mesa_id,), one=True)[0]
            cuota = comp_total / n_personas

            for pid_p, pnom in personas:
                propios = df("""SELECT nombre_producto, cantidad, precio_unitario, subtotal
                                FROM pedidos_mesa WHERE mesa_id=? AND persona_id=? AND anulado=0
                                ORDER BY id""", (mesa_id, pid_p))
                total_propio = float(propios["subtotal"].sum()) if not propios.empty else 0
                st.markdown(f"**👤 {pnom}** — Total: {fmt(total_propio + cuota)}")
                if not propios.empty:
                    propios.columns = ["Producto","Cant.","Precio","Subtotal"]
                    st.dataframe(propios, use_container_width=True, hide_index=True)
                st.markdown(f"<small>+ Cuota compartida: {fmt(cuota)}</small>", unsafe_allow_html=True)
                st.markdown("---")

    # Cobro
    st.markdown("---")
    st.markdown("#### 💳 Registrar pago y cerrar mesa")

    descuento = st.number_input("Descuento ($)", min_value=0.0, step=1000.0, key=f"desc_{mesa_id}")
    total_cobrar = total_mesa - descuento
    st.markdown(kpi("TOTAL A COBRAR", fmt(total_cobrar),"","green"), unsafe_allow_html=True)

    metodo = st.selectbox("Método de pago", ["Efectivo","Tarjeta débito","Tarjeta crédito","Transferencia","Nequi","Daviplata"], key=f"met_{mesa_id}")

    if metodo == "Efectivo":
        recibido = st.number_input("Efectivo recibido", min_value=0.0, step=1000.0, value=float(total_cobrar), key=f"rec_{mesa_id}")
        cambio = recibido - total_cobrar
        if cambio >= 0: st.success(f"Cambio: {fmt(cambio)}")
        else: st.error(f"Falta: {fmt(-cambio)}")

    nota_cierre = st.text_input("Nota de cierre", key=f"nota_c_{mesa_id}")

    c_cobrar, c_cuenta = st.columns(2)
    with c_cobrar:
        if st.button("✅ COBRAR Y CERRAR MESA", type="primary", use_container_width=True):
            if total_cobrar <= 0:
                st.error("El total debe ser mayor a cero.")
            else:
                hoy   = date.today().isoformat()
                ahora = datetime.now().strftime("%H:%M:%S")
                pedidos_items = qry("""SELECT producto_id, nombre_producto, SUM(cantidad), precio_unitario, SUM(subtotal)
                                       FROM pedidos_mesa WHERE mesa_id=? AND anulado=0
                                       GROUP BY producto_id, nombre_producto, precio_unitario""", (mesa_id,))
                with get_conn() as conn:
                    cur = conn.execute(
                        "INSERT INTO ventas(fecha,hora,total,descuento,metodo_pago,usuario,nota,origen) VALUES(?,?,?,?,?,?,?,?)",
                        (hoy, ahora, total_cobrar, descuento, metodo, st.session_state.user, f"{mnombre} | {nota_cierre}", "mesa"))
                    vid = cur.lastrowid
                    for pid_prod, pnom_prod, cant, precio_u, subt in pedidos_items:
                        conn.execute(
                            "INSERT INTO detalle_ventas(venta_id,producto_id,nombre_producto,cantidad,precio_unitario,subtotal) VALUES(?,?,?,?,?,?)",
                            (vid, pid_prod, pnom_prod, cant, precio_u, subt))
                    conn.execute("UPDATE mesas SET estado='libre',fecha_apertura=NULL,hora_apertura=NULL WHERE id=?", (mesa_id,))
                    conn.execute("UPDATE personas_mesa SET activo=0 WHERE mesa_id=?", (mesa_id,))
                    conn.commit()
                st.session_state[f"cart_mesa_{mesa_id}"] = []
                st.session_state.mesa_vista = None
                st.success(f"¡{mnombre} cobrada y cerrada! Venta #{vid} — {fmt(total_cobrar)}")
                st.rerun()

    with c_cuenta:
        if mestado != "cuenta":
            if st.button("🔔 Marcar 'Pidiendo cuenta'", use_container_width=True):
                exe("UPDATE mesas SET estado='cuenta' WHERE id=?", (mesa_id,))
                st.rerun()
        else:
            if st.button("↩ Volver a 'Ocupada'", use_container_width=True):
                exe("UPDATE mesas SET estado='ocupada' WHERE id=?", (mesa_id,))
                st.rerun()

# ─── INVENTARIO ──────────────────────────────────────────────────────────────
def page_inventario():
    st.markdown("## 📦 Inventario")
    tab1, tab2, tab3 = st.tabs(["📋 Productos", "➕ Nuevo producto", "📥 Entrada de stock"])

    with tab1:
        cats_list = ["Todas"] + [r[0] for r in qry("SELECT nombre FROM categorias ORDER BY nombre")]
        c1, c2 = st.columns(2)
        filtro_cat = c1.selectbox("Categoría", cats_list)
        solo_bajos = c2.checkbox("Solo stock bajo")

        sql = """SELECT p.codigo, p.nombre, c.nombre as cat, p.precio_venta,
                        p.precio_costo, p.stock, p.stock_minimo, p.unidad
                 FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id
                 WHERE p.activo=1"""
        par = []
        if filtro_cat != "Todas":
            sql += " AND c.nombre=?"; par.append(filtro_cat)
        if solo_bajos:
            sql += " AND p.stock<=p.stock_minimo"
        sql += " ORDER BY p.nombre"

        inv = df(sql, par)
        if not inv.empty:
            inv["Estado"] = inv.apply(lambda r: "🔴 Bajo" if r["stock"] <= r["stock_minimo"] else "🟢 OK", axis=1)
            inv.columns = ["Código","Nombre","Categoría","Precio Venta","Precio Costo","Stock","Stock Mín.","Unidad","Estado"]
            st.dataframe(inv, use_container_width=True, hide_index=True)
        else:
            st.info("No hay productos.")

    with tab2:
        cats   = {r[0]: r[1] for r in qry("SELECT nombre,id FROM categorias ORDER BY nombre")}
        provs  = {r[0]: r[1] for r in qry("SELECT nombre,id FROM proveedores WHERE activo=1 ORDER BY nombre")}
        provs["(Sin proveedor)"] = None

        with st.form("nuevo_prod"):
            c1, c2 = st.columns(2)
            cod  = c1.text_input("Código *")
            nom  = c2.text_input("Nombre *")
            cat  = c1.selectbox("Categoría", list(cats.keys()))
            prov = c2.selectbox("Proveedor", list(provs.keys()))
            pv   = c1.number_input("Precio venta", min_value=0.0, step=500.0)
            pc   = c2.number_input("Precio costo", min_value=0.0, step=500.0)
            si   = c1.number_input("Stock inicial", min_value=0.0, step=1.0)
            sm   = c2.number_input("Stock mínimo", min_value=0.0, value=5.0, step=1.0)
            uni  = c1.text_input("Unidad", "unidad")
            if st.form_submit_button("✅ Crear producto", type="primary"):
                if not cod or not nom:
                    st.error("Código y nombre son obligatorios.")
                elif qry("SELECT 1 FROM productos WHERE codigo=?", (cod,), one=True):
                    st.error("El código ya existe.")
                else:
                    exe("INSERT INTO productos(codigo,nombre,categoria_id,proveedor_id,precio_venta,precio_costo,stock,stock_minimo,unidad) VALUES(?,?,?,?,?,?,?,?,?)",
                        (cod, nom, cats[cat], provs[prov], pv, pc, si, sm, uni))
                    st.success(f"'{nom}' creado.")
                    st.rerun()

    with tab3:
        prods2 = df("SELECT id,nombre,stock FROM productos WHERE activo=1 ORDER BY nombre")
        provs2 = qry("SELECT id,nombre FROM proveedores WHERE activo=1 ORDER BY nombre")
        if prods2.empty:
            st.warning("Crea productos primero.")
        else:
            with st.form("entrada"):
                psel = st.selectbox("Proveedor", ["(Ninguno)"] + [r[1] for r in provs2])
                nota_e = st.text_input("Nota / # Factura")
                fecha_e = st.date_input("Fecha", date.today())
                items_e = []
                for i in range(8):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    op = c1.selectbox(f"Producto {i+1}", ["(ninguno)"] + prods2["nombre"].tolist(), key=f"ep{i}")
                    ca = c2.number_input("Cant.", min_value=0.0, step=1.0, key=f"ec{i}")
                    co = c3.number_input("Costo", min_value=0.0, step=100.0, key=f"eco{i}")
                    if op != "(ninguno)" and ca > 0:
                        pid_e = int(prods2[prods2["nombre"] == op]["id"].values[0])
                        items_e.append((pid_e, op, ca, co))
                if st.form_submit_button("📥 Registrar entrada", type="primary"):
                    if not items_e:
                        st.error("Agrega al menos un producto.")
                    else:
                        total_e = sum(i[2] * i[3] for i in items_e)
                        prov_id_e = None
                        if psel != "(Ninguno)":
                            r2 = qry("SELECT id FROM proveedores WHERE nombre=?", (psel,), one=True)
                            if r2: prov_id_e = r2[0]
                        with get_conn() as conn:
                            cur2 = conn.execute("INSERT INTO compras(fecha,proveedor_id,total,nota,usuario) VALUES(?,?,?,?,?)",
                                                (fecha_e.isoformat(), prov_id_e, total_e, nota_e, st.session_state.user))
                            cid = cur2.lastrowid
                            for pid_e, pn_e, ca_e, co_e in items_e:
                                conn.execute("INSERT INTO detalle_compras(compra_id,producto_id,nombre_producto,cantidad,precio_unitario,subtotal) VALUES(?,?,?,?,?,?)",
                                             (cid, pid_e, pn_e, ca_e, co_e, ca_e*co_e))
                                conn.execute("UPDATE productos SET stock=stock+? WHERE id=?", (ca_e, pid_e))
                            conn.commit()
                        st.success(f"Entrada registrada. Total: {fmt(total_e)}")
                        st.rerun()

# ─── CAJA (ventas directas) ───────────────────────────────────────────────────
def page_caja():
    st.markdown("## 🧾 Caja rápida")
    st.caption("Para pedidos directos sin mesa. Para ventas por mesa, usa el módulo **Mesas**.")
    tab1, tab2 = st.tabs(["💳 Nueva venta", "📜 Historial"])

    with tab1:
        if "carrito_caja" not in st.session_state:
            st.session_state.carrito_caja = []

        prods_c = df("""SELECT p.id,p.codigo,p.nombre,p.precio_venta,p.stock,c.nombre as cat
                        FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id
                        WHERE p.activo=1 AND p.stock>0 ORDER BY c.nombre,p.nombre""")

        col_l, col_r = st.columns([3, 2])
        with col_l:
            if prods_c.empty:
                st.warning("Sin productos disponibles.")
            else:
                cats_c = ["Todas"] + sorted(prods_c["cat"].dropna().unique().tolist())
                cat_fc = st.selectbox("Categoría", cats_c, key="caja_cat")
                pf = prods_c if cat_fc == "Todas" else prods_c[prods_c["cat"] == cat_fc]

                c1, c2, c3 = st.columns([3, 1.5, 1])
                ops = [f"[{r['codigo']}] {r['nombre']} — {fmt(r['precio_venta'])}" for _, r in pf.iterrows()]
                sp  = c1.selectbox("Producto", ops, key="caja_prod")
                ca  = c2.number_input("Cant.", min_value=0.1, value=1.0, step=1.0, key="caja_cant")
                if c3.button("➕", type="primary", key="caja_add"):
                    cod_s = sp.split("]")[0][1:]
                    row_p = pf[pf["codigo"] == cod_s].iloc[0]
                    if ca > row_p["stock"]:
                        st.error(f"Stock insuficiente. Hay {row_p['stock']}")
                    else:
                        ex = next((i for i,it in enumerate(st.session_state.carrito_caja) if it["id"]==int(row_p["id"])), None)
                        if ex is not None:
                            st.session_state.carrito_caja[ex]["cantidad"] += ca
                            st.session_state.carrito_caja[ex]["subtotal"]  = st.session_state.carrito_caja[ex]["cantidad"] * st.session_state.carrito_caja[ex]["precio"]
                        else:
                            st.session_state.carrito_caja.append({"id":int(row_p["id"]),"codigo":row_p["codigo"],"nombre":row_p["nombre"],"precio":float(row_p["precio_venta"]),"cantidad":ca,"subtotal":ca*float(row_p["precio_venta"])})

            if st.session_state.carrito_caja:
                st.markdown("---")
                st.markdown("**🛒 Carrito**")
                cart_df2 = pd.DataFrame([{"Producto":i["nombre"],"Cant.":i["cantidad"],"Precio":fmt(i["precio"]),"Subtotal":fmt(i["subtotal"])} for i in st.session_state.carrito_caja])
                st.dataframe(cart_df2, use_container_width=True, hide_index=True)
                idx_d = st.number_input("Eliminar ítem #", min_value=1, max_value=len(st.session_state.carrito_caja), step=1)
                c_del, c_vac2 = st.columns(2)
                if c_del.button("🗑 Eliminar"): st.session_state.carrito_caja.pop(idx_d-1); st.rerun()
                if c_vac2.button("🗑 Vaciar todo"): st.session_state.carrito_caja = []; st.rerun()

        with col_r:
            st.markdown("**Cobro**")
            if st.session_state.carrito_caja:
                sub_c = sum(i["subtotal"] for i in st.session_state.carrito_caja)
                desc_c = st.number_input("Descuento ($)", min_value=0.0, step=1000.0)
                total_c = sub_c - desc_c
                st.markdown(kpi("Total", fmt(total_c), f"Subtotal {fmt(sub_c)}","green"), unsafe_allow_html=True)
                met_c = st.selectbox("Método", ["Efectivo","Tarjeta débito","Tarjeta crédito","Transferencia","Nequi","Daviplata"])
                if met_c == "Efectivo":
                    rec_c = st.number_input("Recibido", min_value=0.0, value=float(total_c), step=1000.0)
                    cam_c = rec_c - total_c
                    if cam_c >= 0: st.success(f"Cambio: {fmt(cam_c)}")
                    else: st.error(f"Falta: {fmt(-cam_c)}")
                nota_c = st.text_input("Nota")
                if st.button("✅ COBRAR", type="primary", use_container_width=True):
                    if total_c > 0:
                        hoy_c = date.today().isoformat()
                        aho_c = datetime.now().strftime("%H:%M:%S")
                        with get_conn() as conn:
                            cur_c = conn.execute("INSERT INTO ventas(fecha,hora,total,descuento,metodo_pago,usuario,nota) VALUES(?,?,?,?,?,?,?)",
                                                 (hoy_c, aho_c, total_c, desc_c, met_c, st.session_state.user, nota_c))
                            vc = cur_c.lastrowid
                            for it in st.session_state.carrito_caja:
                                conn.execute("INSERT INTO detalle_ventas(venta_id,producto_id,nombre_producto,cantidad,precio_unitario,subtotal) VALUES(?,?,?,?,?,?)",
                                             (vc, it["id"], it["nombre"], it["cantidad"], it["precio"], it["subtotal"]))
                                conn.execute("UPDATE productos SET stock=stock-? WHERE id=?", (it["cantidad"], it["id"]))
                            conn.commit()
                        st.session_state.carrito_caja = []
                        st.success(f"Venta #{vc} registrada — {fmt(total_c)}")
                        st.rerun()
            else:
                st.info("Carrito vacío.")

    with tab2:
        c1, c2 = st.columns(2)
        fd_h = c1.date_input("Desde", date.today(), key="h_d")
        fh_h = c2.date_input("Hasta", date.today(), key="h_h")
        hist_v = df("SELECT id,fecha,hora,total,descuento,metodo_pago,origen,usuario,nota,anulada FROM ventas WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC,hora DESC",
                    (fd_h.isoformat(), fh_h.isoformat()))
        if not hist_v.empty:
            hist_v.columns = ["ID","Fecha","Hora","Total","Descuento","Método","Origen","Usuario","Nota","Anulada"]
            hist_v["Anulada"] = hist_v["Anulada"].map({0:"No",1:"Sí"})
            tp = hist_v[hist_v["Anulada"]=="No"]["Total"].sum()
            st.markdown(f"**Total período: {fmt(tp)}**")
            st.dataframe(hist_v, use_container_width=True, hide_index=True)
        else:
            st.info("Sin ventas.")

# ─── NÓMINA ──────────────────────────────────────────────────────────────────
RECARGO = {"Normal":1.0,"Nocturno":1.35,"Dominical/Festivo":1.75,"Extra diurno":1.25,"Extra nocturno":1.75}

def page_nomina():
    st.markdown("## 👥 Nómina por horas")
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Empleados","⏱ Horas","💰 Liquidar","📋 Historial"])

    with tab1:
        c_l, c_r = st.columns(2)
        with c_l:
            emps_df = df("SELECT id,nombre,cedula,cargo,telefono,tarifa_hora,fecha_ingreso FROM empleados WHERE activo=1 ORDER BY nombre")
            if not emps_df.empty:
                emps_df.columns = ["ID","Nombre","Cédula","Cargo","Teléfono","Tarifa/H","Ingreso"]
                st.dataframe(emps_df, use_container_width=True, hide_index=True)
            else: st.info("No hay empleados.")
        with c_r:
            with st.form("nuevo_emp"):
                nom_e = st.text_input("Nombre *")
                ced_e = st.text_input("Cédula *")
                car_e = st.selectbox("Cargo", ["Barman","Mesero/a","Cajero/a","Domiciliario","Vigilante","Administrador","Otro"])
                tel_e = st.text_input("Teléfono")
                tar_e = st.number_input("Tarifa/hora ($)", min_value=0.0, step=500.0)
                fi_e  = st.date_input("Ingreso", date.today())
                if st.form_submit_button("✅ Crear"):
                    if not nom_e or not ced_e or tar_e <= 0:
                        st.error("Nombre, cédula y tarifa requeridos.")
                    elif qry("SELECT 1 FROM empleados WHERE cedula=?", (ced_e,), one=True):
                        st.error("Cédula ya registrada.")
                    else:
                        exe("INSERT INTO empleados(nombre,cedula,cargo,telefono,tarifa_hora,fecha_ingreso) VALUES(?,?,?,?,?,?)",
                            (nom_e, ced_e, car_e, tel_e, tar_e, fi_e.isoformat()))
                        st.success("Empleado creado."); st.rerun()

    with tab2:
        emps2 = qry("SELECT id,nombre,tarifa_hora FROM empleados WHERE activo=1 ORDER BY nombre")
        if not emps2:
            st.warning("No hay empleados.")
        else:
            ed2 = {r[1]: r[0] for r in emps2}
            et2 = {r[1]: r[2] for r in emps2}
            with st.form("reg_horas"):
                emp_s = st.selectbox("Empleado", list(ed2.keys()))
                c1, c2, c3 = st.columns(3)
                feh = c1.date_input("Fecha", date.today())
                hen = c2.text_input("Entrada (HH:MM)", "08:00")
                hsa = c3.text_input("Salida (HH:MM)", "17:00")
                tip = st.selectbox("Tipo", list(RECARGO.keys()))
                not_h = st.text_input("Nota")
                hh = 0.0
                try:
                    d1 = datetime.strptime(hen, "%H:%M")
                    d2 = datetime.strptime(hsa, "%H:%M")
                    hh = round((d2 - d1).seconds / 3600, 2)
                except: pass
                tar_h = et2.get(emp_s, 0)
                pag_e = hh * tar_h * RECARGO.get(tip, 1.0)
                if hh > 0:
                    st.info(f"Horas: {hh:.2f} | Factor: {RECARGO[tip]}x | Pago estimado: {fmt(pag_e)}")
                if st.form_submit_button("⏱ Registrar"):
                    if hh <= 0: st.error("Verifica horas.")
                    else:
                        exe("INSERT INTO horas_trabajo(empleado_id,fecha,hora_entrada,hora_salida,horas_trabajadas,tipo,nota) VALUES(?,?,?,?,?,?,?)",
                            (ed2[emp_s], feh.isoformat(), hen, hsa, hh, tip, not_h))
                        st.success("Horas registradas."); st.rerun()

            pen = df("""SELECT h.id,e.nombre,h.fecha,h.hora_entrada,h.hora_salida,h.horas_trabajadas,h.tipo
                        FROM horas_trabajo h JOIN empleados e ON h.empleado_id=e.id
                        WHERE h.pagado=0 ORDER BY h.fecha DESC""")
            if not pen.empty:
                pen.columns = ["ID","Empleado","Fecha","Entrada","Salida","Horas","Tipo"]
                st.markdown("**Horas pendientes de pago:**")
                st.dataframe(pen, use_container_width=True, hide_index=True)

    with tab3:
        emps3 = qry("SELECT id,nombre,tarifa_hora FROM empleados WHERE activo=1 ORDER BY nombre")
        if not emps3:
            st.warning("No hay empleados.")
        else:
            ed3  = {r[1]: (r[0], r[2]) for r in emps3}
            el   = st.selectbox("Empleado", list(ed3.keys()), key="liq_emp")
            c1, c2 = st.columns(2)
            pi = c1.date_input("Período desde", date.today() - timedelta(days=7))
            pf_l = c2.date_input("Período hasta", date.today())
            eid_l, tar_l = ed3[el]
            hpend = df("SELECT id,fecha,horas_trabajadas,tipo FROM horas_trabajo WHERE empleado_id=? AND pagado=0 AND fecha BETWEEN ? AND ? ORDER BY fecha",
                       (eid_l, pi.isoformat(), pf_l.isoformat()))
            if not hpend.empty:
                hpend["monto"] = hpend.apply(lambda r: r["horas_trabajadas"] * tar_l * RECARGO.get(r["tipo"], 1.0), axis=1)
                th = hpend["horas_trabajadas"].sum()
                tm = hpend["monto"].sum()
                hpend.columns = ["ID","Fecha","Horas","Tipo","Monto"]
                st.dataframe(hpend, use_container_width=True, hide_index=True)
                c1, c2 = st.columns(2)
                c1.markdown(kpi("Total horas", f"{th:.2f} h","","blue"), unsafe_allow_html=True)
                c2.markdown(kpi("Total a pagar", fmt(tm), f"Tarifa base {fmt(tar_l)}/h","green"), unsafe_allow_html=True)
                met_n = st.selectbox("Método pago", ["Efectivo","Transferencia","Nequi","Daviplata"])
                if st.button("💰 Liquidar", type="primary"):
                    ids_l = hpend["ID"].tolist()
                    with get_conn() as conn:
                        conn.execute("INSERT INTO pagos_nomina(empleado_id,periodo_inicio,periodo_fin,horas_totales,monto_total,fecha_pago,metodo_pago,usuario) VALUES(?,?,?,?,?,?,?,?)",
                                     (eid_l, pi.isoformat(), pf_l.isoformat(), th, tm, date.today().isoformat(), met_n, st.session_state.user))
                        for hid in ids_l:
                            conn.execute("UPDATE horas_trabajo SET pagado=1 WHERE id=?", (hid,))
                        conn.commit()
                    st.success(f"Pago registrado: {fmt(tm)} a {el}"); st.rerun()
            else:
                st.info("Sin horas pendientes en ese período.")

    with tab4:
        c1, c2 = st.columns(2)
        fdn = c1.date_input("Desde", date.today() - timedelta(days=30), key="hn_d")
        fhn = c2.date_input("Hasta", date.today(), key="hn_h")
        hn  = df("SELECT pn.id,e.nombre,pn.periodo_inicio,pn.periodo_fin,pn.horas_totales,pn.monto_total,pn.fecha_pago,pn.metodo_pago FROM pagos_nomina pn JOIN empleados e ON pn.empleado_id=e.id WHERE pn.fecha_pago BETWEEN ? AND ? ORDER BY pn.fecha_pago DESC",
                 (fdn.isoformat(), fhn.isoformat()))
        if not hn.empty:
            hn.columns = ["ID","Empleado","Desde","Hasta","Horas","Total","Fecha pago","Método"]
            st.markdown(f"**Total nómina: {fmt(hn['Total'].sum())}**")
            st.dataframe(hn, use_container_width=True, hide_index=True)
        else: st.info("Sin pagos en el período.")

# ─── PROVEEDORES ─────────────────────────────────────────────────────────────
def page_proveedores():
    st.markdown("## 🏪 Proveedores")
    tab1, tab2 = st.tabs(["📋 Lista","➕ Nuevo"])

    with tab1:
        prov_df = df("SELECT id,nombre,contacto,telefono,email,nit FROM proveedores WHERE activo=1 ORDER BY nombre")
        if not prov_df.empty:
            prov_df.columns = ["ID","Nombre","Contacto","Teléfono","Email","NIT"]
            st.dataframe(prov_df, use_container_width=True, hide_index=True)
        else: st.info("Sin proveedores.")

    with tab2:
        with st.form("nprov"):
            c1, c2 = st.columns(2)
            np_ = c1.text_input("Nombre *"); nc_ = c2.text_input("Contacto")
            nt_ = c1.text_input("Teléfono"); ne_ = c2.text_input("Email")
            nn_ = st.text_input("NIT / Cédula")
            if st.form_submit_button("✅ Crear"):
                if not np_: st.error("Nombre requerido.")
                else:
                    exe("INSERT INTO proveedores(nombre,contacto,telefono,email,nit) VALUES(?,?,?,?,?)",
                        (np_, nc_, nt_, ne_, nn_))
                    st.success(f"'{np_}' creado."); st.rerun()

# ─── GASTOS ──────────────────────────────────────────────────────────────────
CATS_GASTO = ["Servicios públicos","Arriendo/Local","Publicidad","Aseo y limpieza",
              "Mantenimiento","Transporte","Impuestos y tasas","Música/Entretenimiento","Otros"]

def page_gastos():
    st.markdown("## 💸 Gastos operativos")
    tab1, tab2 = st.tabs(["➕ Registrar","📋 Historial"])

    with tab1:
        with st.form("ngasto"):
            c1, c2 = st.columns(2)
            fg  = c1.date_input("Fecha", date.today())
            cg  = c2.selectbox("Categoría", CATS_GASTO)
            dg  = c1.text_input("Descripción")
            mg  = c2.number_input("Monto ($) *", min_value=0.0, step=1000.0)
            mtg = st.selectbox("Método", ["Efectivo","Transferencia","Tarjeta"])
            if st.form_submit_button("💾 Registrar"):
                if mg <= 0: st.error("Monto > 0.")
                else:
                    exe("INSERT INTO gastos(fecha,categoria,descripcion,monto,metodo_pago,usuario) VALUES(?,?,?,?,?,?)",
                        (fg.isoformat(), cg, dg, mg, mtg, st.session_state.user))
                    st.success(f"Gasto {fmt(mg)} registrado."); st.rerun()

    with tab2:
        c1, c2 = st.columns(2)
        fdg = c1.date_input("Desde", date.today() - timedelta(days=30), key="gd")
        fhg = c2.date_input("Hasta", date.today(), key="gh")
        gdf = df("SELECT id,fecha,categoria,descripcion,monto,metodo_pago FROM gastos WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC",
                 (fdg.isoformat(), fhg.isoformat()))
        if not gdf.empty:
            gdf.columns = ["ID","Fecha","Categoría","Descripción","Monto","Método"]
            st.markdown(f"**Total: {fmt(gdf['Monto'].sum())}**")
            st.dataframe(gdf, use_container_width=True, hide_index=True)
            pc = gdf.groupby("Categoría")["Monto"].sum().reset_index()
            fig = px.pie(pc, names="Categoría", values="Monto", color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(paper_bgcolor="#1e293b", font_color="#cbd5e1")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin gastos.")

# ─── BALANCE ─────────────────────────────────────────────────────────────────
def page_balance():
    st.markdown("## 📊 Balance financiero")
    c1, c2 = st.columns(2)
    fdb = c1.date_input("Desde", date.today().replace(day=1))
    fhb = c2.date_input("Hasta", date.today())

    ing   = qry("SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha BETWEEN ? AND ? AND anulada=0", (fdb.isoformat(),fhb.isoformat()), one=True)[0]
    costo = qry("""SELECT COALESCE(SUM(dv.cantidad*p.precio_costo),0)
                   FROM detalle_ventas dv JOIN ventas v ON dv.venta_id=v.id
                   JOIN productos p ON dv.producto_id=p.id
                   WHERE v.fecha BETWEEN ? AND ? AND v.anulada=0""", (fdb.isoformat(),fhb.isoformat()), one=True)[0]
    gop  = qry("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE fecha BETWEEN ? AND ?", (fdb.isoformat(),fhb.isoformat()), one=True)[0]
    nom  = qry("SELECT COALESCE(SUM(monto_total),0) FROM pagos_nomina WHERE fecha_pago BETWEEN ? AND ?", (fdb.isoformat(),fhb.isoformat()), one=True)[0]
    comp = qry("SELECT COALESCE(SUM(total),0) FROM compras WHERE fecha BETWEEN ? AND ?", (fdb.isoformat(),fhb.isoformat()), one=True)[0]

    ub = ing - costo
    un = ub - gop - nom

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(kpi("Ingresos ventas", fmt(ing), "","green"), unsafe_allow_html=True)
        st.markdown(kpi("Costo de ventas", fmt(costo), "","red"), unsafe_allow_html=True)
        st.markdown(kpi("Utilidad bruta", fmt(ub), f"Margen {ub/ing*100:.1f}%" if ing>0 else "","green" if ub>=0 else "red"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi("Gastos operativos", fmt(gop), "","yellow"), unsafe_allow_html=True)
        st.markdown(kpi("Nómina pagada", fmt(nom), "","orange"), unsafe_allow_html=True)
        st.markdown(kpi("Compras inventario", fmt(comp), "","purple"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi("UTILIDAD NETA", fmt(un), f"Margen {un/ing*100:.1f}%" if ing>0 else "","green" if un>=0 else "red"), unsafe_allow_html=True)

    st.divider()
    vd = df("SELECT fecha, SUM(total) as ingresos FROM ventas WHERE fecha BETWEEN ? AND ? AND anulada=0 GROUP BY fecha", (fdb.isoformat(),fhb.isoformat()))
    gd = df("SELECT fecha, SUM(monto) as egresos FROM gastos WHERE fecha BETWEEN ? AND ? GROUP BY fecha", (fdb.isoformat(),fhb.isoformat()))
    if not vd.empty or not gd.empty:
        flujo = pd.merge(vd, gd, on="fecha", how="outer").fillna(0).sort_values("fecha")
        fig = go.Figure()
        fig.add_bar(x=flujo["fecha"], y=flujo.get("ingresos",0), name="Ingresos", marker_color="#22c55e")
        fig.add_bar(x=flujo["fecha"], y=flujo.get("egresos",0), name="Gastos", marker_color="#ef4444")
        fig.update_layout(barmode="group", paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font_color="#cbd5e1")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Estado de resultados")
    st.table(pd.DataFrame({
        "Concepto": ["(+) Ingresos","(-) Costo ventas","(=) Utilidad bruta","(-) Gastos op.","(-) Nómina","(=) UTILIDAD NETA"],
        "Monto":    [fmt(ing), fmt(-costo), fmt(ub), fmt(-gop), fmt(-nom), fmt(un)]
    }))

# ─── REPORTES ────────────────────────────────────────────────────────────────
def page_reportes():
    st.markdown("## 📈 Reportes")
    tipo = st.selectbox("Tipo", ["Ventas por período","Mesas por día","Productos más vendidos","Horas por empleado","Compras por proveedor"])
    c1, c2 = st.columns(2)
    fdr = c1.date_input("Desde", date.today() - timedelta(days=30))
    fhr = c2.date_input("Hasta", date.today())

    dff = None
    if tipo == "Ventas por período":
        dff = df("SELECT fecha, COUNT(*) as n, SUM(total) as total, metodo_pago FROM ventas WHERE fecha BETWEEN ? AND ? AND anulada=0 GROUP BY fecha,metodo_pago ORDER BY fecha", (fdr.isoformat(),fhr.isoformat()))
    elif tipo == "Mesas por día":
        dff = df("""SELECT DATE(v.fecha) as fecha, COUNT(v.id) as ventas, SUM(v.total) as total
                    FROM ventas v WHERE v.origen='mesa' AND v.fecha BETWEEN ? AND ? AND v.anulada=0
                    GROUP BY DATE(v.fecha) ORDER BY fecha""", (fdr.isoformat(),fhr.isoformat()))
    elif tipo == "Productos más vendidos":
        dff = df("""SELECT dv.nombre_producto, SUM(dv.cantidad) as u, SUM(dv.subtotal) as ing
                    FROM detalle_ventas dv JOIN ventas v ON dv.venta_id=v.id
                    WHERE v.fecha BETWEEN ? AND ? AND v.anulada=0
                    GROUP BY dv.nombre_producto ORDER BY ing DESC LIMIT 20""", (fdr.isoformat(),fhr.isoformat()))
    elif tipo == "Horas por empleado":
        dff = df("""SELECT e.nombre, h.tipo, COUNT(*) as turnos, SUM(h.horas_trabajadas) as horas
                    FROM horas_trabajo h JOIN empleados e ON h.empleado_id=e.id
                    WHERE h.fecha BETWEEN ? AND ? GROUP BY e.nombre,h.tipo ORDER BY e.nombre""", (fdr.isoformat(),fhr.isoformat()))
    elif tipo == "Compras por proveedor":
        dff = df("""SELECT pv.nombre, COUNT(c.id) as compras, SUM(c.total) as total
                    FROM compras c JOIN proveedores pv ON c.proveedor_id=pv.id
                    WHERE c.fecha BETWEEN ? AND ? GROUP BY pv.nombre ORDER BY total DESC""", (fdr.isoformat(),fhr.isoformat()))

    if dff is not None and not dff.empty:
        st.dataframe(dff, use_container_width=True, hide_index=True)
        csv_b = dff.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar CSV", csv_b, f"{tipo}.csv", "text/csv")
    else:
        st.info("Sin datos en el período.")

# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────
def page_config():
    st.markdown("## ⚙️ Configuración")
    if st.session_state.rol != "admin":
        st.warning("Solo administradores.")
        return

    tab1, tab2, tab3 = st.tabs(["👤 Usuarios","🏷️ Categorías","🪑 Mesas"])

    with tab1:
        udf = df("SELECT id,username,rol,activo FROM usuarios ORDER BY username")
        if not udf.empty:
            udf.columns = ["ID","Usuario","Rol","Activo"]
            udf["Activo"] = udf["Activo"].map({1:"✅",0:"❌"})
            st.dataframe(udf, use_container_width=True, hide_index=True)
        with st.form("nu"):
            c1, c2 = st.columns(2)
            un_ = c1.text_input("Usuario"); pw_ = c2.text_input("Contraseña", type="password")
            rol_ = st.selectbox("Rol", ["cajero","barman","admin"])
            if st.form_submit_button("Crear"):
                if not un_ or not pw_: st.error("Requeridos.")
                elif qry("SELECT 1 FROM usuarios WHERE username=?", (un_,), one=True): st.error("Ya existe.")
                else:
                    exe("INSERT INTO usuarios(username,password,rol) VALUES(?,?,?)", (un_, hsh(pw_), rol_))
                    st.success(f"'{un_}' creado."); st.rerun()
        with st.form("cpw"):
            us_ = st.selectbox("Usuario", [r[0] for r in qry("SELECT username FROM usuarios WHERE activo=1")])
            pw1_ = st.text_input("Nueva contraseña", type="password"); pw2_ = st.text_input("Confirmar", type="password")
            if st.form_submit_button("Cambiar"):
                if pw1_ != pw2_: st.error("No coinciden.")
                elif len(pw1_) < 6: st.error("Mínimo 6 caracteres.")
                else:
                    exe("UPDATE usuarios SET password=? WHERE username=?", (hsh(pw1_), us_))
                    st.success("Contraseña actualizada.")

    with tab2:
        cdf = df("SELECT id,nombre,color FROM categorias ORDER BY nombre")
        if not cdf.empty:
            cdf.columns = ["ID","Nombre","Color"]
            st.dataframe(cdf, use_container_width=True, hide_index=True)
        with st.form("ncat"):
            c1, c2 = st.columns(2)
            cn_ = c1.text_input("Categoría"); cc_ = c2.color_picker("Color","#3b82f6")
            if st.form_submit_button("Agregar"):
                if cn_:
                    exe("INSERT OR IGNORE INTO categorias(nombre,color) VALUES(?,?)", (cn_, cc_))
                    st.success(f"'{cn_}' agregada."); st.rerun()

    with tab3:
        st.markdown("**Gestión de mesas**")
        mesas_conf = df("SELECT id,numero,nombre,capacidad,estado FROM mesas ORDER BY numero")
        if not mesas_conf.empty:
            mesas_conf.columns = ["ID","#","Nombre","Capacidad","Estado"]
            st.dataframe(mesas_conf, use_container_width=True, hide_index=True)
        st.caption("Las mesas libres se pueden editar. Las ocupadas o con cuenta deben cerrarse primero.")
        with st.form("edit_mesa"):
            mesa_id_e = st.number_input("ID de mesa a editar", min_value=1, step=1)
            c1, c2 = st.columns(2)
            new_nom  = c1.text_input("Nuevo nombre")
            new_cap  = c2.number_input("Capacidad", min_value=1, value=4)
            if st.form_submit_button("Guardar"):
                exe("UPDATE mesas SET nombre=?,capacidad=? WHERE id=? AND estado='libre'",
                    (new_nom, new_cap, mesa_id_e))
                st.success("Mesa actualizada (solo si estaba libre)."); st.rerun()

# ─── SIDEBAR & ROUTING ───────────────────────────────────────────────────────
def main():
    if "user" not in st.session_state:
        login(); return

    with st.sidebar:
        logo_b64 = get_logo_b64()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="tribu-logo-sidebar">' if logo_b64 else '<div style="text-align:center;font-size:36px">🪶</div>'
        st.markdown(f"""
        <div class="tribu-brand">
            {logo_html}
            <span class="brand-name">LA TRIBU</span>
            <span class="brand-sub">Cafe · Bar</span>
        </div>
        """, unsafe_allow_html=True)

        rol = st.session_state.rol
        if rol == "admin":
            badge = '<span class="badge-admin">⚡ ADMIN</span>'
        elif rol == "barman":
            badge = '<span class="badge-barman">🍹 BARMAN</span>'
        else:
            badge = '<span class="badge-cajero">💼 CAJERO</span>'
        st.markdown(f"<div style='text-align:center;margin:8px 0'>{badge}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;color:#5a5033;font-size:12px;margin-bottom:8px'>👤 {st.session_state.user}</div>", unsafe_allow_html=True)
        st.divider()
        pagina = st.radio("Ir a", [
            "🏠 Dashboard",
            "🪑 Mesas",
            "🧾 Caja rápida",
            "📦 Inventario",
            "👥 Nómina",
            "🏪 Proveedores",
            "💸 Gastos",
            "📊 Balance",
            "📈 Reportes",
            "⚙️ Configuración",
        ], label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Salir", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    {
        "🏠 Dashboard":      page_dashboard,
        "🪑 Mesas":          page_mesas,
        "🧾 Caja rápida":    page_caja,
        "📦 Inventario":     page_inventario,
        "👥 Nómina":         page_nomina,
        "🏪 Proveedores":    page_proveedores,
        "💸 Gastos":         page_gastos,
        "📊 Balance":        page_balance,
        "📈 Reportes":       page_reportes,
        "⚙️ Configuración":  page_config,
    }[pagina]()

if __name__ == "__main__":
    main()
