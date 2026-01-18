# views/financeiro.py
import streamlit as st
import pandas as pd
from datetime import date
from database import run_query
import time


def render_financeiro():
    # Inicializa estado de navegação
    if 'tela_fin' not in st.session_state:
        st.session_state.tela_fin = 'menu'

    # --- 1. CARREGAMENTO DE DADOS (Global para todas as telas) ---
    dados_vendas = run_query(
        "SELECT id, produto_nome, cliente_nome, total, valor_pago, tipo_pagamento, data_venda, data_recebimento, status FROM vendas",
        fetch=True)
    df_vendas = pd.DataFrame(dados_vendas,
                             columns=["ID", "Produto", "Cliente", "Total", "Pago", "Tipo", "Data Venda", "Vencimento",
                                      "Status"]) if dados_vendas else pd.DataFrame()

    dados_mov = run_query("SELECT id, data, tipo, descricao, valor FROM caixa_movimentos", fetch=True)
    df_mov = pd.DataFrame(dados_mov,
                          columns=["ID", "Data", "Tipo", "Descricao", "Valor"]) if dados_mov else pd.DataFrame()

    # --- 2. CÁLCULOS DE SALDO (KPIs) ---
    if not df_vendas.empty:
        df_vendas['Falta Pagar'] = df_vendas['Total'] - df_vendas['Pago']
        receita_vendas = df_vendas['Pago'].sum()
        # Filtro de segurança (> 0.001)
        total_a_receber = df_vendas[(df_vendas['Status'] == 'Pendente') & (df_vendas['Falta Pagar'] > 0.001)][
            'Falta Pagar'].sum()
    else:
        receita_vendas = 0.0
        total_a_receber = 0.0

    if not df_mov.empty:
        total_sup = df_mov[df_mov['Tipo'] == 'Entrada']['Valor'].sum()
        total_san = df_mov[df_mov['Tipo'] == 'Saida']['Valor'].sum()
    else:
        total_sup = 0.0
        total_san = 0.0

    saldo_atual = (receita_vendas + total_sup) - total_san

    # =======================================================
    # TELA 1: MENU DASHBOARD (Visão Geral)
    # =======================================================
    if st.session_state.tela_fin == 'menu':
        st.header("💰 Painel Financeiro")

        # --- CARTÕES DE MÉTRICAS (KPIs) ---
        with st.container(border=True):
            st.markdown("##### 📊 Resumo do Caixa")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💵 Saldo Disponível", f"R$ {saldo_atual:.2f}", help="Dinheiro físico na gaveta")
            c2.metric("📉 Sangrias/Saídas", f"R$ {total_san:.2f}", delta_color="inverse")
            c3.metric("📈 Receita Vendas", f"R$ {receita_vendas:.2f}")
            c4.metric("⏳ A Receber (Fiado)", f"R$ {total_a_receber:.2f}", delta="Pendente")

        st.write("")  # Espaço

        # --- NAVEGAÇÃO ---
        st.markdown("##### 🚀 Ações Rápidas")

        # DESTAQUE: Contas a Receber (Linha inteira ou destaque visual)
        with st.container(border=True):
            col_icon, col_info, col_btn = st.columns([1, 4, 2])
            with col_icon:
                st.markdown("# 📋")
            with col_info:
                st.markdown("### Contas a Receber")
                st.write("Gerenciar clientes devedores e dar baixa em pagamentos.")
            with col_btn:
                st.write("")  # Alinhamento vertical
                if st.button("ABRIR COBRANÇAS", type="primary", use_container_width=True):
                    st.session_state.tela_fin = 'receber'
                    st.rerun()

        # OUTRAS AÇÕES: Caixa e Extrato (Lado a lado)
        c_caixa, c_extrato = st.columns(2)

        with c_caixa:
            with st.container(border=True):
                st.markdown("### ⚡ Movimentar Caixa")
                st.write("Registrar Sangrias (Retiradas) ou Suprimentos (Entradas).")
                if st.button("ABRIR CAIXA", use_container_width=True):
                    st.session_state.tela_fin = 'caixa'
                    st.rerun()

        with c_extrato:
            with st.container(border=True):
                st.markdown("### 📜 Extrato Completo")
                st.write("Visualize o histórico detalhado de todas as movimentações.")
                if st.button("VER EXTRATO", use_container_width=True):
                    st.session_state.tela_fin = 'extrato'
                    st.rerun()

    # =======================================================
    # TELA 2: CONTAS A RECEBER (Baixa Inteligente)
    # =======================================================
    elif st.session_state.tela_fin == 'receber':
        # Header com Voltar
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("⬅️ Voltar"):
                st.session_state.tela_fin = 'menu'
                st.rerun()
        with c_tit:
            st.subheader("Contas a Receber (Baixa)")

        if not df_vendas.empty:
            # Filtro de segurança para pendências reais
            pendentes = df_vendas[(df_vendas['Status'] == 'Pendente') & (df_vendas['Falta Pagar'] > 0.01)].copy()

            if not pendentes.empty:
                with st.container(border=True):
                    # 1. Selecionar Cliente
                    devedores = pendentes['Cliente'].unique()
                    cliente_sel = st.selectbox("Selecione o Cliente:", devedores)

                    # Filtra e Ordena
                    dividas_cli = pendentes[pendentes['Cliente'] == cliente_sel].sort_values('Vencimento')
                    total_devido = round(dividas_cli['Falta Pagar'].sum(), 2)

                    st.info(f"💰 Dívida Total de **{cliente_sel}**: **R$ {total_devido:.2f}**")

                    # Tabela detalhada
                    st.dataframe(dividas_cli[['Vencimento', 'Produto', 'Total', 'Pago', 'Falta Pagar']],
                                 use_container_width=True, hide_index=True)

                st.write("")

                # 2. Área de Pagamento
                with st.container(border=True):
                    st.markdown("#### 💸 Realizar Pagamento")

                    if total_devido <= 0.01:
                        st.success("Tudo pago!")
                    else:
                        c_pay1, c_pay2 = st.columns([1, 1])
                        with c_pay1:
                            valor_seguro = max(total_devido, 0.01)
                            valor_pagamento = st.number_input("Valor Recebido (R$)", min_value=0.01,
                                                              max_value=valor_seguro, value=valor_seguro, step=10.0)

                        with c_pay2:
                            st.write("")  # Espaço visual
                            st.write("")
                            if st.button("✅ CONFIRMAR BAIXA", type="primary", use_container_width=True):
                                valor_restante = valor_pagamento

                                # Loop FIFO
                                for index, row in dividas_cli.iterrows():
                                    if valor_restante <= 0: break

                                    divida_atual = row['Falta Pagar']

                                    if valor_restante >= divida_atual:
                                        novo_pago = row['Total']
                                        novo_status = 'Recebido'
                                        valor_usado = divida_atual
                                    else:
                                        novo_pago = row['Pago'] + valor_restante
                                        novo_status = 'Pendente'
                                        valor_usado = valor_restante

                                    run_query(
                                        "UPDATE vendas SET valor_pago = ?, status = ?, data_recebimento = ? WHERE id = ?",
                                        (novo_pago, novo_status, date.today(), row['ID']))
                                    valor_restante -= valor_usado

                                st.balloons()
                                st.toast("Pagamento registrado com sucesso!", icon="✅")
                                time.sleep(1.5)
                                st.rerun()
            else:
                st.container(border=True).success("Nenhuma conta pendente no sistema! 🎉")
        else:
            st.info("Nenhuma venda registrada.")

    # =======================================================
    # TELA 3: MOVIMENTAR CAIXA (Sangria/Suprimento)
    # =======================================================
    elif st.session_state.tela_fin == 'caixa':
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("⬅️ Voltar"):
                st.session_state.tela_fin = 'menu'
                st.rerun()
        with c_tit:
            st.subheader("Movimentação de Caixa")

        col_sup, col_san = st.columns(2)

        # Suprimento
        with col_sup:
            with st.container(border=True):
                st.markdown("### 🟢 Suprimento (Entrada)")
                st.write("Adicionar troco ou aporte.")
                with st.form("form_sup", clear_on_submit=True):
                    v_sup = st.number_input("Valor (R$)", min_value=0.01, step=10.0)
                    d_sup = st.text_input("Motivo (Ex: Troco inicial)")
                    if st.form_submit_button("Confirmar Entrada"):
                        run_query("INSERT INTO caixa_movimentos (data, tipo, descricao, valor) VALUES (?, ?, ?, ?)",
                                  (date.today(), 'Entrada', d_sup, v_sup))
                        st.toast("Suprimento realizado!", icon="✅")
                        time.sleep(1)
                        st.rerun()

        # Sangria
        with col_san:
            with st.container(border=True):
                st.markdown("### 🔴 Sangria (Saída)")
                st.write("Pagar contas ou retiradas.")
                st.info(f"Saldo atual para retirada: **R$ {saldo_atual:.2f}**")
                with st.form("form_san", clear_on_submit=True):
                    v_san = st.number_input("Valor (R$)", min_value=0.01, step=10.0)
                    d_san = st.text_input("Motivo (Ex: Conta de Luz)")
                    if st.form_submit_button("Confirmar Retirada", type="primary"):
                        if v_san > saldo_atual:
                            st.error("Saldo insuficiente!")
                        else:
                            run_query("INSERT INTO caixa_movimentos (data, tipo, descricao, valor) VALUES (?, ?, ?, ?)",
                                      (date.today(), 'Saida', d_san, v_san))
                            st.toast("Sangria realizada!", icon="💸")
                            time.sleep(1)
                            st.rerun()

    # =======================================================
    # TELA 4: EXTRATO COMPLETO
    # =======================================================
    elif st.session_state.tela_fin == 'extrato':
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("⬅️ Voltar"):
                st.session_state.tela_fin = 'menu'
                st.rerun()
        with c_tit:
            st.subheader("Extrato Financeiro Unificado")

        historico = []
        if not df_mov.empty:
            for _, row in df_mov.iterrows():
                historico.append({
                    "Data": row['Data'],
                    "Descrição": f"{row['Tipo'].upper()}: {row['Descricao']}",
                    "Valor": row['Valor'] * (-1 if row['Tipo'] == 'Saida' else 1),
                    "Ref": "Manual"
                })

        if not df_vendas.empty:
            for _, row in df_vendas.iterrows():
                if row['Pago'] > 0:
                    historico.append({
                        "Data": row['Data Venda'],
                        "Descrição": f"RECEBIMENTO: {row['Produto']} ({row['Cliente']})",
                        "Valor": row['Pago'],
                        "Ref": "Venda"
                    })

        with st.container(border=True):
            if historico:
                df_hist = pd.DataFrame(historico)
                df_hist['Data'] = pd.to_datetime(df_hist['Data'])
                df_hist = df_hist.sort_values(by='Data', ascending=False)

                # Formatação visual na tabela
                st.dataframe(
                    df_hist,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                        "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")
                    }
                )

                # Opção de Download
                csv = df_hist.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Baixar Extrato (CSV)", data=csv, file_name="extrato_financeiro.csv",
                                   mime="text/csv")
            else:
                st.info("Nenhuma movimentação registrada no período.")