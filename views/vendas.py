# views/vendas.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import run_query
from fpdf import FPDF
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time


# --- 1. FUNÇÕES AUXILIARES ---

def enviar_email_orcamento(remetente_email, remetente_senha, destinatario_email, cliente_nome, pdf_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = remetente_email
        msg['To'] = destinatario_email
        msg['Subject'] = f"Orçamento Cerrado Tereré 67 - {cliente_nome}"

        corpo = f"""
        Olá, {cliente_nome}.

        Segue em anexo o orçamento/pedido solicitado.

        Qualquer dúvida, estamos à disposição.

        Atenciosamente,
        Equipe Cerrado Tereré 67.
        """
        msg.attach(MIMEText(corpo, 'plain'))

        part = MIMEBase('application', "octet-stream")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="Orcamento_{cliente_nome}.pdf"')
        msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente_email, remetente_senha)
        server.sendmail(remetente_email, destinatario_email, msg.as_string())
        server.quit()
        return True, "✅ E-mail enviado com sucesso!"
    except Exception as e:
        return False, f"❌ Erro ao enviar: {str(e)}"


def gerar_pdf_orcamento(cliente, itens, total, condicao_pagamento, vencimento):
    pdf = FPDF()
    pdf.add_page()

    # Cabeçalho da Loja
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(46, 139, 87)  # Cor Verde (SeaGreen)
    pdf.cell(190, 10, txt="CERRADO TERERÉ 67", ln=True, align='C')

    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 0, 0)  # Preto
    pdf.cell(190, 10, txt="ORÇAMENTO / PEDIDO DE VENDA", ln=True, align='C')
    pdf.ln(5)

    # Dados Cliente
    pdf.set_font("Arial", size=12)
    pdf.cell(190, 8, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(190, 8, txt=f"Data Emissão: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)

    # Tabela
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(90, 8, "Produto", 1, 0, 'L', True)
    pdf.cell(20, 8, "Qtd", 1, 0, 'C', True)
    pdf.cell(35, 8, "Unitário", 1, 0, 'R', True)
    pdf.cell(45, 8, "Total", 1, 1, 'R', True)

    pdf.set_font("Arial", size=11)
    for item in itens:
        nome = item['nome'][:35]
        pdf.cell(90, 8, nome, 1)
        pdf.cell(20, 8, str(item['qtd']), 1, 0, 'C')
        pdf.cell(35, 8, f"R$ {item['preco']:.2f}", 1, 0, 'R')
        pdf.cell(45, 8, f"R$ {item['total_item']:.2f}", 1, 1, 'R')

    # Totais
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt=f"TOTAL: R$ {total:.2f}", ln=True, align='R')

    pdf.set_font("Arial", size=10)
    pdf.cell(190, 6, txt=f"Forma de Pagamento: {condicao_pagamento}", ln=True)
    if condicao_pagamento == "A Prazo":
        pdf.cell(190, 6, txt=f"Vencimento: {vencimento}", ln=True)

    # Assinatura e CPF
    pdf.ln(35)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 5, txt="Assinatura do Cliente", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 5, txt="CPF: _______._______._______-____", ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1', 'replace')


# --- 2. TELA DE VENDAS ---
def render_vendas():
    if 'tela_vendas' not in st.session_state:
        st.session_state.tela_vendas = 'menu'

    # === TELA 1: MENU ===
    if st.session_state.tela_vendas == 'menu':
        st.header("🛒 Central de Vendas")
        st.markdown("---")

        c_spacer1, c_main, c_spacer2 = st.columns([1, 2, 1])
        with c_main:
            with st.container(border=True):
                st.markdown("### 🚀 Iniciar Operação")
                st.write("Comece um novo atendimento agora.")
                if st.button("➕ NOVA VENDA", type="primary", use_container_width=True):
                    st.session_state.tela_vendas = 'nova_venda'
                    st.rerun()
            st.write("")
            with st.container(border=True):
                st.markdown("### 📂 Consultar")
                st.write("Pesquise vendas passadas e reimprima comprovantes.")
                if st.button("🔍 HISTÓRICO DE VENDAS", use_container_width=True):
                    st.session_state.tela_vendas = 'historico'
                    st.rerun()

    # === TELA 2: HISTÓRICO ===
    elif st.session_state.tela_vendas == 'historico':
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("⬅️ Voltar"):
                st.session_state.tela_vendas = 'menu'
                st.rerun()
        with c_tit:
            st.subheader("Histórico de Vendas")

        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1: data_ini = st.date_input("De:", value=date.today() - timedelta(days=30))
            with c2: data_fim = st.date_input("Até:", value=date.today())
            with c3: busca = st.text_input("Buscar (Cliente/Produto)")

        query = "SELECT data_venda, cliente_nome, produto_nome, qtd_vendida, total, status FROM vendas WHERE data_venda BETWEEN ? AND ?"
        params = [data_ini, data_fim]
        if busca:
            query += " AND (cliente_nome LIKE ? OR produto_nome LIKE ?)"
            params.extend([f"%{busca}%", f"%{busca}%"])
        query += " ORDER BY id DESC"

        dados = run_query(query, tuple(params), fetch=True)
        if dados:
            df = pd.DataFrame(dados, columns=["Data", "Cliente", "Produto", "Qtd", "Total", "Status"])
            df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%d/%m/%Y')
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma venda encontrada.")

    # === TELA 3: NOVA VENDA ===
    elif st.session_state.tela_vendas == 'nova_venda':
        c_cancel, c_head = st.columns([1, 5])
        with c_cancel:
            if st.button("❌ Cancelar"):
                st.session_state.tela_vendas = 'menu'
                st.session_state.carrinho = []
                st.rerun()
        with c_head:
            st.subheader("Nova Venda em Andamento")

        with st.sidebar.expander("⚙️ Configuração de E-mail"):
            email_loja = st.text_input("Seu E-mail (Gmail)", key="email_cfg")
            senha_app = st.text_input("Senha de App", type="password", key="senha_cfg")

        if 'carrinho' not in st.session_state:
            st.session_state.carrinho = []

        produtos = run_query("SELECT id, nome, preco, quantidade FROM produtos", fetch=True)
        clientes_db = run_query("SELECT id, nome FROM clientes", fetch=True)
        lista_clientes = [c[1] for c in clientes_db] if clientes_db else []

        # --- ADICIONAR ITEM ---
        with st.container(border=True):
            st.markdown("#### 📦 Adicionar Item")
            if not produtos:
                st.error("Sem produtos cadastrados.")
            else:
                dict_prods = {p[1]: p for p in produtos}
                c_prod, c_qtd, c_act = st.columns([3, 1, 1])
                with c_prod:
                    prod_sel = st.selectbox("Produto", list(dict_prods.keys()), label_visibility="collapsed",
                                            placeholder="Selecione...")
                    dados_prod = dict_prods[prod_sel]
                    st.caption(f"Estoque: {dados_prod[3]} | Unit: R$ {dados_prod[2]:.2f}")
                with c_qtd:
                    qtd_item = st.number_input("Qtd", min_value=1, max_value=dados_prod[3], step=1,
                                               label_visibility="collapsed")
                with c_act:
                    if st.button("Adicionar", type="secondary", use_container_width=True):
                        total_item = qtd_item * dados_prod[2]
                        st.session_state.carrinho.append(
                            {"id": dados_prod[0], "nome": dados_prod[1], "preco": dados_prod[2], "qtd": qtd_item,
                             "total_item": total_item})
                        st.rerun()

        # --- CHECKOUT ---
        if st.session_state.carrinho:
            col_cart, col_checkout = st.columns([1.5, 1])

            with col_cart:
                st.markdown("#### 🛒 Carrinho")
                df_carrinho = pd.DataFrame(st.session_state.carrinho)
                st.dataframe(df_carrinho[['nome', 'qtd', 'preco', 'total_item']], use_container_width=True,
                             hide_index=True, column_config={"nome": "Item", "qtd": "Qtd", "preco": "Unit (R$)",
                                                             "total_item": "Total (R$)"})
                if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                    st.session_state.carrinho = []
                    st.rerun()

            with col_checkout:
                with st.container(border=True):
                    total_pedido = df_carrinho['total_item'].sum()
                    st.metric("Total a Pagar", f"R$ {total_pedido:.2f}")
                    st.divider()

                    st.markdown("**Dados do Pagamento**")
                    tipo_pag = st.radio("Forma de Pagamento", ["À Vista", "A Prazo"], horizontal=True,
                                        label_visibility="collapsed")

                    cliente_final = "Consumidor Final"
                    data_venc = date.today()

                    if tipo_pag == "A Prazo":
                        cliente_final = st.selectbox("Cliente (Obrigatório)", lista_clientes)
                        dias = st.number_input("Dias Vencimento", value=30, min_value=1)
                        data_venc = date.today() + timedelta(days=dias)
                        st.caption(f"Vence em: {data_venc.strftime('%d/%m/%Y')}")
                    else:
                        if st.checkbox("Identificar Cliente?"):
                            cliente_final = st.selectbox("Cliente", lista_clientes)

                    st.divider()

                    # --- AÇÕES UNIFICADAS ---
                    st.markdown("**Documentação & Envio**")
                    email_cliente = st.text_input("E-mail do Cliente", placeholder="cliente@email.com")

                    pdf_bytes = gerar_pdf_orcamento(cliente_final, st.session_state.carrinho, total_pedido, tipo_pag,
                                                    data_venc.strftime('%d/%m/%Y'))
                    b64 = base64.b64encode(pdf_bytes).decode()

                    # CSS Botão customizado
                    style_btn = """
                        text-decoration: none; display: flex; justify-content: center; align-items: center; 
                        height: 100%; width: 100%; border: 1px solid rgba(49, 51, 63, 0.2); 
                        background-color: white; color: rgb(49, 51, 63); padding: 0.25rem 0.75rem; 
                        border-radius: 0.5rem; font-family: 'Source Sans Pro', sans-serif;
                    """

                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        st.markdown(
                            f'<div style="height: 40px; display: flex; align-items: center;"><a href="data:application/octet-stream;base64,{b64}" download="orcamento.pdf" style="{style_btn}">📄 Baixar PDF</a></div>',
                            unsafe_allow_html=True)
                    with col_act2:
                        if st.button("📧 Enviar", use_container_width=True):
                            if not email_loja or not senha_app:
                                st.error("Configure e-mail na barra lateral!")
                            elif not email_cliente:
                                st.error("Digite o e-mail!")
                            else:
                                with st.spinner("Enviando..."):
                                    suc, msg = enviar_email_orcamento(email_loja, senha_app, email_cliente,
                                                                      cliente_final, pdf_bytes)
                                    if suc:
                                        st.toast(msg, icon="✅")
                                    else:
                                        st.error(msg)

                    st.write("")

                    if st.button("✅ CONCLUIR VENDA", type="primary", use_container_width=True):
                        if tipo_pag == "A Prazo" and not lista_clientes:
                            st.error("Cadastre clientes antes!")
                        else:
                            for item in st.session_state.carrinho:
                                vp = item['total_item'] if tipo_pag == "À Vista" else 0.0
                                stt = "Recebido" if tipo_pag == "À Vista" else "Pendente"
                                run_query(
                                    '''INSERT INTO vendas (produto_id, produto_nome, cliente_nome, qtd_vendida, total, valor_pago, tipo_pagamento, data_venda, data_recebimento, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                    (item['id'], item['nome'], cliente_final, item['qtd'], item['total_item'], vp,
                                     tipo_pag, date.today(), data_venc, stt))
                                run_query("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?",
                                          (item['qtd'], item['id']))

                            st.session_state.carrinho = []
                            st.session_state.tela_vendas = 'menu'
                            st.balloons()
                            st.toast("Venda registrada com sucesso!", icon="🎉")
                            time.sleep(2)
                            st.rerun()

        elif not st.session_state.carrinho:
            st.info("Adicione itens acima para iniciar.")