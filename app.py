# -*- coding: utf-8 -*-
"""
La Tribu Cafe Bar — Sistema de gestión integral
Base de datos: Supabase (PostgreSQL) en producción / SQLite en local
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from contextlib import contextmanager
import os, hashlib, base64

# ─── CONFIGURACIÓN DE BASE DE DATOS ──────────────────────────────────────────
# Soporta variables individuales PG_* O un DATABASE_URL completo
_PG_HOST = _PG_USER = _PG_PASSWORD = _PG_DBNAME = _PG_PORT = ""
DATABASE_URL = ""
try:
    _PG_HOST     = st.secrets.get("PG_HOST", "")
    _PG_USER     = st.secrets.get("PG_USER", "")
    _PG_PASSWORD = st.secrets.get("PG_PASSWORD", "")
    _PG_DBNAME   = st.secrets.get("PG_DBNAME", "postgres")
    _PG_PORT     = st.secrets.get("PG_PORT", "5432")
    DATABASE_URL = st.secrets.get("DATABASE_URL", "")
except Exception:
    pass
DATABASE_URL = DATABASE_URL or os.environ.get("DATABASE_URL", "")
_PG_HOST     = _PG_HOST or os.environ.get("PG_HOST", "")

USE_PG   = bool(_PG_HOST) or DATABASE_URL.startswith(("postgres://", "postgresql://"))
DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(DATA_DIR, "bar.db")

# Tipo de ID según motor
ID_COL = "BIGSERIAL" if USE_PG else "INTEGER"

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

.stApp { background: #12141f; }
.main .block-container { padding-top: 1.5rem; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0d0f1a 0%,#12141f 60%,#0d0f1a 100%) !important;
    border-right: 1px solid #c8941a33;
}
[data-testid="stSidebar"] * { color:#e2c97e !important; }
[data-testid="stSidebar"] hr { border-color:#c8941a44 !important; }

.tribu-brand { text-align:center; padding:12px 0 8px 0; border-bottom:1px solid #c8941a44; margin-bottom:12px; }
.tribu-brand .brand-name {
    font-family:'Cinzel',serif; font-size:22px; font-weight:900;
    background:linear-gradient(135deg,#c8941a,#f5d07a,#c8941a);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    letter-spacing:3px; margin:6px 0 2px 0; display:block;
}
.tribu-brand .brand-sub { font-size:10px; color:#8a7450 !important; letter-spacing:4px; text-transform:uppercase; }
.tribu-logo-sidebar { width:80px; height:80px; border-radius:50%; border:2px solid #c8941a66;
    object-fit:cover; display:block; margin:0 auto; }

.kpi { background:linear-gradient(135deg,#1a1d2e 0%,#1e2135 100%); border-left:4px solid #c8941a;
    padding:14px 18px; border-radius:12px; margin-bottom:10px; box-shadow:0 4px 20px rgba(0,0,0,.4); }
.kpi.green  { border-left-color:#22c55e; }
.kpi.red    { border-left-color:#ef4444; }
.kpi.yellow { border-left-color:#f59e0b; }
.kpi.purple { border-left-color:#a855f7; }
.kpi.orange { border-left-color:#f97316; }
.kpi.blue   { border-left-color:#3b82f6; }
.kpi h4 { margin:0; font-size:10px; color:#8a7450; text-transform:uppercase; letter-spacing:.08em; }
.kpi p  { margin:4px 0 0; font-size:26px; font-weight:800; color:#f5d07a; }
.kpi small { color:#5a5033; font-size:11px; }

.mesa-card { background:linear-gradient(135deg,#1a1d2e,#1e2135); border-radius:14px;
    padding:20px 14px; margin:6px 0; border:2px solid #2a2d40; text-align:center;
    box-shadow:0 4px 16px rgba(0,0,0,.5); }
.mesa-titulo { font-size:19px; font-weight:800; color:#f5d07a; margin:0; }
.mesa-estado { font-size:12px; margin:4px 0; font-weight:600; }
.mesa-info   { font-size:12px; color:#8a7450; margin:2px 0; }

.persona-chip { display:inline-block; background:#2a1e0a; border:1px solid #c8941a66;
    color:#f5d07a !important; padding:3px 12px; border-radius:20px; font-size:12px;
    font-weight:700; margin:3px; }

.badge-admin  { background:#2a1e0a; color:#f5d07a; border:1px solid #c8941a; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-cajero { background:#0a2a15; color:#86efac; border:1px solid #22c55e66; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-barman { background:#2a0a0a; color:#fca5a5; border:1px solid #ef444466; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }

.stTabs [data-baseweb="tab"] { color:#8a7450; font-weight:600; }
.stTabs [aria-selected="true"] { color:#f5d07a !important; border-bottom:2px solid #c8941a !important; }

.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#c8941a,#a87515) !important;
    border:none !important; color:#12141f !important; font-weight:700 !important;
    border-radius:8px !important;
}
.stButton > button[kind="primary"]:hover {
    background:linear-gradient(135deg,#f5d07a,#c8941a) !important;
    box-shadow:0 4px 15px rgba(200,148,26,.4) !important;
}

.login-box { background:linear-gradient(145deg,#1a1d2e,#0d0f1a); border:1px solid #c8941a33;
    border-radius:20px; padding:40px 36px; box-shadow:0 20px 60px rgba(0,0,0,.7),0 0 40px rgba(200,148,26,.08);
    margin-top:40px; }
.login-titulo { font-family:'Cinzel',serif; font-size:34px; font-weight:900;
    background:linear-gradient(135deg,#c8941a 0%,#f5d07a 50%,#c8941a 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    text-align:center; letter-spacing:5px; margin:10px 0 4px 0; }
.login-sub  { text-align:center; color:#5a5033; font-size:11px; letter-spacing:4px; text-transform:uppercase; margin-bottom:24px; }
.login-logo { display:block; margin:0 auto 16px auto; width:110px; border-radius:50%;
    border:3px solid #c8941a66; box-shadow:0 0 30px rgba(200,148,26,.3); }
.ornament   { text-align:center; color:#c8941a44; font-size:14px; letter-spacing:8px; margin:8px 0; }
hr { border-color:#2a2d4066 !important; }
</style>
""", unsafe_allow_html=True)

# ─── CAPA DE BASE DE DATOS ────────────────────────────────────────────────────
@contextmanager
def db_conn():
    """Context manager: abre conexión (PG o SQLite), commit en éxito, rollback en error."""
    if USE_PG:
        import psycopg
        if _PG_HOST:
            # Variables individuales — la contraseña puede tener caracteres especiales
            conn = psycopg.connect(
                host=_PG_HOST, port=int(_PG_PORT or 5432),
                user=_PG_USER, password=_PG_PASSWORD,
                dbname=_PG_DBNAME, sslmode="require"
            )
        else:
            url = DATABASE_URL
            if "sslmode" not in url:
                url += ("&" if "?" in url else "?") + "sslmode=require"
            conn = psycopg.connect(url)
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _p(sql: str) -> str:
    """Convierte %s → ? para SQLite."""
    return sql if USE_PG else sql.replace("%s", "?")

def qry(sql, p=(), one=False):
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(_p(sql), p)
        return cur.fetchone() if one else cur.fetchall()

def exe(sql, p=()):
    with db_conn() as conn:
        conn.cursor().execute(_p(sql), p)

def exe_id(sql, p=()):
    """INSERT y retorna el id generado."""
    with db_conn() as conn:
        cur = conn.cursor()
        if USE_PG:
            cur.execute(_p(sql) + " RETURNING id", p)
            return cur.fetchone()[0]
        else:
            cur.execute(_p(sql), p)
            return cur.lastrowid

def df(sql, p=()):
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(_p(sql), list(p) if p else [])
        if cur.description:
            cols = [desc[0] for desc in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)
        return pd.DataFrame()

def insert_cur(cur, sql, p=()):
    """INSERT dentro de una transacción ya abierta; retorna el id."""
    if USE_PG:
        cur.execute(_p(sql) + " RETURNING id", p)
        return cur.fetchone()[0]
    else:
        cur.execute(_p(sql), p)
        return cur.lastrowid

