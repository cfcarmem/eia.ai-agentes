# Cadastro de Clientes (Streamlit)

Aplicação didática em Python + Streamlit para cadastro simples de clientes. Permite registrar nome, email, telefone e cidade, com persistência local em arquivo CSV, listagem em tela e exportação dos dados.

O projeto tem finalidade de estudo (aprendizado de desenvolvimento de interfaces web com Python), priorizando simplicidade de código em vez de recursos avançados como banco de dados, autenticação ou suporte a múltiplos usuários.

## Funcionalidades

- Cadastro de clientes (nome, email, telefone e cidade) via formulário.
- Validação dos dados antes de salvar (campos obrigatórios, formato de email e telefone, duplicidade de email).
- Persistência dos cadastros em arquivo local `clientes.csv` (criado automaticamente no primeiro uso).
- Listagem em tela de todos os clientes já cadastrados, atualizada automaticamente após cada novo cadastro.
- Exportação da lista de clientes em CSV para download.
- Mensagens de sucesso/erro exibidas ao usuário após cada tentativa de cadastro.

## Estrutura de arquivos

```
eia.ai-agentes/
├── app.py                     # Camada de interface (UI) — ponto de entrada Streamlit
├── validacoes.py               # Camada de lógica de negócio / validação dos dados
├── repositorio_clientes.py     # Camada de persistência (leitura/escrita do clientes.csv)
├── requirements.txt             # Dependências do projeto
├── clientes.csv                 # Arquivo de dados (criado automaticamente na 1ª execução)
└── docs/
    ├── requisitos.md            # Requisitos funcionais e regras de negócio detalhados
    └── arquitetura.md           # Documento de arquitetura da aplicação
```

## Pré-requisitos

- Python 3.10 ou superior (recomendado, por compatibilidade com as anotações de tipo usadas no código, ex. `dict | None`).
- `pip` instalado.

## Como instalar

1. Clone ou baixe este repositório e acesse a pasta do projeto:
   ```bash
   cd eia.ai-agentes
   ```
2. (Opcional, mas recomendado) Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   ```
   No Windows:
   ```bash
   venv\Scripts\activate
   ```
   No Linux/Mac:
   ```bash
   source venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Como executar

Com o ambiente virtual ativado (se estiver usando um) e as dependências instaladas, execute:

```bash
streamlit run app.py
```

O Streamlit abrirá automaticamente a aplicação no navegador (por padrão em `http://localhost:8501`).

## Como usar a aplicação

1. Preencha o formulário de cadastro com **nome**, **email**, **telefone** e **cidade**.
2. Clique em **Cadastrar**.
   - Se algum dado for inválido, mensagens de erro serão exibidas indicando o que precisa ser corrigido.
   - Se o cadastro for válido, uma mensagem de sucesso é exibida e o formulário é limpo automaticamente.
3. A lista de clientes cadastrados é exibida logo abaixo do formulário, sempre atualizada com o cadastro mais recente.
4. Clique em **Exportar CSV** para baixar um arquivo `clientes.csv` com todos os clientes listados na tela.

## Regras de validação principais

- Todos os campos (nome, email, telefone, cidade) são obrigatórios.
- O nome deve ter no mínimo 3 caracteres.
- O email deve seguir um formato válido (`nome@dominio.com`) e é normalizado para minúsculas ao ser salvo.
- Não é permitido cadastrar dois clientes com o mesmo email (verificação sem diferenciar maiúsculas/minúsculas).
- O telefone deve conter apenas dígitos e os símbolos `(`, `)`, `-` e espaço, com 10 ou 11 dígitos numéricos (padrão brasileiro, com DDD).
- Campos de texto não podem começar com os caracteres `=`, `+`, `-` ou `@`, como proteção contra CSV Injection ao abrir o arquivo exportado no Excel/LibreOffice.

Para a lista completa de requisitos e critérios de aceite, consulte [`docs/requisitos.md`](docs/requisitos.md).

## Limitações conhecidas / fora de escopo

- Não há funcionalidade de **edição** de clientes já cadastrados.
- Não há funcionalidade de **exclusão** de clientes.
- Não utiliza banco de dados — a persistência é feita exclusivamente via arquivo `clientes.csv`.
- Não possui autenticação, login ou controle de acesso.
- Projeto pensado para **uso single-user**; não há tratamento de concorrência para múltiplos usuários acessando o arquivo simultaneamente.
- Não há importação de dados de arquivos externos, nem validações avançadas de email/telefone (ex.: verificação real de existência do endereço ou do DDD).

## Documentação detalhada

- [`docs/requisitos.md`](docs/requisitos.md) — requisitos funcionais, regras de negócio, critérios de aceite e itens fora de escopo.
- [`docs/arquitetura.md`](docs/arquitetura.md) — visão geral da arquitetura, estrutura de camadas, funções principais e tratamento de erros.
