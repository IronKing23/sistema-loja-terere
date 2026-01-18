# views/home.py
import streamlit as st
import pandas as pd
from database import run_query
from datetime import date, timedelta
import plotly.express as px  # (Opcional, mas vamos usar st.bar_chart nativo para simplicidade e rapidez)


def render_home():
    st.header("🏠 Painel de Controle")
    st.write(f"Resumo do dia: **{date.today().strftime('%d/%m/%Y')}**")

    # --- 1. BUSCA DE DADOS (QUERIES) ---
    # A. Vendas de Hoje
    dados_hoje = run_query("SELECT SUM(total), COUNT(*) FROM vendas WHERE data_venda = ?", (date.today(),), fetch=True)
    total_hoje = dados_hoje[0][0] if dados_hoje[0][0] else 0.0
    qtd_vendas_hoje = dados_hoje[0][1]

    # B. Contas a Receber (Geral)
    # Calculamos somando (Total - Valor Pago) apenas das Pendentes
    dados_receber = run_query("SELECT SUM(total - valor_pago) FROM vendas WHERE status = 'Pendente'", fetch=True)
    total_receber = dados_receber[0][0] if dados_receber and dados_receber[0][0] else 0.0

    # C. Alertas de Estoque
    # Conta quantos produtos têm quantidade <= minimo_alerta
    dados_estoque = run_query("SELECT COUNT(*) FROM produtos WHERE quantidade <= minimo_alerta", fetch=True)
    qtd_alertas = dados_estoque[0][0]

    # --- 2. CARTÕES DE KPI (INDICADORES) ---
    with st.container(border=True):
        st.markdown("##### 📊 Indicadores Principais")
        k1, k2, k3, k4 = st.columns(4)

        k1.metric("Vendas Hoje (R$)", f"R$ {total_hoje:.2f}", help="Total vendido hoje (faturado)")
        k2.metric("Pedidos Hoje", f"{qtd_vendas_hoje}", help="Quantidade de vendas realizadas hoje")
        k3.metric("A Receber", f"R$ {total_receber:.2f}", delta="Pendências", delta_color="inverse",
                  help="Total que clientes te devem")
        k4.metric("Estoque Baixo", f"{qtd_alertas} itens", delta="Reposição", delta_color="inverse",
                  help="Itens abaixo do mínimo")

    # --- 3. GRÁFICO E TABELA RECENTE ---
    col_chart, col_recent = st.columns([1.5, 1])

    with col_chart:
        with st.container(border=True):
            st.markdown("##### 📈 Vendas: Últimos 7 Dias")

            # Query para os últimos 7 dias
            data_inicio = date.today() - timedelta(days=6)
            query_chart = """
                SELECT data_venda, SUM(total) as total_dia 
                FROM vendas 
                WHERE data_venda >= ? 
                GROUP BY data_venda 
                ORDER BY data_venda ASC
            """
            dados_chart = run_query(query_chart, (data_inicio,), fetch=True)

            if dados_chart:
                df_chart = pd.DataFrame(dados_chart, columns=["Data", "Total"])
                df_chart['Data'] = pd.to_datetime(df_chart['Data']).dt.strftime('%d/%m')
                df_chart.set_index("Data", inplace=True)

                st.bar_chart(df_chart, color="#FF4B4B", height=250)
            else:
                st.info("Sem dados suficientes para o gráfico.")

    with col_recent:
        with st.container(border=True):
            st.markdown("##### ⏱️ Últimas 5 Vendas")

            recentes = run_query("SELECT cliente_nome, total, status FROM vendas ORDER BY id DESC LIMIT 5", fetch=True)
            if recentes:
                df_recentes = pd.DataFrame(recentes, columns=["Cliente", "Valor", "Status"])
                st.dataframe(
                    df_recentes,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Valor": st.column_config.NumberColumn(format="R$ %.2f")
                    }
                )
            else:
                st.caption("Nenhuma venda recente.")

            if st.button("Ver Histórico Completo", use_container_width=True):
                # Truque: Apenas avisa para usar o menu lateral,
                # pois mudar a página programaticamente no streamlit-option-menu exige session_state complexo
                st.info("Acesse o menu 'Vendas' na barra lateral.")