# ─── INIT DB ─────────────────────────────────────────────────────────────────
def init_db():
    SER = "BIGSERIAL" if USE_PG else "INTEGER"
    IGN = "ON CONFLICT DO NOTHING" if USE_PG else "OR IGNORE"

    stmts = [
        f"""CREATE TABLE IF NOT EXISTS usuarios(
            id {SER} PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'cajero',
            activo INTEGER DEFAULT 1)""",
        f"""CREATE TABLE IF NOT EXISTS categorias(
            id {SER} PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#3b82f6')""",
        f"""CREATE TABLE IF NOT EXISTS proveedores(
            id {SER} PRIMARY KEY,
            nombre TEXT NOT NULL, contacto TEXT, telefono TEXT,
            email TEXT, nit TEXT, activo INTEGER DEFAULT 1)""",
        f"""CREATE TABLE IF NOT EXISTS productos(
            id {SER} PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL,
            categoria_id INTEGER, proveedor_id INTEGER,
            precio_venta REAL DEFAULT 0, precio_costo REAL DEFAULT 0,
            stock REAL DEFAULT 0, stock_minimo REAL DEFAULT 5,
            unidad TEXT DEFAULT 'unidad', activo INTEGER DEFAULT 1)""",
        f"""CREATE TABLE IF NOT EXISTS empleados(
            id {SER} PRIMARY KEY,
            nombre TEXT NOT NULL, cedula TEXT UNIQUE NOT NULL,
            cargo TEXT DEFAULT 'mesero', telefono TEXT,
            tarifa_hora REAL DEFAULT 0, activo INTEGER DEFAULT 1,
            fecha_ingreso TEXT)""",
        f"""CREATE TABLE IF NOT EXISTS horas_trabajo(
            id {SER} PRIMARY KEY,
            empleado_id INTEGER, fecha TEXT NOT NULL,
            hora_entrada TEXT, hora_salida TEXT,
            horas_trabajadas REAL DEFAULT 0, tipo TEXT DEFAULT 'normal',
            nota TEXT, pagado INTEGER DEFAULT 0)""",
        f"""CREATE TABLE IF NOT EXISTS pagos_nomina(
            id {SER} PRIMARY KEY,
            empleado_id INTEGER, periodo_inicio TEXT NOT NULL,
            periodo_fin TEXT NOT NULL, horas_totales REAL NOT NULL,
            monto_total REAL NOT NULL, fecha_pago TEXT NOT NULL,
            metodo_pago TEXT DEFAULT 'efectivo', usuario TEXT)""",
        f"""CREATE TABLE IF NOT EXISTS gastos(
            id {SER} PRIMARY KEY,
            fecha TEXT NOT NULL, categoria TEXT NOT NULL,
            descripcion TEXT, monto REAL NOT NULL,
            metodo_pago TEXT DEFAULT 'efectivo', usuario TEXT)""",
        f"""CREATE TABLE IF NOT EXISTS ventas(
            id {SER} PRIMARY KEY,
            fecha TEXT NOT NULL, hora TEXT NOT NULL,
            total REAL NOT NULL, descuento REAL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'efectivo',
            usuario TEXT, nota TEXT, anulada INTEGER DEFAULT 0,
            origen TEXT DEFAULT 'caja')""",
        f"""CREATE TABLE IF NOT EXISTS detalle_ventas(
            id {SER} PRIMARY KEY,
            venta_id INTEGER, producto_id INTEGER,
            nombre_producto TEXT, cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL, subtotal REAL NOT NULL)""",
        f"""CREATE TABLE IF NOT EXISTS compras(
            id {SER} PRIMARY KEY,
            fecha TEXT NOT NULL, proveedor_id INTEGER,
            total REAL NOT NULL, nota TEXT, usuario TEXT)""",
        f"""CREATE TABLE IF NOT EXISTS detalle_compras(
            id {SER} PRIMARY KEY,
            compra_id INTEGER, producto_id INTEGER,
            nombre_producto TEXT, cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL, subtotal REAL NOT NULL)""",
        f"""CREATE TABLE IF NOT EXISTS mesas(
            id {SER} PRIMARY KEY,
            numero INTEGER NOT NULL, nombre TEXT, capacidad INTEGER DEFAULT 4,
            estado TEXT DEFAULT 'libre',
            fecha_apertura TEXT, hora_apertura TEXT, usuario_apertura TEXT)""",
        f"""CREATE TABLE IF NOT EXISTS personas_mesa(
            id {SER} PRIMARY KEY,
            mesa_id INTEGER, nombre TEXT NOT NULL, activo INTEGER DEFAULT 1)""",
        f"""CREATE TABLE IF NOT EXISTS pedidos_mesa(
            id {SER} PRIMARY KEY,
            mesa_id INTEGER, persona_id INTEGER, producto_id INTEGER,
            nombre_producto TEXT NOT NULL, cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL, subtotal REAL NOT NULL,
            fecha TEXT NOT NULL, hora TEXT NOT NULL,
            usuario TEXT, anulado INTEGER DEFAULT 0, ronda INTEGER DEFAULT 1)""",
    ]

    with db_conn() as conn:
        cur = conn.cursor()
        for s in stmts:
            cur.execute(s)

        # Usuario admin inicial
        cur.execute("SELECT COUNT(*) FROM usuarios")
        if cur.fetchone()[0] == 0:
            cur.execute(
                _p("INSERT INTO usuarios(username,password,rol) VALUES(%s,%s,%s)"),
                ("admin", hsh("admin123"), "admin"))

        # Categorías
        cur.execute("SELECT COUNT(*) FROM categorias")
        if cur.fetchone()[0] == 0:
            cats = [("Licores","#8b5cf6"),("Cervezas","#f59e0b"),("Vinos","#ef4444"),
                    ("Cócteles","#ec4899"),("Gaseosas y Jugos","#22c55e"),
                    ("Agua y Energizantes","#06b6d4"),("Snacks y Comida","#f97316"),("Otros","#64748b")]
            for cat, color in cats:
                cur.execute(_p("INSERT INTO categorias(nombre,color) VALUES(%s,%s)"), (cat, color))

        # 12 mesas por defecto
        cur.execute("SELECT COUNT(*) FROM mesas")
        if cur.fetchone()[0] == 0:
            for i in range(1, 13):
                cur.execute(_p("INSERT INTO mesas(numero,nombre,capacidad,estado) VALUES(%s,%s,%s,%s)"),
                            (i, f"Mesa {i}", 4, "libre"))

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def hsh(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

init_db()

def kpi(titulo, valor, sub="", color=""):
    cls = f"kpi {color}" if color else "kpi"
    return f'<div class="{cls}"><h4>{titulo}</h4><p>{valor}</p><small>{sub}</small></div>'

def fmt(v):
    try:    return f"$ {float(v):,.0f}"
    except: return "$ 0"

def dago(n):
    """Fecha de hace N días como string ISO."""
    return (date.today() - timedelta(days=n)).isoformat()

# ─── LOGIN ───────────────────────────────────────────────────────────────────
def login():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        logo_b64 = get_logo_b64()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="login-logo">' \
                    if logo_b64 else '<div style="text-align:center;font-size:48px;margin-bottom:8px;">🪶</div>'
        st.markdown(f"""
        <div class="login-box">
            {logo_html}
            <div class="login-titulo">LA TRIBU</div>
            <div class="login-sub">Cafe · Bar · Sistema de gestión</div>
            <div class="ornament">◆ · · · ◆ · · · ◆</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        u = st.text_input("👤  Usuario")
        p = st.text_input("🔒  Contraseña", type="password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INGRESAR", use_container_width=True, type="primary"):
            row = qry("SELECT username,rol FROM usuarios WHERE username=%s AND password=%s AND activo=1",
                      (u, hsh(p)), one=True)
            if row:
                st.session_state.user = row[0]
                st.session_state.rol  = row[1]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        st.caption("🔑 Acceso inicial: admin · admin123")

# ─── DASHBOARD ───────────────────────────────────────────────────────────────
def page_dashboard():
    hoy = date.today().isoformat()
    st.markdown("## 🏠 Dashboard")
    st.caption(f"Hoy: {date.today().strftime('%A %d de %B de %Y')}")

    v_hoy = qry("SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha=%s AND anulada=0",(hoy,),one=True)[0]
    n_v   = qry("SELECT COUNT(*) FROM ventas WHERE fecha=%s AND anulada=0",(hoy,),one=True)[0]
    g_hoy = qry("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE fecha=%s",(hoy,),one=True)[0]
    costo = qry("""SELECT COALESCE(SUM(dv.cantidad*p.precio_costo),0)
                   FROM detalle_ventas dv JOIN ventas v ON dv.venta_id=v.id
                   JOIN productos p ON dv.producto_id=p.id
                   WHERE v.fecha=%s AND v.anulada=0""",(hoy,),one=True)[0]
    util      = v_hoy - costo - g_hoy
    bajos     = qry("SELECT COUNT(*) FROM productos WHERE stock<=stock_minimo AND activo=1",one=True)[0]
    mesas_ocu = qry("SELECT COUNT(*) FROM mesas WHERE estado IN ('ocupada','cuenta')",one=True)[0]

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(kpi("Ventas hoy",fmt(v_hoy),f"{n_v} transacciones","green"),unsafe_allow_html=True)
    with c2: st.markdown(kpi("Gastos hoy",fmt(g_hoy),"operativos","red"),unsafe_allow_html=True)
    with c3: st.markdown(kpi("Utilidad estimada",fmt(util),"ventas-costo-gastos","green" if util>=0 else "red"),unsafe_allow_html=True)
    with c4: st.markdown(kpi("Mesas ocupadas",str(mesas_ocu),"en este momento","orange"),unsafe_allow_html=True)
    with c5: st.markdown(kpi("Alertas stock",str(bajos),"bajo mínimo","red" if bajos>0 else "green"),unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    c_izq, c_der = st.columns(2)
    with c_izq:
        st.markdown("#### 📈 Ventas últimos 7 días")
        d7 = df("SELECT fecha, SUM(total) as total FROM ventas WHERE anulada=0 AND fecha>=%s GROUP BY fecha ORDER BY fecha",
                (dago(6),))
        if not d7.empty:
            fig = px.bar(d7, x="fecha", y="total", color_discrete_sequence=["#c8941a"],
                         labels={"fecha":"Fecha","total":"Total ($)"})
            fig.update_layout(paper_bgcolor="#1a1d2e",plot_bgcolor="#1a1d2e",
                              font_color="#e2c97e",showlegend=False,margin=dict(t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin ventas registradas aún.")

    with c_der:
        st.markdown("#### 🏆 Más vendidos hoy")
        top = df("""SELECT dv.nombre_producto, SUM(dv.cantidad) as u, SUM(dv.subtotal) as t
                    FROM detalle_ventas dv JOIN ventas v ON dv.venta_id=v.id
                    WHERE v.fecha=%s AND v.anulada=0
                    GROUP BY dv.nombre_producto ORDER BY u DESC LIMIT 8""", (hoy,))
        if not top.empty:
            fig2 = px.bar(top, x="u", y="nombre_producto", orientation="h",
                          color_discrete_sequence=["#f5d07a"],
                          labels={"nombre_producto":"","u":"Unidades"})
            fig2.update_layout(paper_bgcolor="#1a1d2e",plot_bgcolor="#1a1d2e",
                               font_color="#e2c97e",showlegend=False,margin=dict(t=10,b=10))
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
def _estado_badge(e):
    return {"libre":"🟢 Libre","ocupada":"🟡 Ocupada","cuenta":"🔴 Pidiendo cuenta"}.get(e, e)

def _ronda_actual(mid):
    r = qry("SELECT MAX(ronda) FROM pedidos_mesa WHERE mesa_id=%s AND anulado=0",(mid,),one=True)
    return r[0] or 0

def page_mesas():
    if "mesa_vista" not in st.session_state:
        st.session_state.mesa_vista = None
    if st.session_state.mesa_vista:
        _detalle_mesa(st.session_state.mesa_vista)
    else:
        _grid_mesas()

def _grid_mesas():
    st.markdown("## 🪑 Mesas")
    mesas_db = qry("""
        SELECT m.id, m.numero, m.nombre, m.estado, m.hora_apertura,
               (SELECT COUNT(*) FROM pedidos_mesa pm WHERE pm.mesa_id=m.id AND pm.anulado=0) as pedidos,
               (SELECT COALESCE(SUM(pm.subtotal),0) FROM pedidos_mesa pm WHERE pm.mesa_id=m.id AND pm.anulado=0) as total
        FROM mesas m ORDER BY m.numero""")

    with st.popover("➕ Nueva mesa"):
        with st.form("add_mesa"):
            num_m = st.number_input("Número",min_value=1,step=1)
            nom_m = st.text_input("Nombre")
            cap_m = st.number_input("Capacidad",min_value=1,value=4)
            if st.form_submit_button("Crear"):
                exe("INSERT INTO mesas(numero,nombre,capacidad,estado) VALUES(%s,%s,%s,'libre')",
                    (num_m, nom_m or f"Mesa {num_m}", cap_m))
                st.rerun()

    st.markdown("<br>",unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, m in enumerate(mesas_db):
        mid,mnum,mnombre,mestado,mahora,mpedidos,mtotal = m
        col = cols[idx % 4]
        with col:
            color = {"libre":"#22c55e","ocupada":"#f5d07a","cuenta":"#ef4444"}.get(mestado,"#64748b")
            info  = f"{mpedidos} ítems · {fmt(mtotal)}" if mestado != "libre" else "Sin pedidos"
            hora  = f"Desde {str(mahora)[:5]}" if mahora else ""
            st.markdown(f"""
            <div class="mesa-card" style="border-color:{color}">
              <p class="mesa-titulo" style="color:{color}">{mnombre}</p>
              <p class="mesa-estado" style="color:{color}">{_estado_badge(mestado)}</p>
              <p class="mesa-info">{info}</p>
              <p class="mesa-info">{hora}</p>
            </div>""", unsafe_allow_html=True)

            if mestado == "libre":
                if st.button("🔓 Abrir",key=f"abr_{mid}",use_container_width=True):
                    hoy=date.today().isoformat(); ahora=datetime.now().strftime("%H:%M:%S")
                    exe("UPDATE mesas SET estado='ocupada',fecha_apertura=%s,hora_apertura=%s,usuario_apertura=%s WHERE id=%s",
                        (hoy,ahora,st.session_state.user,mid))
                    st.session_state.mesa_vista = mid; st.rerun()
            else:
                if st.button("🔍 Gestionar",key=f"ver_{mid}",use_container_width=True):
                    st.session_state.mesa_vista = mid; st.rerun()

def _detalle_mesa(mesa_id):
    mesa = qry("SELECT id,numero,nombre,estado,fecha_apertura,hora_apertura FROM mesas WHERE id=%s",(mesa_id,),one=True)
    if not mesa:
        st.session_state.mesa_vista = None; st.rerun(); return
    mid,mnum,mnombre,mestado,mfecha,mahora = mesa

    col_b,col_t,col_e = st.columns([1,4,2])
    with col_b:
        if st.button("← Volver"):
            st.session_state.mesa_vista = None; st.rerun()
    with col_t:
        st.markdown(f"## 🪑 {mnombre}")
        st.caption(f"Abierta: {mfecha or ''} {str(mahora)[:5] if mahora else ''}")
    with col_e:
        color_e={"ocupada":"orange","cuenta":"red","libre":"green"}.get(mestado,"blue")
        st.markdown(kpi("Estado",_estado_badge(mestado),"",color_e),unsafe_allow_html=True)

    st.divider()
    personas = qry("SELECT id,nombre FROM personas_mesa WHERE mesa_id=%s AND activo=1 ORDER BY id",(mesa_id,))
    personas_dict = {p[1]:p[0] for p in personas}
    total_actual  = qry("SELECT COALESCE(SUM(subtotal),0) FROM pedidos_mesa WHERE mesa_id=%s AND anulado=0",(mesa_id,),one=True)[0]

    tab_ped,tab_per,tab_cta = st.tabs(["🍺 Agregar pedido","👤 Personas","🧾 Cuenta y cobro"])

    # ── TAB PEDIDO ──────────────────────────────────────────────────────────
    with tab_ped:
        c1,c2 = st.columns(2)
        c1.markdown(kpi("Total acumulado",fmt(total_actual),"todos los pedidos","green"),unsafe_allow_html=True)
        c2.markdown(kpi("Ronda actual",f"#{_ronda_actual(mesa_id)+1}",f"{len(personas)} personas","blue"),unsafe_allow_html=True)

        st.markdown("---")
        prods_d = df("""SELECT p.id,p.nombre,p.precio_venta,c.nombre as cat
                        FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id
                        WHERE p.activo=1 AND p.stock>0 ORDER BY c.nombre,p.nombre""")
        if prods_d.empty:
            st.warning("Sin productos disponibles en inventario.")
        else:
            key_cart = f"cart_m_{mesa_id}"
            if key_cart not in st.session_state:
                st.session_state[key_cart] = []

            cats_d = ["Todas"] + sorted(prods_d["cat"].dropna().unique().tolist())
            cat_f  = st.selectbox("Categoría",cats_d,key=f"cf_{mesa_id}")
            pdf    = prods_d if cat_f=="Todas" else prods_d[prods_d["cat"]==cat_f]

            c1,c2,c3,c4 = st.columns([3,1.5,2,1])
            ops      = [f"{r['nombre']} — {fmt(r['precio_venta'])}" for _,r in pdf.iterrows()]
            sel_p    = c1.selectbox("Producto",ops,key=f"sp_{mesa_id}")
            cant_i   = c2.number_input("Cant.",min_value=1,value=1,step=1,key=f"ci_{mesa_id}")
            op_per   = ["Mesa (compartido)"]+[p[1] for p in personas]
            pers_sel = c3.selectbox("Para quién",op_per,key=f"ps_{mesa_id}")

            if c4.button("➕",key=f"add_{mesa_id}",type="primary"):
                pnom = sel_p.split(" — ")[0]
                pr   = pdf[pdf["nombre"]==pnom].iloc[0]
                pid  = int(pr["id"]); prec=float(pr["precio_venta"])
                perid= personas_dict.get(pers_sel) if pers_sel!="Mesa (compartido)" else None
                st.session_state[key_cart].append({"pid":pid,"nombre":pnom,"cant":cant_i,
                    "precio":prec,"sub":cant_i*prec,"perid":perid,"pernomb":pers_sel})

            cart = st.session_state[key_cart]
            if cart:
                cdf2 = pd.DataFrame([{"Producto":i["nombre"],"Cant.":i["cant"],
                    "Precio":fmt(i["precio"]),"Subtotal":fmt(i["sub"]),"Para":i["pernomb"]} for i in cart])
                st.dataframe(cdf2,use_container_width=True,hide_index=True)
                st.markdown(f"**Total ronda: {fmt(sum(i['sub'] for i in cart))}**")

                c_env,c_vac = st.columns(2)
                with c_env:
                    if st.button("✅ Enviar pedido",type="primary",use_container_width=True):
                        hoy2=date.today().isoformat(); aho2=datetime.now().strftime("%H:%M:%S")
                        ronda=_ronda_actual(mesa_id)+1
                        with db_conn() as conn:
                            cur=conn.cursor()
                            for it in cart:
                                cur.execute(_p("""INSERT INTO pedidos_mesa
                                    (mesa_id,persona_id,producto_id,nombre_producto,
                                     cantidad,precio_unitario,subtotal,fecha,hora,usuario,ronda)
                                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""),
                                    (mesa_id,it["perid"],it["pid"],it["nombre"],
                                     it["cant"],it["precio"],it["sub"],hoy2,aho2,
                                     st.session_state.user,ronda))
                                cur.execute(_p("UPDATE productos SET stock=stock-%s WHERE id=%s"),
                                            (it["cant"],it["pid"]))
                        st.session_state[key_cart]=[]; st.success(f"Ronda #{ronda} enviada!"); st.rerun()
                with c_vac:
                    if st.button("🗑 Vaciar",use_container_width=True):
                        st.session_state[key_cart]=[]; st.rerun()

            st.markdown("---")
            st.markdown("**Historial de pedidos:**")
            hist=df("""SELECT pm.ronda,pm.hora,
                              COALESCE(pe.nombre,'Mesa (compartido)') as para,
                              pm.nombre_producto,pm.cantidad,pm.precio_unitario,pm.subtotal,pm.id
                       FROM pedidos_mesa pm LEFT JOIN personas_mesa pe ON pm.persona_id=pe.id
                       WHERE pm.mesa_id=%s AND pm.anulado=0 ORDER BY pm.ronda,pm.id""",(mesa_id,))
            if not hist.empty:
                hist.columns=["Ronda","Hora","Para","Producto","Cant.","Precio","Subtotal","id"]
                st.dataframe(hist.drop(columns=["id"]),use_container_width=True,hide_index=True)
                if st.session_state.rol=="admin":
                    ianu=st.number_input("Anular pedido ID",min_value=1,step=1,key=f"anu_{mesa_id}")
                    if st.button("🚫 Anular ítem",key=f"banu_{mesa_id}"):
                        ra=qry("SELECT producto_id,cantidad FROM pedidos_mesa WHERE id=%s AND mesa_id=%s",(ianu,mesa_id),one=True)
                        if ra:
                            exe("UPDATE pedidos_mesa SET anulado=1 WHERE id=%s",(ianu,))
                            exe("UPDATE productos SET stock=stock+%s WHERE id=%s",(ra[1],ra[0]))
                            st.success("Anulado."); st.rerun()

    # ── TAB PERSONAS ────────────────────────────────────────────────────────
    with tab_per:
        st.markdown("**Personas en esta mesa**")
        st.caption("Asigna pedidos a cada persona para dividir la cuenta al final.")
        if personas:
            for pid_p,pnom in personas:
                c1,c2=st.columns([4,1])
                c1.markdown(f'<span class="persona-chip">👤 {pnom}</span>',unsafe_allow_html=True)
                if c2.button("✕",key=f"qp_{pid_p}"):
                    exe("UPDATE personas_mesa SET activo=0 WHERE id=%s",(pid_p,)); st.rerun()
        else:
            st.info("Sin personas. Todos los pedidos van a la mesa completa.")

        st.markdown("---")
        with st.form(f"addp_{mesa_id}"):
            nom_p=st.text_input("Nombre")
            if st.form_submit_button("➕ Agregar"):
                if nom_p.strip():
                    exe("INSERT INTO personas_mesa(mesa_id,nombre) VALUES(%s,%s)",(mesa_id,nom_p.strip()))
                    st.success(f"'{nom_p}' agregado/a."); st.rerun()

        if personas:
            st.markdown("---"); st.markdown("**Consumo por persona (parcial):**")
            _tabla_cuenta(mesa_id,personas,solo_resumen=True)

    # ── TAB CUENTA ──────────────────────────────────────────────────────────
    with tab_cta:
        _cuenta_cobro(mesa_id,personas,mnombre,mestado)

