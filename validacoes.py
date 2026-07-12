"""
Camada de lógica de negócio / validação.

Contém apenas funções puras: recebem dados simples (dict/strings) e devolvem
mensagens de erro. Não acessam disco nem Streamlit diretamente.
"""

import re

CAMPOS_OBRIGATORIOS = ["nome", "email", "telefone", "cidade"]

REGEX_EMAIL = re.compile(r"^[^@\s.][^@\s]*@[^@\s.]+(\.[^@\s.]+)*\.[^@\s.]{2,}$")

# Caracteres que o Excel/LibreOffice podem interpretar como início de fórmula
# ao abrir um CSV exportado (CSV Injection). Ver RF08/RN08.
CARACTERES_FORMULA = ("=", "+", "-", "@")


def validar_campos_obrigatorios(dados: dict) -> list[str]:
    """Retorna lista de nomes de campos vazios/ausentes (RN01)."""
    campos_vazios = []
    for campo in CAMPOS_OBRIGATORIOS:
        valor = dados.get(campo, "")
        if not valor or not valor.strip():
            campos_vazios.append(campo)
    return campos_vazios


def validar_caractere_formula(texto: str) -> str | None:
    """
    Retorna mensagem de erro se o texto começar com caractere que o Excel/LibreOffice
    pode interpretar como fórmula (proteção contra CSV Injection), senão None.
    """
    if texto.strip().startswith(CARACTERES_FORMULA):
        return "O texto não pode começar com os caracteres =, +, - ou @."
    return None


def validar_nome(nome: str) -> str | None:
    """Retorna mensagem de erro se nome tiver menos de 3 caracteres (RN05), senão None."""
    if len(nome.strip()) < 3:
        return "O nome deve ter no mínimo 3 caracteres."
    return validar_caractere_formula(nome)


def validar_email(email: str) -> str | None:
    """Retorna mensagem de erro se o formato do email for inválido (RN02), senão None."""
    if not REGEX_EMAIL.match(email.strip()):
        return "O email informado não é válido. Use o formato nome@dominio.com."
    return None


def validar_telefone(telefone: str) -> str | None:
    """Retorna mensagem de erro se o telefone não seguir o padrão de 10-11 dígitos (RN03), senão None."""
    telefone = telefone.strip()
    # Só permite dígitos e os separadores (), - e espaço.
    if not re.match(r"^[\d()\-\s]+$", telefone):
        return "O telefone deve conter apenas números e os símbolos (), - e espaço."

    apenas_digitos = re.sub(r"\D", "", telefone)
    if not (10 <= len(apenas_digitos) <= 11):
        return "O telefone deve ter entre 10 e 11 dígitos numéricos (com DDD)."
    return None


def validar_cliente(dados: dict, email_existe: bool) -> list[str]:
    """
    Função orquestradora: roda todas as validações e a checagem de duplicidade,
    retornando a lista consolidada de mensagens de erro (vazia se tudo OK).
    """
    erros: list[str] = []

    campos_vazios = validar_campos_obrigatorios(dados)
    if campos_vazios:
        campos_formatados = ", ".join(campos_vazios)
        erros.append(f"Preencha o(s) campo(s) obrigatório(s): {campos_formatados}.")
        # Se há campos vazios, evita rodar as demais validações de formato sobre eles.
        return erros

    erro_nome = validar_nome(dados["nome"])
    if erro_nome:
        erros.append(erro_nome)

    erro_email = validar_email(dados["email"])
    if erro_email:
        erros.append(erro_email)
    elif email_existe:
        erros.append("Este email já está cadastrado para outro cliente.")

    erro_telefone = validar_telefone(dados["telefone"])
    if erro_telefone:
        erros.append(erro_telefone)

    erro_cidade = validar_caractere_formula(dados["cidade"])
    if erro_cidade:
        erros.append(erro_cidade)

    return erros
