# main.py
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import requests
import time
from database import init_db
from views import home, vendas, estoque, financeiro, clientes, login, usuarios
@st.cache_data(show_spinner=False)
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=2)
        return r.json() if r.status_code == 200 else None
    except:
        return None
# Config
st.set_page_config(page_title="Cerrado Tereré 67", layout="wide", page_icon="🌿")

# CSS
st.markdown("""
    <style>
    section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }
    .sidebar-title { text-align: center; font-size: 24px; font-weight: bold; color: #2E8B57; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)


# Função Loader (Segura)
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=3)
        return r.json() if r.status_code == 200 else None
    except:
        return None


init_db()

# --- ESTADOS ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'logout_anim' not in st.session_state:
    st.session_state.logout_anim = False

# --- LÓGICA ---

# 1. SAÍDA (LOGOUT)
if st.session_state.logout_anim:
    anim_bye = load_lottieurl("https://lottie.host/020050df-d035-4303-8854-9725d2222238/v1G8Y2X20n.json")

    placeholder = st.empty()
    with placeholder.container():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if anim_bye:
                st_lottie(anim_bye, height=200, key="bye_anim")
            else:
                st.markdown("# 👋")
            st.markdown(
                f"<h2 style='text-align: center; color: #2E8B57;'>Até logo, {st.session_state.get('user_nome')}!</h2>",
                unsafe_allow_html=True)

    time.sleep(2.5)
    st.session_state.logged_in = False
    st.session_state.logout_anim = False
    st.rerun()

# 2. LOGIN (Se não logado)
elif not st.session_state.logged_in:
    login.render_login()

# 3. SISTEMA (Se logado)
else:
    perms = st.session_state.get('permissoes', [])
    is_admin = 'admin' in perms

    opcoes_menu = ["Início"]
    icones_menu = ["house-fill"]

    if is_admin or 'vendas' in perms: opcoes_menu.append("Vendas"); icones_menu.append("cart4")
    if is_admin or 'clientes' in perms: opcoes_menu.append("Clientes"); icones_menu.append("people-fill")
    if is_admin or 'estoque' in perms: opcoes_menu.append("Estoque"); icones_menu.append("box-seam-fill")
    if is_admin or 'financeiro' in perms: opcoes_menu.append("Financeiro"); icones_menu.append("graph-up-arrow")
    if is_admin or 'usuarios' in perms: opcoes_menu.append("Usuários"); icones_menu.append("person-badge-fill")

    with st.sidebar:
        st.markdown('<div class="sidebar-title">🌿 Cerrado Tereré 67</div>', unsafe_allow_html=True)
        st.success(f"👤 {st.session_state.get('user_nome', 'Usuário')}")

        selected = option_menu(
            menu_title=None,
            options=opcoes_menu,
            icons=icones_menu,
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#6c757d", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "5px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#2E8B57"},
            }
        )

        st.markdown("---")
        if st.button("🔒 Sair", use_container_width=True):
            st.session_state.logout_anim = True
            st.rerun()

    if selected == "Início":
        home.render_home()
    elif selected == "Vendas" and (is_admin or 'vendas' in perms):
        vendas.render_vendas()
    elif selected == "Clientes" and (is_admin or 'clientes' in perms):
        clientes.render_clientes()
    elif selected == "Estoque" and (is_admin or 'estoque' in perms):
        estoque.render_estoque()
    elif selected == "Financeiro" and (is_admin or 'financeiro' in perms):
        financeiro.render_financeiro()
    elif selected == "Usuários" and (is_admin or 'usuarios' in perms):
        usuarios.render_usuarios()