"""
Camada de persistência da aplicação.

Responsável exclusivamente por ler e gravar clientes no arquivo clientes.csv.
Não conhece regras de validação nem Streamlit (ver validacoes.py e app.py).
"""

import os
import pandas as pd

CAMINHO_CSV = "clientes.csv"
COLUNAS = ["nome", "email", "telefone", "cidade"]


def garantir_arquivo_existe(caminho: str = CAMINHO_CSV) -> None:
    """Cria o arquivo CSV com cabeçalho se ele ainda não existir (RN07)."""
    if not os.path.exists(caminho):
        try:
            df_vazio = pd.DataFrame(columns=COLUNAS)
            df_vazio.to_csv(caminho, index=False, encoding="utf-8")
        except OSError as erro:
            raise RuntimeError("Não foi possível criar o arquivo de clientes.") from erro


def ler_clientes(caminho: str = CAMINHO_CSV) -> pd.DataFrame:
    """Lê todos os clientes cadastrados. Retorna DataFrame vazio (com colunas) se não houver dados."""
    garantir_arquivo_existe(caminho)
    try:
        # dtype=str evita que o pandas "adivinhe" tipos (ex.: telefone virar número)
        df = pd.read_csv(caminho, dtype=str, encoding="utf-8")
        df = df.fillna("")
        # Garante que o DataFrame sempre tenha exatamente as colunas esperadas,
        # na ordem esperada, mesmo que o arquivo em disco esteja fora de ordem
        # ou com colunas faltando (evita corrupção silenciosa no append e KeyError).
        for coluna in COLUNAS:
            if coluna not in df.columns:
                df[coluna] = ""
        return df[COLUNAS]
    except pd.errors.EmptyDataError:
        # Arquivo existe mas está vazio (sem nem o cabeçalho) — trata como base vazia.
        return pd.DataFrame(columns=COLUNAS)
    except (OSError, pd.errors.ParserError) as erro:
        raise RuntimeError("Não foi possível ler o arquivo de clientes.") from erro


def salvar_cliente(cliente: dict, caminho: str = CAMINHO_CSV) -> None:
    """Adiciona (append) um novo cliente ao CSV, preservando os registros existentes (RN06)."""
    try:
        clientes_atuais = ler_clientes(caminho)
        cliente_normalizado = {**cliente, "email": cliente["email"].strip().lower()}
        novo_df = pd.DataFrame([cliente_normalizado], columns=COLUNAS)
        clientes_atualizados = pd.concat([clientes_atuais, novo_df], ignore_index=True)
        clientes_atualizados.to_csv(caminho, index=False, encoding="utf-8")
    except OSError as erro:
        raise RuntimeError("Não foi possível salvar o cliente no arquivo.") from erro


def email_ja_cadastrado(email: str, caminho: str = CAMINHO_CSV) -> bool:
    """Verifica duplicidade de email consultando os registros já persistidos (RN04)."""
    clientes = ler_clientes(caminho)
    if clientes.empty:
        return False
    # Comparação case-insensitive, conforme regra de negócio.
    emails_cadastrados = clientes["email"].str.lower()
    return email.strip().lower() in emails_cadastrados.values