# ─── LÓGICA DE CUENTA ────────────────────────────────────────────────────────
def _tabla_cuenta(mesa_id, personas, solo_resumen=False):
    n = max(len(personas),1)
    comp   = qry("SELECT COALESCE(SUM(subtotal),0) FROM pedidos_mesa WHERE mesa_id=%s AND persona_id IS NULL AND anulado=0",(mesa_id,),one=True)[0]
    cuota  = comp/n
    pers_df= df("""SELECT pe.nombre,SUM(pm.subtotal) as total,COUNT(pm.id) as items
                   FROM pedidos_mesa pm JOIN personas_mesa pe ON pm.persona_id=pe.id
                   WHERE pm.mesa_id=%s AND pm.anulado=0 GROUP BY pe.nombre""",(mesa_id,))
    resumen={pnom:{"propio":0.0} for _,pnom in personas}
    if not pers_df.empty:
        for _,r in pers_df.iterrows():
            if r["nombre"] in resumen:
                resumen[r["nombre"]]["propio"]=r["total"]
    rows=[{"Persona":p,"Pedidos propios":fmt(d["propio"]),"Cuota compartida":fmt(cuota),
           "TOTAL":fmt(d["propio"]+cuota)} for p,d in resumen.items()]
    if rows:
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        if not solo_resumen:
            st.caption(f"Compartido total {fmt(comp)} ÷ {n} personas = {fmt(cuota)} c/u")

