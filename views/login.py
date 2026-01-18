# views/login.py
import streamlit as st
import time
import requests
from database import get_user_data, check_hashes, update_user_password

# Tenta importar Lottie, se não tiver, usa fallback
try:
    from streamlit_lottie import st_lottie

    HAS_LOTTIE = True
except ImportError:
    HAS_LOTTIE = False


# --- FUNÇÃO SEGURA PARA CARREGAR ANIMAÇÃO ---
@st.cache_data(show_spinner=False)
def load_lottieurl(url):
    if not HAS_LOTTIE:
        return None
    try:
        # Timeout ultra-rápido (1s) para não travar a tela
        r = requests.get(url, timeout=1)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


def render_login():
    # Tenta carregar
    anim_login = load_lottieurl("https://lottie.host/6e64d7c0-671e-450b-8d5c-912dfa88785e/3u1s4Xz6tB.json")
    anim_success = load_lottieurl("https://lottie.host/939b4b0e-6169-4508-b785-52d3a0429188/8p7X5Zq7tB.json")

    # Placeholder principal
    login_area = st.empty()

    # --- RENDERIZAÇÃO DO FORMULÁRIO ---
    with login_area.container():
        # Centralização usando colunas
        c_esq, c_centro, c_dir = st.columns([1, 4, 1])  # Coluna do meio mais larga

        with c_centro:
            st.markdown("<br>", unsafe_allow_html=True)

            # --- ÁREA DO LOGIN (Card com Borda) ---
            with st.container(border=True):
                # Se a animação carregou, mostra pequena no topo. Se não, mostra emoji.
                col_logo, col_texto = st.columns([1, 2])
                with col_logo:
                    if anim_login and HAS_LOTTIE:
                        st_lottie(anim_login, height=100, key="logo_anim")
                    else:
                        st.markdown("# 🌿")

                with col_texto:
                    st.markdown("## Cerrado Tereré 67")
                    st.caption("Sistema de Gestão Integrado")

                st.divider()

                # --- CAMPOS DE LOGIN ---
                if 'temp_user_valid' not in st.session_state:
                    usuario = st.text_input("Usuário", placeholder="Digite seu login")
                    senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")

                    st.write("")
                    if st.button("🔓 ACESSAR SISTEMA", type="primary", use_container_width=True):
                        if not usuario or not senha:
                            st.warning("Preencha usuário e senha.")
                        else:
                            user_data = get_user_data(usuario)

                            if user_data:
                                stored_password, nome_real, permissoes, mudar_senha = user_data[0]
                                if check_hashes(senha, stored_password):
                                    if mudar_senha == 1:
                                        st.session_state.temp_user_valid = usuario
                                        st.warning("🔒 Troca de senha obrigatória.")
                                        st.rerun()
                                    else:
                                        # === ANIMAÇÃO DE SUCESSO ===
                                        login_area.empty()  # Limpa a tela

                                        with login_area.container():
                                            st.markdown("<br><br><br>", unsafe_allow_html=True)
                                            c1, c2, c3 = st.columns([1, 2, 1])
                                            with c2:
                                                if anim_success and HAS_LOTTIE:
                                                    st_lottie(anim_success, height=200, key="win_anim")
                                                else:
                                                    st.markdown("# 🎉")

                                                st.markdown(
                                                    f"<h1 style='text-align: center; color: #2E8B57;'>Bem-vindo!</h1>",
                                                    unsafe_allow_html=True)
                                                st.markdown(f"<h3 style='text-align: center;'>{nome_real}</h3>",
                                                            unsafe_allow_html=True)

                                        # Define sessão
                                        st.session_state.logged_in = True
                                        st.session_state.username = usuario
                                        st.session_state.user_nome = nome_real
                                        st.session_state.permissoes = permissoes.split(',') if permissoes else []

                                        time.sleep(2)
                                        st.rerun()
                                else:
                                    st.error("Senha incorreta.")
                            else:
                                st.error("Usuário não encontrado.")

                # --- TELA DE NOVA SENHA ---
                else:
                    st.warning("⚠️ Defina sua Senha Pessoal")
                    nova_senha = st.text_input("Nova Senha", type="password")
                    confirmar_senha = st.text_input("Confirmar Senha", type="password")

                    if st.button("💾 SALVAR NOVA SENHA", type="primary", use_container_width=True):
                        if nova_senha == confirmar_senha and len(nova_senha) >= 4:
                            usuario_temp = st.session_state.temp_user_valid
                            update_user_password(usuario_temp, nova_senha)

                            # Pega dados atualizados
                            user_data = get_user_data(usuario_temp)
                            stored_password, nome_real, permissoes, mudar_senha = user_data[0]

                            st.session_state.logged_in = True
                            st.session_state.username = usuario_temp
                            st.session_state.user_nome = nome_real
                            st.session_state.permissoes = permissoes.split(',') if permissoes else []
                            del st.session_state.temp_user_valid

                            st.success("Senha atualizada! Entrando...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Senhas inválidas ou muito curtas.")