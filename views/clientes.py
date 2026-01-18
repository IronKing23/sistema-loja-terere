# views/clientes.py
import streamlit as st
import pandas as pd
from database import run_query
from fpdf import FPDF
import base64
from datetime import date
import time


# --- 1. FUNÇÃO GERAR RELATÓRIO PDF (Mantida igual) ---
def gerar_relatorio_cliente(dados_cliente, df_vendas, tipo_relatorio="Geral"):
    pdf = FPDF()
    pdf.add_page()

    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    titulo = "HISTÓRICO DE COMPRAS" if tipo_relatorio == "Geral" else "RELATÓRIO DE DÍVIDAS EM ABERTO"
    pdf.cell(190, 10, txt=titulo, ln=True, align='C')
    pdf.ln(5)

    # Dados do Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt=f"Cliente: {dados_cliente['Nome']}", ln=True)

    pdf.set_font("Arial", size=10)
    pdf.cell(95, 6, txt=f"CPF: {dados_cliente['CPF']}", ln=False)
    pdf.cell(95, 6, txt=f"Telefone: {dados_cliente['Telefone']}", ln=True)
    pdf.cell(190, 6, txt=f"Endereço: {dados_cliente['Endereço']}", ln=True)
    pdf.cell(190, 6, txt=f"Data Emissão: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)

    # Tabela
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(240, 240, 240)

    pdf.cell(25, 8, "Data", 1, 0, 'C', True)
    pdf.cell(80, 8, "Produto", 1, 0, 'L', True)
    pdf.cell(25, 8, "Total", 1, 0, 'R', True)
    pdf.cell(25, 8, "Pago", 1, 0, 'R', True)
    pdf.cell(35, 8, "Saldo Devido", 1, 1, 'R', True)

    pdf.set_font("Arial", size=9)

    total_divida_relatorio = 0
    total_comprado_relatorio = 0

    for index, row in df_vendas.iterrows():
        saldo = row['Total'] - row['Pago']
        if tipo_relatorio == "Dividas" and saldo < 0.01:
            continue

        data_fmt = pd.to_datetime(row['Data Venda']).strftime('%d/%m/%Y')
        produto = row['Produto'][:35]

        pdf.cell(25, 7, data_fmt, 1, 0, 'C')
        pdf.cell(80, 7, produto, 1, 0, 'L')
        pdf.cell(25, 7, f"R$ {row['Total']:.2f}", 1, 0, 'R')
        pdf.cell(25, 7, f"R$ {row['Pago']:.2f}", 1, 0, 'R')
        pdf.cell(35, 7, f"R$ {saldo:.2f}", 1, 1, 'R')

        total_divida_relatorio += saldo
        total_comprado_relatorio += row['Total']

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    if tipo_relatorio == "Geral":
        pdf.cell(190, 8, txt=f"TOTAL COMPRADO: R$ {total_comprado_relatorio:.2f}", ln=True, align='R')

    pdf.cell(190, 8, txt=f"TOTAL EM ABERTO: R$ {total_divida_relatorio:.2f}", ln=True, align='R')

    return pdf.output(dest='S').encode('latin-1', 'replace')


# --- Helper para Botão de Download Estilizado ---
def criar_botao_download(pdf_bytes, nome_arquivo, label):
    b64 = base64.b64encode(pdf_bytes).decode()
    style_btn = """
        text-decoration: none; display: flex; justify-content: center; align-items: center; 
        height: 100%; width: 100%; border: 1px solid rgba(49, 51, 63, 0.2); 
        background-color: white; color: rgb(49, 51, 63); padding: 0.25rem 0.75rem; 
        border-radius: 0.5rem; font-family: 'Source Sans Pro', sans-serif; font-size: 14px;
    """
    return f'<div style="height: 40px; display: flex; align-items: center; margin-bottom: 5px;"><a href="data:application/octet-stream;base64,{b64}" download="{nome_arquivo}.pdf" style="{style_btn}">📄 {label}</a></div>'


# --- 2. RENDERIZAÇÃO DA TELA ---
def render_clientes():
    # Inicializa estado de navegação
    if 'tela_clientes' not in st.session_state:
        st.session_state.tela_clientes = 'menu'

    # =======================================================
    # TELA 1: MENU DASHBOARD (Visão Geral)
    # =======================================================
    if st.session_state.tela_clientes == 'menu':
        st.header("👥 Gestão de Clientes")

        # Recupera total de clientes para mostrar KPI
        total_cli = run_query("SELECT COUNT(*) FROM clientes", fetch=True)[0][0]

        st.markdown("---")

        c_spacer1, c_main, c_spacer2 = st.columns([1, 2, 1])
        with c_main:
            # KPI Rápido
            st.caption(f"Total de Clientes Cadastrados: {total_cli}")

            with st.container(border=True):
                st.markdown("### 🔍 Consultar e Gerenciar")
                st.write("Pesquise fichas, veja histórico e edite dados.")
                if st.button("ACESSAR CARTEIRA", type="primary", use_container_width=True):
                    st.session_state.tela_clientes = 'consultar'
                    st.rerun()

            st.write("")

            with st.container(border=True):
                st.markdown("### ➕ Novo Cadastro")
                st.write("Adicione um novo cliente ao sistema.")
                if st.button("CADASTRAR NOVO", use_container_width=True):
                    st.session_state.tela_clientes = 'novo'
                    st.rerun()

    # =======================================================
    # TELA 2: CONSULTAR E GERENCIAR (Ficha Completa)
    # =======================================================
    elif st.session_state.tela_clientes == 'consultar':
        # Header com Voltar
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("⬅️ Voltar"):
                st.session_state.tela_clientes = 'menu'
                st.rerun()
        with c_tit:
            st.subheader("Carteira de Clientes")

        clientes_db = run_query("SELECT id, nome, telefone, cpf, endereco FROM clientes", fetch=True)

        if clientes_db:
            df_clientes = pd.DataFrame(clientes_db, columns=["ID", "Nome", "Telefone", "CPF", "Endereço"])

            # --- BARRA DE PESQUISA ---
            with st.container(border=True):
                col_search1, col_search2 = st.columns([3, 1])
                with col_search1:
                    termo_busca = st.text_input("Buscar Cliente:", placeholder="Digite o nome...",
                                                label_visibility="collapsed")

                if termo_busca:
                    df_filtrado = df_clientes[df_clientes['Nome'].str.contains(termo_busca, case=False, na=False)]
                else:
                    df_filtrado = df_clientes

                lista_nomes = df_filtrado['Nome'].tolist()

                if not lista_nomes:
                    st.warning("Nenhum cliente encontrado.")
                    cliente_selecionado = None
                else:
                    cliente_selecionado = st.selectbox("Selecione para ver a ficha:", lista_nomes)

            # --- FICHA DO CLIENTE ---
            if cliente_selecionado:
                dados_cli = df_filtrado[df_filtrado['Nome'] == cliente_selecionado].iloc[0]

                st.write("")  # Espaço

                c_left, c_right = st.columns([1, 2])

                # --- COLUNA ESQUERDA: DADOS PESSOAIS ---
                with c_left:
                    with st.container(border=True):
                        st.markdown("#### 👤 Perfil")
                        st.markdown(f"**{dados_cli['Nome']}**")
                        st.caption(f"CPF: {dados_cli['CPF']}")
                        st.caption(f"Tel: {dados_cli['Telefone']}")
                        st.info(f"📍 {dados_cli['Endereço']}")

                        # Botões de Documentos
                        st.markdown("---")
                        st.markdown("**Documentos**")

                        vendas_db = run_query(
                            "SELECT id, produto_nome, total, valor_pago, data_venda, status FROM vendas WHERE cliente_nome = ?",
                            (cliente_selecionado,), fetch=True)
                        if vendas_db:
                            df_hist = pd.DataFrame(vendas_db,
                                                   columns=["ID", "Produto", "Total", "Pago", "Data Venda", "Status"])

                            # Botão Histórico Completo
                            pdf_completo = gerar_relatorio_cliente(dados_cli, df_hist, "Geral")
                            html_btn1 = criar_botao_download(pdf_completo, f"Historico_{cliente_selecionado}",
                                                             "Histórico Completo")
                            st.markdown(html_btn1, unsafe_allow_html=True)

                            # Botão Dívidas
                            dividas = df_hist[(df_hist['Total'] - df_hist['Pago']) > 0.01]
                            if not dividas.empty:
                                pdf_dividas = gerar_relatorio_cliente(dados_cli, df_hist, "Dividas")
                                html_btn2 = criar_botao_download(pdf_dividas, f"Dividas_{cliente_selecionado}",
                                                                 "Relatório de Dívidas")
                                st.markdown(html_btn2, unsafe_allow_html=True)
                            else:
                                st.success("Nada em aberto! ✅")
                        else:
                            st.caption("Sem histórico de compras.")

                    # Módulo de Edição (Expander)
                    with st.expander("✏️ Editar Cadastro"):
                        with st.form("form_edicao_cliente"):
                            novo_nome = st.text_input("Nome", value=dados_cli['Nome'])
                            novo_tel = st.text_input("Telefone", value=dados_cli['Telefone'])
                            novo_cpf = st.text_input("CPF", value=dados_cli['CPF'])
                            novo_end = st.text_area("Endereço", value=dados_cli['Endereço'])

                            if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                                run_query("UPDATE clientes SET nome=?, telefone=?, cpf=?, endereco=? WHERE id=?",
                                          (novo_nome, novo_tel, novo_cpf, novo_end, int(dados_cli['ID'])))
                                if novo_nome != dados_cli['Nome']:
                                    run_query("UPDATE vendas SET cliente_nome=? WHERE cliente_nome=?",
                                              (novo_nome, dados_cli['Nome']))
                                st.toast("Cadastro atualizado!", icon="✅")
                                time.sleep(1)
                                st.rerun()

                # --- COLUNA DIREITA: FINANCEIRO ---
                with c_right:
                    with st.container(border=True):
                        st.markdown("#### 📊 Score Financeiro")

                        if vendas_db:
                            total_comprado = df_hist['Total'].sum()
                            total_pago = df_hist['Pago'].sum()
                            saldo_devedor = total_comprado - total_pago

                            m1, m2, m3 = st.columns(3)
                            m1.metric("Total Gasto", f"R$ {total_comprado:.2f}")
                            m2.metric("Total Pago", f"R$ {total_pago:.2f}")
                            m3.metric("Em Aberto", f"R$ {saldo_devedor:.2f}", delta_color="inverse")

                            st.divider()
                            st.markdown("**📜 Últimas Movimentações**")

                            df_show = df_hist.copy()
                            df_show['Saldo'] = df_show['Total'] - df_show['Pago']
                            df_show['Data Venda'] = pd.to_datetime(df_show['Data Venda']).dt.strftime('%d/%m/%Y')

                            st.dataframe(
                                df_show[['Data Venda', 'Produto', 'Total', 'Pago', 'Saldo', 'Status']],
                                use_container_width=True,
                                hide_index=True,
                                height=300
                            )
                        else:
                            st.info("Este cliente ainda não realizou compras na loja.")

        else:
            st.info("Nenhum cliente cadastrado no sistema.")

    # =======================================================
    # TELA 3: NOVO CADASTRO
    # =======================================================
    elif st.session_state.tela_clientes == 'novo':
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("⬅️ Voltar"):
                st.session_state.tela_clientes = 'menu'
                st.rerun()
        with c_tit:
            st.subheader("Novo Cadastro")

        with st.container(border=True):
            with st.form("form_cliente", clear_on_submit=True):
                st.markdown("#### Dados do Cliente")
                nome = st.text_input("Nome Completo *")

                c1, c2 = st.columns(2)
                with c1:
                    telefone = st.text_input("Telefone / WhatsApp")
                with c2:
                    cpf = st.text_input("CPF (Opcional)")

                endereco = st.text_area("Endereço Completo")

                st.write("")
                if st.form_submit_button("✅ CADASTRAR CLIENTE", type="primary", use_container_width=True):
                    if not nome:
                        st.error("O campo Nome é obrigatório!")
                    else:
                        run_query("INSERT INTO clientes (nome, telefone, cpf, endereco) VALUES (?, ?, ?, ?)",
                                  (nome, telefone, cpf, endereco))
                        st.balloons()
                        st.toast(f"Cliente {nome} cadastrado com sucesso!", icon="👤")
                        time.sleep(1.5)
                        st.session_state.tela_clientes = 'menu'  # Volta pro menu
                        st.rerun()