def _cuenta_cobro(mesa_id, personas, mnombre, mestado):
    total_m = qry("SELECT COALESCE(SUM(subtotal),0) FROM pedidos_mesa WHERE mesa_id=%s AND anulado=0",(mesa_id,),one=True)[0]
    n_ped   = qry("SELECT COUNT(*) FROM pedidos_mesa WHERE mesa_id=%s AND anulado=0",(mesa_id,),one=True)[0]
    if total_m==0: st.info("No hay pedidos en esta mesa."); return

    st.markdown("### 🧾 Cuenta detallada")
    c1,c2=st.columns(2)
    c1.markdown(kpi("Total mesa",fmt(total_m),f"{n_ped} ítems","green"),unsafe_allow_html=True)
    c2.markdown(kpi("Personas",str(len(personas)),"en esta mesa","blue"),unsafe_allow_html=True)

    with st.expander("📋 Detalle por ronda"):
        rondas=df("""SELECT pm.ronda,pm.nombre_producto,
                            COALESCE(pe.nombre,'Mesa (compartido)') as para,
                            pm.cantidad,pm.precio_unitario,pm.subtotal
                     FROM pedidos_mesa pm LEFT JOIN personas_mesa pe ON pm.persona_id=pe.id
                     WHERE pm.mesa_id=%s AND pm.anulado=0 ORDER BY pm.ronda,pm.id""",(mesa_id,))
        rondas.columns=["Ronda","Producto","Para","Cant.","Precio","Subtotal"]
        st.dataframe(rondas,use_container_width=True,hide_index=True)

    if personas:
        st.markdown("---"); st.markdown("#### 👥 Cuenta por persona")
        _tabla_cuenta(mesa_id,personas,solo_resumen=False)
        with st.expander("🔍 Ver pedidos individuales detallados"):
            n2=max(len(personas),1)
            comp2=qry("SELECT COALESCE(SUM(subtotal),0) FROM pedidos_mesa WHERE mesa_id=%s AND persona_id IS NULL AND anulado=0",(mesa_id,),one=True)[0]
            cuota2=comp2/n2
            for pid_p,pnom in personas:
                pr2=df("SELECT nombre_producto,cantidad,precio_unitario,subtotal FROM pedidos_mesa WHERE mesa_id=%s AND persona_id=%s AND anulado=0 ORDER BY id",(mesa_id,pid_p))
                tot_p=float(pr2["subtotal"].sum()) if not pr2.empty else 0
                st.markdown(f"**👤 {pnom}** — Total: {fmt(tot_p+cuota2)}")
                if not pr2.empty:
                    pr2.columns=["Producto","Cant.","Precio","Subtotal"]
                    st.dataframe(pr2,use_container_width=True,hide_index=True)
                st.caption(f"+ Cuota compartida: {fmt(cuota2)}")
                st.markdown("---")

    st.markdown("---"); st.markdown("#### 💳 Registrar pago y cerrar mesa")
    desc_c=st.number_input("Descuento ($)",min_value=0.0,step=1000.0,key=f"dc_{mesa_id}")
    total_c=total_m-desc_c
    st.markdown(kpi("TOTAL A COBRAR",fmt(total_c),"","green"),unsafe_allow_html=True)
    met=st.selectbox("Método",["Efectivo","Tarjeta débito","Tarjeta crédito","Transferencia","Nequi","Daviplata"],key=f"met_{mesa_id}")
    if met=="Efectivo":
        rec=st.number_input("Recibido",min_value=0.0,value=float(total_c),step=1000.0,key=f"rec_{mesa_id}")
        cam=rec-total_c
        if cam>=0: st.success(f"Cambio: {fmt(cam)}")
        else: st.error(f"Falta: {fmt(-cam)}")
    nota_c=st.text_input("Nota de cierre",key=f"nc_{mesa_id}")

    c_cobr,c_mrc=st.columns(2)
    with c_cobr:
        if st.button("✅ COBRAR Y CERRAR MESA",type="primary",use_container_width=True):
            if total_c>0:
                hoy3=date.today().isoformat(); aho3=datetime.now().strftime("%H:%M:%S")
                items3=qry("""SELECT producto_id,nombre_producto,SUM(cantidad),precio_unitario,SUM(subtotal)
                               FROM pedidos_mesa WHERE mesa_id=%s AND anulado=0
                               GROUP BY producto_id,nombre_producto,precio_unitario""",(mesa_id,))
                with db_conn() as conn:
                    cur=conn.cursor()
                    vid=insert_cur(cur,_p("INSERT INTO ventas(fecha,hora,total,descuento,metodo_pago,usuario,nota,origen) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"),
                        (hoy3,aho3,total_c,desc_c,met,st.session_state.user,f"{mnombre}|{nota_c}","mesa"))
                    for pp,pn,cant,pu,sub in items3:
                        cur.execute(_p("INSERT INTO detalle_ventas(venta_id,producto_id,nombre_producto,cantidad,precio_unitario,subtotal) VALUES(%s,%s,%s,%s,%s,%s)"),
                            (vid,pp,pn,cant,pu,sub))
                    cur.execute(_p("UPDATE mesas SET estado='libre',fecha_apertura=NULL,hora_apertura=NULL WHERE id=%s"),(mesa_id,))
                    cur.execute(_p("UPDATE personas_mesa SET activo=0 WHERE mesa_id=%s"),(mesa_id,))
                st.session_state[f"cart_m_{mesa_id}"]=[]
                st.session_state.mesa_vista=None
                st.success(f"{mnombre} cobrada. Venta #{vid} — {fmt(total_c)}"); st.rerun()
    with c_mrc:
        if mestado!="cuenta":
            if st.button("🔔 Marcar 'Pidiendo cuenta'",use_container_width=True):
                exe("UPDATE mesas SET estado='cuenta' WHERE id=%s",(mesa_id,)); st.rerun()
        else:
            if st.button("↩ Volver a 'Ocupada'",use_container_width=True):
                exe("UPDATE mesas SET estado='ocupada' WHERE id=%s",(mesa_id,)); st.rerun()

