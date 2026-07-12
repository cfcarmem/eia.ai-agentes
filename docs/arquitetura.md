# Documento de Arquitetura — Aplicação de Cadastro de Clientes (Streamlit)

## 1. Visão Geral da Arquitetura

Trata-se de uma aplicação **monolítica simples**, de finalidade didática, organizada em **poucos módulos Python** dentro de um único processo Streamlit (sem API, sem banco de dados, sem serviços externos).

A aplicação segue uma separação leve em três camadas lógicas, mas fisicamente concentradas em três arquivos:

- **Camada de Interface (UI)** — responsável por exibir o formulário, a listagem e o botão de exportação, usando Streamlit.
- **Camada de Lógica de Negócio / Validação** — responsável pelas regras de negócio (campos obrigatórios, formato de email/telefone, duplicidade).
- **Camada de Persistência** — responsável por ler e gravar dados no arquivo `clientes.csv`.

Não há necessidade de padrões arquiteturais complexos (MVC completo, camadas de serviço, repositórios abstratos, injeção de dependência etc.). A comunicação entre camadas se dá por chamadas de função diretas — sem classes, sem frameworks adicionais — mantendo o código legível para fins de aprendizado.

Fluxo básico de execução:

1. Streamlit renderiza o formulário de cadastro e a listagem atual de clientes (lida do CSV).
2. Usuário preenche o formulário e clica em "Cadastrar".
3. A camada de validação verifica os dados; se inválidos, retorna mensagens de erro para a UI.
4. Se válidos, a camada de persistência grava (append) o novo registro em `clientes.csv`.
5. Streamlit re-executa o script (comportamento nativo do framework) e a listagem é recarregada automaticamente a partir do CSV, já refletindo o novo cliente (atende RF10 sem necessidade de código adicional de "refresh").
6. Usuário pode clicar em "Exportar CSV" para baixar os dados exibidos, via `st.download_button`.

---

## 2. Estrutura de Pastas/Arquivos Proposta

```
eia.ai-agentes/
├── app.py                # Camada de interface (UI) — ponto de entrada Streamlit
├── validacoes.py         # Camada de lógica de negócio / validação
├── repositorio_clientes.py  # Camada de persistência (leitura/escrita do CSV)
├── clientes.csv          # Arquivo de dados (criado automaticamente na 1ª execução)
└── docs/
    ├── requisitos.md
    └── arquitetura.md
```

Total: **3 arquivos Python**, dentro do limite de 3-4 estabelecido. Não há pastas adicionais (`src/`, `tests/`, `models/` etc.) para manter o projeto enxuto e de fácil navegação para fins didáticos.

---

## 3. Divisão de Responsabilidades

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| **Interface (UI)** | `app.py` | Renderizar formulário (`st.form`), capturar inputs, exibir mensagens (`st.success`/`st.error`), exibir tabela de clientes (`st.dataframe`), disponibilizar botão de exportação (`st.download_button`). Orquestra chamadas às camadas de validação e persistência, mas não contém regras de negócio nem lógica de leitura/escrita de arquivo. |
| **Lógica de Negócio / Validação** | `validacoes.py` | Conter funções puras que recebem os dados do formulário e retornam se são válidos e quais erros ocorreram (campos obrigatórios, formato de email, formato de telefone, tamanho mínimo do nome, verificação de duplicidade de email a partir da lista de clientes já existente). Não acessa o disco nem o Streamlit diretamente. |
| **Persistência** | `repositorio_clientes.py` | Conter funções para ler todos os clientes do `clientes.csv` (retornando lista de dicionários ou DataFrame), verificar/criar o arquivo com cabeçalho caso não exista, e adicionar (append) um novo cliente ao arquivo. Não conhece regras de validação nem Streamlit. |

Essa divisão evita que `app.py` fique "inchado", mas sem introduzir camadas desnecessárias (ex.: não há camada de "controller" ou "service" separada da validação, pois seria redundante em um projeto deste porte).

---

## 4. Principais Funções/Módulos Previstos

### `repositorio_clientes.py`

```python
CAMINHO_CSV = "clientes.csv"
COLUNAS = ["nome", "email", "telefone", "cidade"]

def garantir_arquivo_existe(caminho: str = CAMINHO_CSV) -> None:
    """Cria o arquivo CSV com cabeçalho se ele ainda não existir (RN07)."""

def ler_clientes(caminho: str = CAMINHO_CSV) -> list[dict] | pd.DataFrame:
    """Lê todos os clientes cadastrados. Retorna lista vazia/DataFrame vazio se não houver dados."""

def salvar_cliente(cliente: dict, caminho: str = CAMINHO_CSV) -> None:
    """Adiciona (append) um novo cliente ao CSV, preservando os registros existentes (RN06)."""

def email_ja_cadastrado(email: str, caminho: str = CAMINHO_CSV) -> bool:
    """Verifica duplicidade de email consultando os registros já persistidos (RN04)."""
```

### `validacoes.py`

```python
def validar_campos_obrigatorios(dados: dict) -> list[str]:
    """Retorna lista de nomes de campos vazios/ausentes (RN01)."""

def validar_nome(nome: str) -> str | None:
    """Retorna mensagem de erro se nome tiver menos de 3 caracteres (RN05), senão None."""

def validar_email(email: str) -> str | None:
    """Retorna mensagem de erro se o formato do email for inválido (RN02), senão None."""

def validar_telefone(telefone: str) -> str | None:
    """Retorna mensagem de erro se o telefone não seguir o padrão de 10-11 dígitos (RN03), senão None."""

def validar_cliente(dados: dict, email_existe: bool) -> list[str]:
    """Função orquestradora: roda todas as validações acima e a checagem de duplicidade,
    retornando a lista consolidada de mensagens de erro (vazia se tudo OK)."""
```

