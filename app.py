"""
Camada de interface (UI) — ponto de entrada Streamlit.

Orquestra chamadas às camadas de validação (validacoes.py) e persistência
(repositorio_clientes.py). Não contém regras de negócio nem lógica de
leitura/escrita de arquivo.
"""

import streamlit as st

import repositorio_clientes as repositorio
import validacoes


CAMPOS_FORMULARIO = ("campo_nome", "campo_email", "campo_telefone", "campo_cidade")


def exibir_formulario_cadastro() -> dict | None:
    """Renderiza st.form e retorna os dados digitados quando o usuário submete."""
    if st.session_state.pop("limpar_formulario", False):
        for campo in CAMPOS_FORMULARIO:
            st.session_state[campo] = ""

    with st.form("form_cadastro_cliente", clear_on_submit=False):
        nome = st.text_input("Nome", key="campo_nome")
        email = st.text_input("Email", key="campo_email")
        telefone = st.text_input("Telefone", placeholder="(11) 98765-4321", key="campo_telefone")
        cidade = st.text_input("Cidade", key="campo_cidade")

        enviado = st.form_submit_button("Cadastrar")

    if enviado:
        return {
            "nome": nome.strip(),
            "email": email.strip(),
            "telefone": telefone.strip(),
            "cidade": cidade.strip(),
        }
    return None


def exibir_listagem_clientes(clientes) -> None:
    """Renderiza st.dataframe com os clientes cadastrados."""
    st.subheader("Clientes cadastrados")
    if clientes.empty:
        st.info("Nenhum cliente cadastrado ainda.")
    else:
        st.dataframe(clientes, use_container_width=True)


def exibir_botao_exportacao(clientes) -> None:
    """Renderiza st.download_button oferecendo o CSV para download (RF08, RN08)."""
    # to_csv sem salvar em disco: gera a string em memória, fiel aos dados exibidos.
    csv_bytes = clientes.to_csv(index=False, encoding="utf-8").encode("utf-8")
    st.download_button(
        label="Exportar CSV",
        data=csv_bytes,
        file_name="clientes.csv",
        mime="text/csv",
        disabled=clientes.empty,
    )


def main() -> None:
    """Ponto de entrada Streamlit: monta layout, formulário, listagem e exportação."""
    st.title("Cadastro de Clientes")

    try:
        dados_formulario = exibir_formulario_cadastro()

        if dados_formulario is not None:
            email_existe = repositorio.email_ja_cadastrado(dados_formulario["email"])
            erros = validacoes.validar_cliente(dados_formulario, email_existe)

            if erros:
                for erro in erros:
                    st.error(erro)
            else:
                repositorio.salvar_cliente(dados_formulario)
                st.success("Cliente cadastrado com sucesso!")
                st.session_state["limpar_formulario"] = True
                st.rerun()

        clientes = repositorio.ler_clientes()
        exibir_listagem_clientes(clientes)
        exibir_botao_exportacao(clientes)

    except RuntimeError:
        # Erros técnicos de I/O já foram traduzidos em repositorio_clientes.py;
        # aqui apenas evitamos expor stack trace ao usuário final.
        st.error("Não foi possível acessar o arquivo de clientes.")


if __name__ == "__main__":
    main()
