# views/estoque.py
import streamlit as st
import pandas as pd
from database import run_query
import time


def render_estoque():
    # Inicializa estado de navegação
    if 'tela_estoque' not in st.session_state:
        st.session_state.tela_estoque = 'menu'

    # --- 1. CARREGAMENTO DE DADOS (Global) ---
    # Buscamos os dados aqui para alimentar tanto os KPIs do Menu quanto a Tabela de Visualização
    dados = run_query("SELECT id, nome, preco, quantidade, minimo_alerta FROM produtos", fetch=True)
    df_produtos = pd.DataFrame(dados,
                               columns=["ID", "Nome", "Preço", "Qtd", "Alerta Mínimo"]) if dados else pd.DataFrame()

    # =======================================================
    # TELA 1: MENU DASHBOARD (Visão Geral)
    # =======================================================
    if st.session_state.tela_estoque == 'menu':
        st.header("📦 Gerenciamento de Estoque")

        # --- CÁLCULO DE KPIS ---
        if not df_produtos.empty:
            total_itens = len(df_produtos)
            # Valor do Estoque = Soma de (Preço * Quantidade) de cada item
            valor_estoque = (df_produtos['Preço'] * df_produtos['Qtd']).sum()
            # Itens abaixo do mínimo
            alertas = len(df_produtos[df_produtos['Qtd'] <= df_produtos['Alerta Mínimo']])
        else:
            total_itens = 0
            valor_estoque = 0.0
            alertas = 0

        st.markdown("---")

        # --- CARTÕES DE MÉTRICAS ---
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("📦 Total de Produtos", f"{total_itens}")
            c2.metric("💰 Valor em Estoque", f"R$ {valor_estoque:.2f}")
            c3.metric("🚨 Alertas de Reposição", f"{alertas}", delta_color="inverse")

        st.write("")  # Espaço

        # --- BOTÕES DE AÇÃO ---
        c_main, c_new = st.columns([2, 1])

        with c_main:
            with st.container(border=True):
                st.markdown("### 🔍 Consultar e Editar")
                st.write("Visualize o inventário, filtre produtos e ajuste preços ou quantidades.")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("VER TABELA COMPLETA", use_container_width=True):
                        st.session_state.tela_estoque = 'visualizar'
                        st.rerun()
                with col_btn2:
                    if st.button("✏️ EDITAR ITEM", use_container_width=True):
                        st.session_state.tela_estoque = 'editar'
                        st.rerun()

        with c_new:
            with st.container(border=True):
                st.markdown("### ➕ Cadastro")
                st.write("Novo item.")
                st.write("")  # Espaço para alinhar botões
                if st.button("ADICIONAR PRODUTO", type="primary", use_container_width=True):
                    st.session_state.tela_estoque = 'novo'
                    st.rerun()

    # =======================================================
    # TELA 2: VISUALIZAR ESTOQUE (Tabela)
    # =======================================================
    elif st.session_state.tela_estoque == 'visualizar':
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("⬅️ Voltar"):
                st.session_state.tela_estoque = 'menu'
                st.rerun()
        with c_tit:
            st.subheader("Visão Geral do Inventário")

        if not df_produtos.empty:
            # Barra de Filtros
            with st.container(border=True):
                col_search, col_filter = st.columns([3, 1])
                with col_search:
                    busca = st.text_input("Buscar Produto:", placeholder="Digite o nome...",
                                          label_visibility="collapsed")
                with col_filter:
                    filtro_alerta = st.checkbox("Apenas Estoque Baixo")

            # Aplica Filtros
            df_show = df_produtos.copy()
            if busca:
                df_show = df_show[df_show['Nome'].str.contains(busca, case=False)]

            if filtro_alerta:
                df_show = df_show[df_show['Qtd'] <= df_show['Alerta Mínimo']]

            # Feedback Visual de Alertas
            estoque_baixo = df_show[df_show['Qtd'] <= df_show['Alerta Mínimo']]
            if not estoque_baixo.empty:
                st.warning(f"⚠️ Atenção: {len(estoque_baixo)} itens precisam de reposição!")

            # Tabela
            st.dataframe(
                df_show,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Preço": st.column_config.NumberColumn("Preço (R$)", format="R$ %.2f"),
                    "Qtd": st.column_config.NumberColumn("Quantidade"),
                    "Alerta Mínimo": st.column_config.NumberColumn("Mínimo")
                }
            )
        else:
            st.info("Nenhum produto cadastrado.")

    # =======================================================
    # TELA 3: NOVO CADASTRO
    # =======================================================
    elif st.session_state.tela_estoque == 'novo':
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("⬅️ Voltar"):
                st.session_state.tela_estoque = 'menu'
                st.rerun()
        with c_tit:
            st.subheader("Cadastro de Produto")

        with st.container(border=True):
            # clear_on_submit ajuda se o usuário quiser cadastrar vários seguidos sem sair da tela
            with st.form("form_cadastro", clear_on_submit=True):
                st.markdown("#### Dados do Produto")
                nome = st.text_input("Nome do Produto *")

                c1, c2 = st.columns(2)
                with c1:
                    preco = st.number_input("Preço de Venda (R$)", min_value=0.01, format="%.2f")
                with c2:
                    qtd = st.number_input("Quantidade Inicial", min_value=0, step=1)

                alerta = st.number_input("Avisar quando estoque for menor que:", value=5)

                st.write("")
                if st.form_submit_button("✅ SALVAR PRODUTO", type="primary", use_container_width=True):
                    if not nome:
                        st.error("O nome do produto é obrigatório!")
                    else:
                        run_query(
                            "INSERT INTO produtos (nome, preco, quantidade, minimo_alerta) VALUES (?, ?, ?, ?)",
                            (nome, preco, qtd, alerta)
                        )
                        st.toast(f"Produto '{nome}' cadastrado!", icon="📦")
                        time.sleep(1)
                        # Aqui optamos por NÃO voltar ao menu automaticamente para permitir cadastros em série.
                        # Se preferir voltar, descomente as linhas abaixo:
                        # st.session_state.tela_estoque = 'menu'
                        # st.rerun()

    # =======================================================
    # TELA 4: EDITAR PRODUTO
    # =======================================================
    elif st.session_state.tela_estoque == 'editar':
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("⬅️ Voltar"):
                st.session_state.tela_estoque = 'menu'
                st.rerun()
        with c_tit:
            st.subheader("Editar Produto")

        if not df_produtos.empty:
            with st.container(border=True):
                # Seletor de Busca
                lista_prods = df_produtos['Nome'].tolist()
                prod_selecionado = st.selectbox("Selecione o produto para editar:", lista_prods)

                # Pega dados atuais
                dados_atuais = df_produtos[df_produtos['Nome'] == prod_selecionado].iloc[0]
                id_sel = int(dados_atuais['ID'])

                st.divider()

                # Formulário de Edição
                with st.form("form_edicao"):
                    st.markdown(f"Editando: **{dados_atuais['Nome']}**")

                    novo_nome = st.text_input("Nome", value=dados_atuais['Nome'])

                    c1, c2 = st.columns(2)
                    with c1:
                        novo_preco = st.number_input("Preço (R$)", min_value=0.01, value=float(dados_atuais['Preço']),
                                                     format="%.2f")
                    with c2:
                        nova_qtd = st.number_input("Quantidade", min_value=0, value=int(dados_atuais['Qtd']), step=1)

                    novo_alerta = st.number_input("Alerta Mínimo", value=int(dados_atuais['Alerta Mínimo']))

                    if st.form_submit_button("💾 ATUALIZAR DADOS", use_container_width=True):
                        run_query(
                            "UPDATE produtos SET nome=?, preco=?, quantidade=?, minimo_alerta=? WHERE id=?",
                            (novo_nome, novo_preco, nova_qtd, novo_alerta, id_sel)
                        )
                        st.success("Produto atualizado com sucesso!")
                        time.sleep(1)
                        st.session_state.tela_estoque = 'menu'  # Volta pro menu após editar
                        st.rerun()
        else:
            st.warning("Nenhum produto para editar.")