### `app.py`

```python
def main() -> None:
    """Ponto de entrada Streamlit: monta layout, formulário, listagem e exportação."""

def exibir_formulario_cadastro() -> dict | None:
    """Renderiza st.form e retorna os dados digitados quando o usuário submete."""

def exibir_listagem_clientes(clientes) -> None:
    """Renderiza st.dataframe/st.table com os clientes cadastrados."""

def exibir_botao_exportacao(clientes) -> None:
    """Renderiza st.download_button oferecendo o CSV para download (RF08, RN08)."""
```

Não há classes nem estado em memória além do que o próprio Streamlit gerencia por reexecução (`st.rerun` implícito) — o CSV é a única fonte de verdade, o que simplifica bastante o raciocínio sobre o estado da aplicação.

---

## 5. Formato do Arquivo `clientes.csv`

Cabeçalho fixo, codificação UTF-8, separador vírgula:

```csv
nome,email,telefone,cidade
Maria Silva,maria.silva@exemplo.com,(11) 98765-4321,São Paulo
João Souza,joao.souza@exemplo.com,1132345678,Curitiba
```

| Coluna | Tipo | Observações |
|---|---|---|
| `nome` | texto | mínimo 3 caracteres (RN05) |
| `email` | texto | formato `texto@texto.dominio`; único no arquivo (RN02, RN04) |
| `telefone` | texto | armazenado como digitado (dígitos e opcionalmente `(`, `)`, `-`, espaço); 10-11 dígitos numéricos (RN03) |
| `cidade` | texto | obrigatório, sem validação de formato específica |

O arquivo é criado automaticamente com esse cabeçalho no primeiro cadastro (RN07) e cada novo cliente é *appendado* como uma nova linha (RN06).

---

## 6. Bibliotecas / Dependências

| Biblioteca | Uso | Justificativa |
|---|---|---|
| **streamlit** | Framework de UI | Requisito explícito do projeto. |
| **pandas** | Leitura/escrita e manipulação do CSV, exibição em `st.dataframe` | Embora o módulo `csv` nativo fosse suficiente para o volume de dados de um projeto didático, `pandas` é adotado porque: (a) se integra nativamente com `st.dataframe`/`st.table`, exigindo menos código de conversão; (b) `DataFrame.to_csv()` facilita tanto o append quanto a geração do CSV para `st.download_button`; (c) é uma biblioteca que o público didático deste projeto provavelmente já usa/vai aprender, sendo pedagogicamente relevante. Para um projeto ainda mais minimalista, o módulo `csv` nativo seria uma alternativa igualmente válida — mas `pandas` reduz a quantidade de código boilerplate nas camadas de UI e persistência. |
| **re** (nativo) | Validação de formato de email/telefone via expressões regulares | Já incluso no Python padrão, sem necessidade de dependência externa. |

Não há necessidade de bibliotecas de validação mais robustas (ex.: `email-validator`, `pydantic`) dado o caráter didático e o escopo intencionalmente simples das regras (RN02, RN03).

Arquivo `requirements.txt` sugerido:

```
streamlit
pandas
```

---

## 7. Tratamento de Erros e Validações

**Onde ficam as validações:**
- Todas as regras de negócio (RN01-RN05) ficam centralizadas em `validacoes.py`, como funções puras que recebem dados simples (dict/strings) e retornam mensagens de erro — nunca lançam exceções para fluxo de controle normal, nem acessam `st.*` diretamente. Isso mantém a validação testável isoladamente e reutilizável.
- A checagem de duplicidade (RN04) depende de dados persistidos; por isso `app.py` primeiro consulta `repositorio_clientes.email_ja_cadastrado()` e passa o resultado para `validacoes.validar_cliente()`, mantendo `validacoes.py` sem dependência direta do disco.

**Como as validações se propagam para a UI:**
- `app.py`, ao receber a submissão do formulário, chama `validar_cliente(dados, email_existe)`.
- Se a lista de erros retornada não for vazia, `app.py` exibe cada mensagem via `st.error(...)` (RF09) e **não** chama `salvar_cliente`, interrompendo o fluxo de gravação.
- Se não houver erros, `app.py` chama `salvar_cliente(dados)` e exibe `st.success("Cliente cadastrado com sucesso!")`.

**Erros técnicos / de infraestrutura (não regras de negócio):**
- Problemas de leitura/escrita do arquivo (ex.: permissão de disco, arquivo corrompido) são tratados dentro de `repositorio_clientes.py` com blocos `try/except` pontuais, convertendo exceções técnicas (`OSError`, `pd.errors.ParserError` etc.) em uma exceção de aplicação simples ou em um retorno de erro que `app.py` exibe via `st.error("Não foi possível acessar o arquivo de clientes.")`, evitando que o *stack trace* técnico apareça diretamente ao usuário final.
- Como o projeto é de uso único (não há concorrência prevista — item fora de escopo), não há necessidade de locking de arquivo ou tratamento de condições de corrida.

**Resumo do fluxo de erro:**
```
Usuário submete formulário
        │
        ▼
validar_cliente() em validacoes.py
        │
   ┌────┴────┐
   erros?     sem erros
   │            │
   ▼            ▼
st.error(*)   salvar_cliente() em repositorio_clientes.py
(interrompe)      │
              ┌───┴───┐
           OK erro técnico
              │        │
              ▼        ▼
         st.success  st.error("erro ao salvar")
```

Essa abordagem mantém uma fronteira clara: **erros de negócio** são esperados e tratados como retorno normal de função (lista de mensagens), enquanto **erros técnicos** são tratados como exceções capturadas na camada de persistência — sem misturar as duas responsabilidades e sem expor detalhes de implementação ao usuário final.