# ─── INVENTARIO ──────────────────────────────────────────────────────────────
def page_inventario():
    st.markdown("## 📦 Inventario")
    tab1,tab2,tab3=st.tabs(["📋 Productos","➕ Nuevo producto","📥 Entrada de stock"])

    with tab1:
        cats_l=["Todas"]+[r[0] for r in qry("SELECT nombre FROM categorias ORDER BY nombre")]
        c1,c2=st.columns(2)
        fcat=c1.selectbox("Categoría",cats_l)
        sbaj=c2.checkbox("Solo stock bajo")
        sql2="SELECT p.codigo,p.nombre,c.nombre as cat,p.precio_venta,p.precio_costo,p.stock,p.stock_minimo,p.unidad FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id WHERE p.activo=1"
        par2=[]
        if fcat!="Todas": sql2+=" AND c.nombre=%s"; par2.append(fcat)
        if sbaj: sql2+=" AND p.stock<=p.stock_minimo"
        sql2+=" ORDER BY p.nombre"
        inv=df(sql2,par2)
        if not inv.empty:
            inv["Estado"]=inv.apply(lambda r:"🔴 Bajo" if r["stock"]<=r["stock_minimo"] else "🟢 OK",axis=1)
            inv.columns=["Código","Nombre","Categoría","Precio Venta","Precio Costo","Stock","Stock Mín.","Unidad","Estado"]
            st.dataframe(inv,use_container_width=True,hide_index=True)
        else: st.info("No hay productos.")

    with tab2:
        cats2={r[0]:r[1] for r in qry("SELECT nombre,id FROM categorias ORDER BY nombre")}
        provs2={r[0]:r[1] for r in qry("SELECT nombre,id FROM proveedores WHERE activo=1 ORDER BY nombre")}
        provs2["(Sin proveedor)"]=None
        with st.form("np"):
            c1,c2=st.columns(2)
            cod=c1.text_input("Código *"); nom=c2.text_input("Nombre *")
            cat=c1.selectbox("Categoría",list(cats2.keys()))
            prov=c2.selectbox("Proveedor",list(provs2.keys()))
            pv=c1.number_input("Precio venta",min_value=0.0,step=500.0)
            pc=c2.number_input("Precio costo",min_value=0.0,step=500.0)
            si=c1.number_input("Stock inicial",min_value=0.0,step=1.0)
            sm=c2.number_input("Stock mínimo",min_value=0.0,value=5.0,step=1.0)
            uni=c1.text_input("Unidad","unidad")
            if st.form_submit_button("✅ Crear",type="primary"):
                if not cod or not nom: st.error("Código y nombre requeridos.")
                elif qry("SELECT 1 FROM productos WHERE codigo=%s",(cod,),one=True): st.error("Código ya existe.")
                else:
                    exe("INSERT INTO productos(codigo,nombre,categoria_id,proveedor_id,precio_venta,precio_costo,stock,stock_minimo,unidad) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (cod,nom,cats2[cat],provs2[prov],pv,pc,si,sm,uni))
                    st.success(f"'{nom}' creado."); st.rerun()

    with tab3:
        prods3=df("SELECT id,nombre,stock FROM productos WHERE activo=1 ORDER BY nombre")
        provs3=qry("SELECT id,nombre FROM proveedores WHERE activo=1 ORDER BY nombre")
        if prods3.empty: st.warning("Crea productos primero.")
        else:
            with st.form("ent"):
                psel=st.selectbox("Proveedor",["(Ninguno)"]+[r[1] for r in provs3])
                nota_e=st.text_input("Nota / # Factura")
                fecha_e=st.date_input("Fecha",date.today())
                items_e=[]
                for i in range(8):
                    c1,c2,c3=st.columns([3,1,1])
                    op=c1.selectbox(f"Producto {i+1}",["(ninguno)"]+prods3["nombre"].tolist(),key=f"ep{i}")
                    ca=c2.number_input("Cant.",min_value=0.0,step=1.0,key=f"ec{i}")
                    co=c3.number_input("Costo",min_value=0.0,step=100.0,key=f"eco{i}")
                    if op!="(ninguno)" and ca>0:
                        pid_e=int(prods3[prods3["nombre"]==op]["id"].values[0])
                        items_e.append((pid_e,op,ca,co))
                if st.form_submit_button("📥 Registrar",type="primary"):
                    if not items_e: st.error("Agrega al menos un producto.")
                    else:
                        total_e=sum(i[2]*i[3] for i in items_e)
                        prov_id_e=None
                        if psel!="(Ninguno)":
                            r3=qry("SELECT id FROM proveedores WHERE nombre=%s",(psel,),one=True)
                            if r3: prov_id_e=r3[0]
                        with db_conn() as conn:
                            cur=conn.cursor()
                            cid=insert_cur(cur,"INSERT INTO compras(fecha,proveedor_id,total,nota,usuario) VALUES(%s,%s,%s,%s,%s)",
                                (fecha_e.isoformat(),prov_id_e,total_e,nota_e,st.session_state.user))
                            for pid_e,pn_e,ca_e,co_e in items_e:
                                cur.execute(_p("INSERT INTO detalle_compras(compra_id,producto_id,nombre_producto,cantidad,precio_unitario,subtotal) VALUES(%s,%s,%s,%s,%s,%s)"),
                                    (cid,pid_e,pn_e,ca_e,co_e,ca_e*co_e))
                                cur.execute(_p("UPDATE productos SET stock=stock+%s WHERE id=%s"),(ca_e,pid_e))
                        st.success(f"Entrada registrada. Total: {fmt(total_e)}"); st.rerun()

# ─── CAJA RÁPIDA ─────────────────────────────────────────────────────────────
def page_caja():
    st.markdown("## 🧾 Caja rápida")
    st.caption("Pedidos directos sin mesa. Para ventas por mesa usa el módulo **Mesas**.")
    tab1,tab2=st.tabs(["💳 Nueva venta","📜 Historial"])

    with tab1:
        if "carrito_caja" not in st.session_state: st.session_state.carrito_caja=[]
        prods_c=df("""SELECT p.id,p.codigo,p.nombre,p.precio_venta,p.stock,c.nombre as cat
                      FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id
                      WHERE p.activo=1 AND p.stock>0 ORDER BY c.nombre,p.nombre""")
        col_l,col_r=st.columns([3,2])
        with col_l:
            if prods_c.empty: st.warning("Sin productos.")
            else:
                cats_c=["Todas"]+sorted(prods_c["cat"].dropna().unique().tolist())
                cat_fc=st.selectbox("Categoría",cats_c,key="cc_cat")
                pf=prods_c if cat_fc=="Todas" else prods_c[prods_c["cat"]==cat_fc]
                c1,c2,c3=st.columns([3,1.5,1])
                ops=[f"[{r['codigo']}] {r['nombre']} — {fmt(r['precio_venta'])}" for _,r in pf.iterrows()]
                sp=c1.selectbox("Producto",ops,key="cc_prod")
                ca=c2.number_input("Cant.",min_value=0.1,value=1.0,step=1.0,key="cc_cant")
                if c3.button("➕",type="primary",key="cc_add"):
                    cod_s=sp.split("]")[0][1:]
                    rp=pf[pf["codigo"]==cod_s].iloc[0]
                    if ca>rp["stock"]: st.error(f"Stock insuficiente. Hay {rp['stock']}")
                    else:
                        ex=next((i for i,it in enumerate(st.session_state.carrito_caja) if it["id"]==int(rp["id"])),None)
                        if ex is not None:
                            st.session_state.carrito_caja[ex]["cant"]+=ca
                            st.session_state.carrito_caja[ex]["sub"]=st.session_state.carrito_caja[ex]["cant"]*st.session_state.carrito_caja[ex]["precio"]
                        else:
                            st.session_state.carrito_caja.append({"id":int(rp["id"]),"codigo":rp["codigo"],
                                "nombre":rp["nombre"],"precio":float(rp["precio_venta"]),"cant":ca,"sub":ca*float(rp["precio_venta"])})
            if st.session_state.carrito_caja:
                st.markdown("---")
                cdf3=pd.DataFrame([{"Producto":i["nombre"],"Cant.":i["cant"],"Precio":fmt(i["precio"]),"Subtotal":fmt(i["sub"])} for i in st.session_state.carrito_caja])
                st.dataframe(cdf3,use_container_width=True,hide_index=True)
                idx_d=st.number_input("Eliminar ítem #",min_value=1,max_value=len(st.session_state.carrito_caja),step=1)
                c_d1,c_d2=st.columns(2)
                if c_d1.button("🗑 Eliminar"): st.session_state.carrito_caja.pop(idx_d-1); st.rerun()
                if c_d2.button("🗑 Vaciar"): st.session_state.carrito_caja=[]; st.rerun()
        with col_r:
            st.markdown("**Cobro**")
            if st.session_state.carrito_caja:
                sub_c=sum(i["sub"] for i in st.session_state.carrito_caja)
                desc_c2=st.number_input("Descuento ($)",min_value=0.0,step=1000.0)
                total_c2=sub_c-desc_c2
                st.markdown(kpi("Total",fmt(total_c2),f"Subtotal {fmt(sub_c)}","green"),unsafe_allow_html=True)
                met_c=st.selectbox("Método",["Efectivo","Tarjeta débito","Tarjeta crédito","Transferencia","Nequi","Daviplata"])
                if met_c=="Efectivo":
                    rec_c=st.number_input("Recibido",min_value=0.0,value=float(total_c2),step=1000.0)
                    cam_c=rec_c-total_c2
                    if cam_c>=0: st.success(f"Cambio: {fmt(cam_c)}")
                    else: st.error(f"Falta: {fmt(-cam_c)}")
                nota_c2=st.text_input("Nota")
                if st.button("✅ COBRAR",type="primary",use_container_width=True):
                    if total_c2>0:
                        hc=date.today().isoformat(); ahc=datetime.now().strftime("%H:%M:%S")
                        with db_conn() as conn:
                            cur=conn.cursor()
                            vc=insert_cur(cur,"INSERT INTO ventas(fecha,hora,total,descuento,metodo_pago,usuario,nota) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                                (hc,ahc,total_c2,desc_c2,met_c,st.session_state.user,nota_c2))
                            for it in st.session_state.carrito_caja:
                                cur.execute(_p("INSERT INTO detalle_ventas(venta_id,producto_id,nombre_producto,cantidad,precio_unitario,subtotal) VALUES(%s,%s,%s,%s,%s,%s)"),
                                    (vc,it["id"],it["nombre"],it["cant"],it["precio"],it["sub"]))
                                cur.execute(_p("UPDATE productos SET stock=stock-%s WHERE id=%s"),(it["cant"],it["id"]))
                        st.session_state.carrito_caja=[]
                        st.success(f"Venta #{vc} — {fmt(total_c2)}"); st.rerun()
            else: st.info("Carrito vacío.")

    with tab2:
        c1,c2=st.columns(2)
        fd_h=c1.date_input("Desde",date.today(),key="hd")
        fh_h=c2.date_input("Hasta",date.today(),key="hh")
        hv=df("SELECT id,fecha,hora,total,descuento,metodo_pago,origen,usuario,nota,anulada FROM ventas WHERE fecha>=%s AND fecha<=%s ORDER BY fecha DESC,hora DESC",
              (fd_h.isoformat(),fh_h.isoformat()))
        if not hv.empty:
            hv.columns=["ID","Fecha","Hora","Total","Descuento","Método","Origen","Usuario","Nota","Anulada"]
            hv["Anulada"]=hv["Anulada"].map({0:"No",1:"Sí"})
            st.markdown(f"**Total: {fmt(hv[hv['Anulada']=='No']['Total'].sum())}**")
            st.dataframe(hv,use_container_width=True,hide_index=True)
        else: st.info("Sin ventas.")

# ─── NÓMINA ──────────────────────────────────────────────────────────────────
RECARGO={"Normal":1.0,"Nocturno":1.35,"Dominical/Festivo":1.75,"Extra diurno":1.25,"Extra nocturno":1.75}

def page_nomina():
    st.markdown("## 👥 Nómina por horas")
    tab1,tab2,tab3,tab4=st.tabs(["👤 Empleados","⏱ Horas","💰 Liquidar","📋 Historial"])

    with tab1:
        c_l,c_r=st.columns(2)
        with c_l:
            ed=df("SELECT id,nombre,cedula,cargo,telefono,tarifa_hora,fecha_ingreso FROM empleados WHERE activo=1 ORDER BY nombre")
            if not ed.empty:
                ed.columns=["ID","Nombre","Cédula","Cargo","Teléfono","Tarifa/H","Ingreso"]
                st.dataframe(ed,use_container_width=True,hide_index=True)
            else: st.info("No hay empleados.")
        with c_r:
            with st.form("nemp"):
                nom_e=st.text_input("Nombre *"); ced_e=st.text_input("Cédula *")
                car_e=st.selectbox("Cargo",["Barman","Mesero/a","Cajero/a","Domiciliario","Vigilante","Administrador","Otro"])
                tel_e=st.text_input("Teléfono"); tar_e=st.number_input("Tarifa/hora ($)",min_value=0.0,step=500.0)
                fi_e=st.date_input("Ingreso",date.today())
                if st.form_submit_button("✅ Crear"):
                    if not nom_e or not ced_e or tar_e<=0: st.error("Nombre, cédula y tarifa requeridos.")
                    elif qry("SELECT 1 FROM empleados WHERE cedula=%s",(ced_e,),one=True): st.error("Cédula ya existe.")
                    else:
                        exe("INSERT INTO empleados(nombre,cedula,cargo,telefono,tarifa_hora,fecha_ingreso) VALUES(%s,%s,%s,%s,%s,%s)",
                            (nom_e,ced_e,car_e,tel_e,tar_e,fi_e.isoformat()))
                        st.success("Empleado creado."); st.rerun()

    with tab2:
        emps2=qry("SELECT id,nombre,tarifa_hora FROM empleados WHERE activo=1 ORDER BY nombre")
        if not emps2: st.warning("No hay empleados.")
        else:
            ed2={r[1]:r[0] for r in emps2}; et2={r[1]:r[2] for r in emps2}
            with st.form("rh"):
                emp_s=st.selectbox("Empleado",list(ed2.keys()))
                c1,c2,c3=st.columns(3)
                feh=c1.date_input("Fecha",date.today())
                hen=c2.text_input("Entrada (HH:MM)","08:00"); hsa=c3.text_input("Salida (HH:MM)","17:00")
                tip=st.selectbox("Tipo",list(RECARGO.keys())); not_h=st.text_input("Nota")
                hh=0.0
                try:
                    d1=datetime.strptime(hen,"%H:%M"); d2=datetime.strptime(hsa,"%H:%M")
                    hh=round((d2-d1).seconds/3600,2)
                except: pass
                tar_h=et2.get(emp_s,0); pag_e=hh*tar_h*RECARGO.get(tip,1.0)
                if hh>0: st.info(f"Horas: {hh:.2f} | Factor: {RECARGO[tip]}x | Pago: {fmt(pag_e)}")
                if st.form_submit_button("⏱ Registrar"):
                    if hh<=0: st.error("Verifica horas.")
                    else:
                        exe("INSERT INTO horas_trabajo(empleado_id,fecha,hora_entrada,hora_salida,horas_trabajadas,tipo,nota) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                            (ed2[emp_s],feh.isoformat(),hen,hsa,hh,tip,not_h))
                        st.success("Registrado."); st.rerun()
            pen=df("SELECT h.id,e.nombre,h.fecha,h.hora_entrada,h.hora_salida,h.horas_trabajadas,h.tipo FROM horas_trabajo h JOIN empleados e ON h.empleado_id=e.id WHERE h.pagado=0 ORDER BY h.fecha DESC")
            if not pen.empty:
                pen.columns=["ID","Empleado","Fecha","Entrada","Salida","Horas","Tipo"]
                st.markdown("**Horas pendientes:**"); st.dataframe(pen,use_container_width=True,hide_index=True)

    with tab3:
        emps3=qry("SELECT id,nombre,tarifa_hora FROM empleados WHERE activo=1 ORDER BY nombre")
        if not emps3: st.warning("No hay empleados.")
        else:
            ed3={r[1]:(r[0],r[2]) for r in emps3}
            el=st.selectbox("Empleado",list(ed3.keys()),key="liq_e")
            c1,c2=st.columns(2)
            pi=c1.date_input("Desde",date.today()-timedelta(days=7))
            pf_l=c2.date_input("Hasta",date.today())
            eid_l,tar_l=ed3[el]
            hp=df("SELECT id,fecha,horas_trabajadas,tipo FROM horas_trabajo WHERE empleado_id=%s AND pagado=0 AND fecha>=%s AND fecha<=%s ORDER BY fecha",
                  (eid_l,pi.isoformat(),pf_l.isoformat()))
            if not hp.empty:
                hp["monto"]=hp.apply(lambda r:r["horas_trabajadas"]*tar_l*RECARGO.get(r["tipo"],1.0),axis=1)
                th=hp["horas_trabajadas"].sum(); tm=hp["monto"].sum()
                hp.columns=["ID","Fecha","Horas","Tipo","Monto"]
                st.dataframe(hp,use_container_width=True,hide_index=True)
                c1,c2=st.columns(2)
                c1.markdown(kpi("Horas",f"{th:.2f} h","","blue"),unsafe_allow_html=True)
                c2.markdown(kpi("A pagar",fmt(tm),f"Tarifa {fmt(tar_l)}/h","green"),unsafe_allow_html=True)
                met_n=st.selectbox("Método pago",["Efectivo","Transferencia","Nequi","Daviplata"])
                if st.button("💰 Liquidar",type="primary"):
                    ids_l=hp["ID"].tolist()
                    with db_conn() as conn:
                        cur=conn.cursor()
                        cur.execute(_p("INSERT INTO pagos_nomina(empleado_id,periodo_inicio,periodo_fin,horas_totales,monto_total,fecha_pago,metodo_pago,usuario) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"),
                            (eid_l,pi.isoformat(),pf_l.isoformat(),th,tm,date.today().isoformat(),met_n,st.session_state.user))
                        for hid in ids_l:
                            cur.execute(_p("UPDATE horas_trabajo SET pagado=1 WHERE id=%s"),(hid,))
                    st.success(f"Pago {fmt(tm)} registrado."); st.rerun()
            else: st.info("Sin horas pendientes.")

    with tab4:
        c1,c2=st.columns(2)
        fdn=c1.date_input("Desde",date.today()-timedelta(days=30),key="hn_d")
        fhn=c2.date_input("Hasta",date.today(),key="hn_h")
        hn=df("SELECT pn.id,e.nombre,pn.periodo_inicio,pn.periodo_fin,pn.horas_totales,pn.monto_total,pn.fecha_pago,pn.metodo_pago FROM pagos_nomina pn JOIN empleados e ON pn.empleado_id=e.id WHERE pn.fecha_pago>=%s AND pn.fecha_pago<=%s ORDER BY pn.fecha_pago DESC",
              (fdn.isoformat(),fhn.isoformat()))
        if not hn.empty:
            hn.columns=["ID","Empleado","Desde","Hasta","Horas","Total","Fecha","Método"]
            st.markdown(f"**Total nómina: {fmt(hn['Total'].sum())}**")
            st.dataframe(hn,use_container_width=True,hide_index=True)
        else: st.info("Sin pagos.")

# ─── PROVEEDORES ─────────────────────────────────────────────────────────────
def page_proveedores():
    st.markdown("## 🏪 Proveedores")
    tab1,tab2=st.tabs(["📋 Lista","➕ Nuevo"])
    with tab1:
        pv=df("SELECT id,nombre,contacto,telefono,email,nit FROM proveedores WHERE activo=1 ORDER BY nombre")
        if not pv.empty:
            pv.columns=["ID","Nombre","Contacto","Teléfono","Email","NIT"]
            st.dataframe(pv,use_container_width=True,hide_index=True)
        else: st.info("Sin proveedores.")
    with tab2:
        with st.form("nprov"):
            c1,c2=st.columns(2)
            np_=c1.text_input("Nombre *"); nc_=c2.text_input("Contacto")
            nt_=c1.text_input("Teléfono"); ne_=c2.text_input("Email"); nn_=st.text_input("NIT")
            if st.form_submit_button("✅ Crear"):
                if not np_: st.error("Nombre requerido.")
                else:
                    exe("INSERT INTO proveedores(nombre,contacto,telefono,email,nit) VALUES(%s,%s,%s,%s,%s)",(np_,nc_,nt_,ne_,nn_))
                    st.success(f"'{np_}' creado."); st.rerun()

# ─── GASTOS ──────────────────────────────────────────────────────────────────
CATS_G=["Servicios públicos","Arriendo/Local","Publicidad","Aseo y limpieza",
        "Mantenimiento","Transporte","Impuestos y tasas","Música/Entretenimiento","Otros"]

def page_gastos():
    st.markdown("## 💸 Gastos operativos")
    tab1,tab2=st.tabs(["➕ Registrar","📋 Historial"])
    with tab1:
        with st.form("ng"):
            c1,c2=st.columns(2)
            fg=c1.date_input("Fecha",date.today()); cg=c2.selectbox("Categoría",CATS_G)
            dg=c1.text_input("Descripción"); mg=c2.number_input("Monto ($)",min_value=0.0,step=1000.0)
            mtg=st.selectbox("Método",["Efectivo","Transferencia","Tarjeta"])
            if st.form_submit_button("💾 Registrar"):
                if mg<=0: st.error("Monto > 0")
                else:
                    exe("INSERT INTO gastos(fecha,categoria,descripcion,monto,metodo_pago,usuario) VALUES(%s,%s,%s,%s,%s,%s)",
                        (fg.isoformat(),cg,dg,mg,mtg,st.session_state.user))
                    st.success(f"Gasto {fmt(mg)} registrado."); st.rerun()
    with tab2:
        c1,c2=st.columns(2)
        fdg=c1.date_input("Desde",date.today()-timedelta(days=30),key="gd")
        fhg=c2.date_input("Hasta",date.today(),key="gh")
        gdf2=df("SELECT id,fecha,categoria,descripcion,monto,metodo_pago FROM gastos WHERE fecha>=%s AND fecha<=%s ORDER BY fecha DESC",
               (fdg.isoformat(),fhg.isoformat()))
        if not gdf2.empty:
            gdf2.columns=["ID","Fecha","Categoría","Descripción","Monto","Método"]
            st.markdown(f"**Total: {fmt(gdf2['Monto'].sum())}**")
            st.dataframe(gdf2,use_container_width=True,hide_index=True)
            pc=gdf2.groupby("Categoría")["Monto"].sum().reset_index()
            fig=px.pie(pc,names="Categoría",values="Monto",color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(paper_bgcolor="#1a1d2e",font_color="#e2c97e")
            st.plotly_chart(fig,use_container_width=True)
        else: st.info("Sin gastos.")

# ─── BALANCE ─────────────────────────────────────────────────────────────────
def page_balance():
    st.markdown("## 📊 Balance financiero")
    c1,c2=st.columns(2)
    fdb=c1.date_input("Desde",date.today().replace(day=1))
    fhb=c2.date_input("Hasta",date.today())
    f1,f2=fdb.isoformat(),fhb.isoformat()

    ing  =qry("SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha>=%s AND fecha<=%s AND anulada=0",(f1,f2),one=True)[0]
    costo=qry("SELECT COALESCE(SUM(dv.cantidad*p.precio_costo),0) FROM detalle_ventas dv JOIN ventas v ON dv.venta_id=v.id JOIN productos p ON dv.producto_id=p.id WHERE v.fecha>=%s AND v.fecha<=%s AND v.anulada=0",(f1,f2),one=True)[0]
    gop  =qry("SELECT COALESCE(SUM(monto),0) FROM gastos WHERE fecha>=%s AND fecha<=%s",(f1,f2),one=True)[0]
    nom  =qry("SELECT COALESCE(SUM(monto_total),0) FROM pagos_nomina WHERE fecha_pago>=%s AND fecha_pago<=%s",(f1,f2),one=True)[0]
    comp =qry("SELECT COALESCE(SUM(total),0) FROM compras WHERE fecha>=%s AND fecha<=%s",(f1,f2),one=True)[0]
    ub=ing-costo; un=ub-gop-nom

    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown(kpi("Ingresos ventas",fmt(ing),"","green"),unsafe_allow_html=True)
        st.markdown(kpi("Costo de ventas",fmt(costo),"","red"),unsafe_allow_html=True)
        st.markdown(kpi("Utilidad bruta",fmt(ub),f"Margen {ub/ing*100:.1f}%" if ing>0 else "","green" if ub>=0 else "red"),unsafe_allow_html=True)
    with c2:
        st.markdown(kpi("Gastos operativos",fmt(gop),"","yellow"),unsafe_allow_html=True)
        st.markdown(kpi("Nómina pagada",fmt(nom),"","orange"),unsafe_allow_html=True)
        st.markdown(kpi("Compras inventario",fmt(comp),"","purple"),unsafe_allow_html=True)
    with c3:
        st.markdown(kpi("UTILIDAD NETA",fmt(un),f"Margen {un/ing*100:.1f}%" if ing>0 else "","green" if un>=0 else "red"),unsafe_allow_html=True)

    st.divider()
    vd=df("SELECT fecha,SUM(total) as ingresos FROM ventas WHERE fecha>=%s AND fecha<=%s AND anulada=0 GROUP BY fecha",(f1,f2))
    gd=df("SELECT fecha,SUM(monto) as egresos FROM gastos WHERE fecha>=%s AND fecha<=%s GROUP BY fecha",(f1,f2))
    if not vd.empty or not gd.empty:
        flujo=pd.merge(vd,gd,on="fecha",how="outer").fillna(0).sort_values("fecha")
        fig=go.Figure()
        fig.add_bar(x=flujo["fecha"],y=flujo.get("ingresos",0),name="Ingresos",marker_color="#22c55e")
        fig.add_bar(x=flujo["fecha"],y=flujo.get("egresos",0),name="Gastos",marker_color="#ef4444")
        fig.update_layout(barmode="group",paper_bgcolor="#1a1d2e",plot_bgcolor="#1a1d2e",font_color="#e2c97e")
        st.plotly_chart(fig,use_container_width=True)

    st.markdown("### Estado de resultados")
    st.table(pd.DataFrame({"Concepto":["(+) Ingresos","(-) Costo ventas","(=) Utilidad bruta","(-) Gastos op.","(-) Nómina","(=) UTILIDAD NETA"],
                           "Monto":[fmt(ing),fmt(-costo),fmt(ub),fmt(-gop),fmt(-nom),fmt(un)]}))

# ─── REPORTES ────────────────────────────────────────────────────────────────
def page_reportes():
    st.markdown("## 📈 Reportes")
    tipo=st.selectbox("Tipo",["Ventas por período","Mesas por día","Productos más vendidos","Horas por empleado","Compras por proveedor"])
    c1,c2=st.columns(2)
    fdr=c1.date_input("Desde",date.today()-timedelta(days=30)); fhr=c2.date_input("Hasta",date.today())
    f1r,f2r=fdr.isoformat(),fhr.isoformat()
    dff=None
    if tipo=="Ventas por período":
        dff=df("SELECT fecha,COUNT(*) as n,SUM(total) as total,metodo_pago FROM ventas WHERE fecha>=%s AND fecha<=%s AND anulada=0 GROUP BY fecha,metodo_pago ORDER BY fecha",(f1r,f2r))
    elif tipo=="Mesas por día":
        dff=df("SELECT fecha,COUNT(id) as ventas,SUM(total) as total FROM ventas WHERE origen='mesa' AND fecha>=%s AND fecha<=%s AND anulada=0 GROUP BY fecha ORDER BY fecha",(f1r,f2r))
    elif tipo=="Productos más vendidos":
        dff=df("SELECT dv.nombre_producto,SUM(dv.cantidad) as u,SUM(dv.subtotal) as ing FROM detalle_ventas dv JOIN ventas v ON dv.venta_id=v.id WHERE v.fecha>=%s AND v.fecha<=%s AND v.anulada=0 GROUP BY dv.nombre_producto ORDER BY ing DESC LIMIT 20",(f1r,f2r))
    elif tipo=="Horas por empleado":
        dff=df("SELECT e.nombre,h.tipo,COUNT(*) as turnos,SUM(h.horas_trabajadas) as horas FROM horas_trabajo h JOIN empleados e ON h.empleado_id=e.id WHERE h.fecha>=%s AND h.fecha<=%s GROUP BY e.nombre,h.tipo ORDER BY e.nombre",(f1r,f2r))
    elif tipo=="Compras por proveedor":
        dff=df("SELECT pv.nombre,COUNT(c.id) as compras,SUM(c.total) as total FROM compras c JOIN proveedores pv ON c.proveedor_id=pv.id WHERE c.fecha>=%s AND c.fecha<=%s GROUP BY pv.nombre ORDER BY total DESC",(f1r,f2r))
    if dff is not None and not dff.empty:
        st.dataframe(dff,use_container_width=True,hide_index=True)
        st.download_button("⬇️ CSV",dff.to_csv(index=False).encode(),"reporte.csv","text/csv")
    else:
        st.info("Sin datos en el período.")

# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────
def page_config():
    st.markdown("## ⚙️ Configuración")
    if st.session_state.rol!="admin": st.warning("Solo administradores."); return
    tab1,tab2,tab3=st.tabs(["👤 Usuarios","🏷️ Categorías","🪑 Mesas"])
    with tab1:
        udf2=df("SELECT id,username,rol,activo FROM usuarios ORDER BY username")
        if not udf2.empty:
            udf2.columns=["ID","Usuario","Rol","Activo"]; udf2["Activo"]=udf2["Activo"].map({1:"✅",0:"❌"})
            st.dataframe(udf2,use_container_width=True,hide_index=True)
        with st.form("nu"):
            c1,c2=st.columns(2)
            un_=c1.text_input("Usuario"); pw_=c2.text_input("Contraseña",type="password")
            rol_=st.selectbox("Rol",["cajero","barman","admin"])
            if st.form_submit_button("Crear"):
                if not un_ or not pw_: st.error("Requeridos.")
                elif qry("SELECT 1 FROM usuarios WHERE username=%s",(un_,),one=True): st.error("Ya existe.")
                else:
                    exe("INSERT INTO usuarios(username,password,rol) VALUES(%s,%s,%s)",(un_,hsh(pw_),rol_))
                    st.success(f"'{un_}' creado."); st.rerun()
        with st.form("cpw"):
            us_=st.selectbox("Usuario",[r[0] for r in qry("SELECT username FROM usuarios WHERE activo=1")])
            pw1_=st.text_input("Nueva contraseña",type="password"); pw2_=st.text_input("Confirmar",type="password")
            if st.form_submit_button("Cambiar"):
                if pw1_!=pw2_: st.error("No coinciden.")
                elif len(pw1_)<6: st.error("Mínimo 6 caracteres.")
                else: exe("UPDATE usuarios SET password=%s WHERE username=%s",(hsh(pw1_),us_)); st.success("Actualizada.")
    with tab2:
        cdf3=df("SELECT id,nombre,color FROM categorias ORDER BY nombre")
        if not cdf3.empty:
            cdf3.columns=["ID","Nombre","Color"]; st.dataframe(cdf3,use_container_width=True,hide_index=True)
        with st.form("ncat"):
            c1,c2=st.columns(2)
            cn_=c1.text_input("Categoría"); cc_=c2.color_picker("Color","#c8941a")
            if st.form_submit_button("Agregar"):
                if cn_:
                    exe("INSERT INTO categorias(nombre,color) VALUES(%s,%s) ON CONFLICT DO NOTHING" if USE_PG
                        else "INSERT OR IGNORE INTO categorias(nombre,color) VALUES(%s,%s)",(cn_,cc_))
                    st.success(f"'{cn_}' agregada."); st.rerun()
    with tab3:
        mc=df("SELECT id,numero,nombre,capacidad,estado FROM mesas ORDER BY numero")
        if not mc.empty:
            mc.columns=["ID","#","Nombre","Capacidad","Estado"]; st.dataframe(mc,use_container_width=True,hide_index=True)
        with st.form("emesa"):
            mid_e=st.number_input("ID mesa",min_value=1,step=1)
            c1,c2=st.columns(2)
            nn_m=c1.text_input("Nuevo nombre"); nc_m=c2.number_input("Capacidad",min_value=1,value=4)
            if st.form_submit_button("Guardar"):
                exe("UPDATE mesas SET nombre=%s,capacidad=%s WHERE id=%s AND estado='libre'",(nn_m,nc_m,mid_e))
                st.success("Actualizada."); st.rerun()

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    if "user" not in st.session_state:
        login(); return

    with st.sidebar:
        logo_b64=get_logo_b64()
        logo_html=f'<img src="data:image/png;base64,{logo_b64}" class="tribu-logo-sidebar">' \
                  if logo_b64 else '<div style="text-align:center;font-size:36px">🪶</div>'
        st.markdown(f"""
        <div class="tribu-brand">
            {logo_html}
            <span class="brand-name">LA TRIBU</span>
            <span class="brand-sub">Cafe · Bar</span>
        </div>""", unsafe_allow_html=True)
        rol=st.session_state.rol
        badge={'admin':'<span class="badge-admin">⚡ ADMIN</span>',
               'barman':'<span class="badge-barman">🍹 BARMAN</span>'}.get(rol,'<span class="badge-cajero">💼 CAJERO</span>')
        st.markdown(f"<div style='text-align:center;margin:8px 0'>{badge}</div>",unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;color:#5a5033;font-size:12px;margin-bottom:8px'>👤 {st.session_state.user}</div>",unsafe_allow_html=True)
        st.divider()
        pagina=st.radio("Ir a",["🏠 Dashboard","🪑 Mesas","🧾 Caja rápida","📦 Inventario",
            "👥 Nómina","🏪 Proveedores","💸 Gastos","📊 Balance","📈 Reportes","⚙️ Configuración"],
            label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Salir",use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    {"🏠 Dashboard":page_dashboard,"🪑 Mesas":page_mesas,"🧾 Caja rápida":page_caja,
     "📦 Inventario":page_inventario,"👥 Nómina":page_nomina,"🏪 Proveedores":page_proveedores,
     "💸 Gastos":page_gastos,"📊 Balance":page_balance,"📈 Reportes":page_reportes,
     "⚙️ Configuración":page_config}[pagina]()

if __name__=="__main__":
    main()
