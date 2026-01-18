# views/usuarios.py
import streamlit as st
import pandas as pd
from datetime import date
from database import run_query, make_hashes


def render_usuarios():
    # Verifica Permissão de Segurança (Só admin ou quem tem permissão 'usuarios')
    perms = st.session_state.get('permissoes', [])
    if 'admin' not in perms and 'usuarios' not in perms:
        st.error("⛔ Acesso Negado. Você não tem permissão para gerenciar usuários.")
        return

    st.header("👥 Gestão de Usuários e Permissões")

    tab_lista, tab_novo = st.tabs(["📋 Lista de Usuários", "➕ Novo Usuário"])

    # --- LISTA DE USUÁRIOS ---
    with tab_lista:
        dados = run_query("SELECT id, username, nome_real, permissoes, mudar_senha FROM usuarios", fetch=True)
        if dados:
            df = pd.DataFrame(dados, columns=["ID", "Login", "Nome", "Permissões", "Troca Pendente?"])
            df['Troca Pendente?'] = df['Troca Pendente?'].apply(lambda x: "Sim" if x == 1 else "Não")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Edição Rápida de Senha/Permissão
            with st.expander("✏️ Editar Usuário / Resetar Senha"):
                lista_logins = df['Login'].tolist()
                user_sel = st.selectbox("Selecione o Usuário:", lista_logins)

                # Pega dados atuais
                info_atual = df[df['Login'] == user_sel].iloc[0]
                perms_atuais = info_atual['Permissões'].split(',') if info_atual['Permissões'] else []

                st.markdown(f"**Editando: {info_atual['Nome']}**")

                c1, c2 = st.columns(2)
                with c1:
                    novo_nome = st.text_input("Nome Completo", value=info_atual['Nome'])
                    resetar = st.checkbox("Resetar Senha para padrão?")
                    if resetar:
                        senha_padrao = date.today().strftime('%Y%m%d')
                        st.caption(f"A senha será: **{senha_padrao}** e pedirá troca no login.")

                with c2:
                    st.write("Acesso às Telas:")
                    p_vendas = st.checkbox("Vendas", value='vendas' in perms_atuais or 'admin' in perms_atuais)
                    p_clientes = st.checkbox("Clientes", value='clientes' in perms_atuais or 'admin' in perms_atuais)
                    p_estoque = st.checkbox("Estoque", value='estoque' in perms_atuais or 'admin' in perms_atuais)
                    p_fin = st.checkbox("Financeiro", value='financeiro' in perms_atuais or 'admin' in perms_atuais)
                    p_users = st.checkbox("Gestão Usuários",
                                          value='usuarios' in perms_atuais or 'admin' in perms_atuais)

                if st.button("💾 Salvar Alterações"):
                    # Monta string de permissões
                    lista_p = []
                    if p_vendas: lista_p.append('vendas')
                    if p_clientes: lista_p.append('clientes')
                    if p_estoque: lista_p.append('estoque')
                    if p_fin: lista_p.append('financeiro')
                    if p_users: lista_p.append('usuarios')
                    str_perms = ",".join(lista_p)

                    query = "UPDATE usuarios SET nome_real = ?, permissoes = ? WHERE username = ?"
                    params = [novo_nome, str_perms, user_sel]

                    if resetar:
                        nova_hash = make_hashes(senha_padrao)
                        query = "UPDATE usuarios SET nome_real = ?, permissoes = ?, password = ?, mudar_senha = 1 WHERE username = ?"
                        params = [novo_nome, str_perms, nova_hash, user_sel]

                    run_query(query, tuple(params))
                    st.success("Usuário atualizado!")
                    st.rerun()

    # --- NOVO USUÁRIO ---
    with tab_novo:
        st.subheader("Cadastro de Colaborador")
        with st.form("novo_user", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome_real = st.text_input("Nome do Colaborador *")
                login_user = st.text_input("Login (Username) *", help="Usado para entrar no sistema")

            with col2:
                # Senha Automática
                senha_auto = date.today().strftime('%Y%m%d')
                st.markdown(f"**Senha Inicial Automática:** `{senha_auto}`")
                st.caption("O usuário será obrigado a mudar esta senha no primeiro acesso.")

            st.markdown("---")
            st.markdown("#### 🔐 Permissões de Acesso")

            cp1, cp2, cp3, cp4, cp5 = st.columns(5)
            chk_vendas = cp1.checkbox("Vendas", value=True)
            chk_clientes = cp2.checkbox("Clientes", value=True)
            chk_estoque = cp3.checkbox("Estoque")
            chk_fin = cp4.checkbox("Financeiro")
            chk_users = cp5.checkbox("Gestão Usuários")

            if st.form_submit_button("✅ Criar Usuário"):
                if not nome_real or not login_user:
                    st.error("Preencha nome e login.")
                else:
                    # Verifica se login já existe
                    existe = run_query("SELECT id FROM usuarios WHERE username = ?", (login_user,), fetch=True)
                    if existe:
                        st.error("Este login já está em uso!")
                    else:
                        lista_p = []
                        if chk_vendas: lista_p.append('vendas')
                        if chk_clientes: lista_p.append('clientes')
                        if chk_estoque: lista_p.append('estoque')
                        if chk_fin: lista_p.append('financeiro')
                        if chk_users: lista_p.append('usuarios')
                        str_perms = ",".join(lista_p)

                        senha_hash = make_hashes(senha_auto)

                        run_query(
                            "INSERT INTO usuarios (username, password, nome_real, permissoes, mudar_senha) VALUES (?, ?, ?, ?, 1)",
                            (login_user, senha_hash, nome_real, str_perms)
                        )
                        st.success(f"Usuário {nome_real} criado com sucesso!")
                        st.rerun()