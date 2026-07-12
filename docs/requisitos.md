# Documento de Requisitos — Aplicação de Cadastro de Clientes (Streamlit)

## 1. Visão Geral do Sistema

A aplicação é um sistema simples de cadastro de clientes, desenvolvido em Python com a biblioteca Streamlit, com finalidade **didática** (aprendizado de desenvolvimento de interfaces web com Python).

O sistema permite que o usuário cadastre clientes informando nome, email, telefone e cidade. Os dados são persistidos em um arquivo local `clientes.csv`, que serve como base de dados simples da aplicação. A aplicação exibe a lista de clientes já cadastrados e permite exportar esses dados em formato CSV para uso externo (ex.: Excel).

Por se tratar de um projeto de estudo, o sistema prioriza simplicidade de código e de fluxo de uso em detrimento de recursos avançados (segurança, escalabilidade, múltiplos usuários, etc.).

---

## 2. Requisitos Funcionais

| Código | Descrição |
|--------|-----------|
| **RF01** | O sistema deve permitir o cadastro de um novo cliente, informando: nome, email, telefone e cidade. |
| **RF02** | O sistema deve validar os campos obrigatórios antes de salvar um cadastro. |
| **RF03** | O sistema deve validar o formato do email informado. |
| **RF04** | O sistema deve validar o formato do telefone informado. |
| **RF05** | O sistema deve impedir o cadastro de clientes com email duplicado. |
| **RF06** | O sistema deve salvar os dados do cliente cadastrado no arquivo `clientes.csv`. |
| **RF07** | O sistema deve exibir, em tela, a lista de todos os clientes cadastrados. |
| **RF08** | O sistema deve permitir exportar a lista de clientes em formato CSV. |
| **RF09** | O sistema deve exibir mensagens de sucesso ou erro ao usuário após tentativa de cadastro. |
| **RF10** | O sistema deve exibir a lista de clientes atualizada automaticamente após um novo cadastro (sem necessidade de recarregar a página manualmente). |

---

## 3. Regras de Negócio

- **RN01 — Campos obrigatórios:** nome, email, telefone e cidade são de preenchimento obrigatório. Nenhum cadastro pode ser salvo com campo vazio.
- **RN02 — Formato de email:** o email deve seguir o padrão básico `texto@texto.dominio` (ex.: `nome@exemplo.com`). Emails fora desse padrão são rejeitados.
- **RN03 — Formato de telefone:** o telefone deve conter apenas dígitos (e opcionalmente os caracteres `(`, `)`, `-` e espaço), com no mínimo 10 e no máximo 11 dígitos numéricos (padrão brasileiro, com DDD, com ou sem o 9º dígito).
- **RN04 — Duplicidade:** não é permitido cadastrar dois clientes com o mesmo email. O email é considerado o identificador único do cliente para fins de checagem de duplicidade. Tentativas de duplicar um email cadastrado devem ser bloqueadas com mensagem de erro.
- **RN05 — Nome mínimo:** o nome deve ter no mínimo 3 caracteres, para evitar cadastros com entradas inválidas (ex.: "a", "12").
- **RN06 — Persistência incremental:** cada novo cliente cadastrado é adicionado (append) ao arquivo `clientes.csv` existente; o arquivo não é sobrescrito a cada novo cadastro.
- **RN07 — Criação automática do arquivo:** caso o arquivo `clientes.csv` não exista, o sistema deve criá-lo automaticamente no primeiro cadastro, incluindo o cabeçalho das colunas (nome, email, telefone, cidade).
- **RN08 — Exportação fiel:** a exportação em CSV deve conter exatamente os mesmos dados exibidos na listagem em tela, sem filtros ou alterações adicionais.

---

## 4. Critérios de Aceite por Requisito Funcional

**RF01 — Cadastro de cliente**
- Dado que o usuário preencheu nome, email, telefone e cidade corretamente,
- Quando o usuário confirmar o cadastro,
- Então o cliente deve ser salvo e uma mensagem de sucesso deve ser exibida.

**RF02 — Validação de campos obrigatórios**
- Dado que o usuário deixou algum campo (nome, email, telefone ou cidade) em branco,
- Quando o usuário tentar cadastrar,
- Então o sistema deve impedir o salvamento e exibir mensagem indicando o(s) campo(s) pendente(s).

**RF03 — Validação de email**
- Dado que o usuário informou um email em formato inválido (ex.: sem "@" ou sem domínio),
- Quando tentar cadastrar,
- Então o sistema deve rejeitar o cadastro e exibir mensagem de erro específica sobre o email.

**RF04 — Validação de telefone**
- Dado que o usuário informou um telefone com letras, símbolos inválidos ou quantidade de dígitos fora do intervalo permitido (10-11 dígitos),
- Quando tentar cadastrar,
- Então o sistema deve rejeitar o cadastro e exibir mensagem de erro específica sobre o telefone.

**RF05 — Bloqueio de email duplicado**
- Dado que já existe um cliente cadastrado com um determinado email,
- Quando o usuário tentar cadastrar outro cliente com o mesmo email,
- Então o sistema deve impedir o cadastro e exibir mensagem informando que o email já está em uso.

**RF06 — Persistência em CSV**
- Dado que um cadastro foi validado com sucesso,
- Quando o sistema salvar os dados,
- Então o novo registro deve constar no arquivo `clientes.csv`, preservando os registros anteriores.

**RF07 — Listagem de clientes**
- Dado que existem clientes cadastrados no arquivo `clientes.csv`,
- Quando o usuário acessar a aplicação,
- Então a lista completa de clientes (nome, email, telefone, cidade) deve ser exibida em tela.

**RF08 — Exportação em CSV**
- Dado que existe ao menos um cliente cadastrado,
- Quando o usuário clicar no botão de exportação,
- Então o sistema deve disponibilizar um arquivo CSV para download contendo todos os clientes listados.

**RF09 — Mensagens de feedback**
- Dado que o usuário realizou uma ação de cadastro (com sucesso ou erro),
- Quando a ação for processada,
- Então o sistema deve exibir uma mensagem clara indicando o resultado (sucesso ou o motivo do erro).

**RF10 — Atualização automática da lista**
- Dado que um novo cliente foi cadastrado com sucesso,
- Quando a tela for renderizada novamente pelo Streamlit,
- Então a lista de clientes exibida deve incluir o novo cliente, sem exigir ação manual adicional do usuário além do cadastro.

---

## 5. Fora de Escopo

Os itens abaixo **não** fazem parte deste projeto, por se tratar de uma aplicação simples e didática:

- **Edição de clientes cadastrados** — não haverá funcionalidade para alterar dados de um cliente já cadastrado.
- **Exclusão de clientes cadastrados** — não haverá funcionalidade para remover clientes da base.
- **Autenticação e autorização de usuários** (login, senha, perfis de acesso).
- **Uso de banco de dados relacional ou NoSQL** (ex.: MySQL, PostgreSQL, MongoDB) — a persistência será feita exclusivamente via arquivo `clientes.csv`.
- **Importação de dados** a partir de arquivos externos (ex.: importar CSV de terceiros).
- **Múltiplos usuários simultâneos ou controle de concorrência** no acesso ao arquivo CSV.
- **Validações avançadas** de email (verificação de existência real do endereço) ou telefone (verificação de DDD válido, operadora, etc.).
- **Internacionalização** (suporte a formatos de telefone/endereço de outros países).
- **Interface responsiva para dispositivos móveis** ou testes de usabilidade formais.
- **Deploy em produção, versionamento de dados ou backups automáticos.**

Observação: conforme escopo definido pelo usuário, a aplicação contempla apenas **cadastrar**, **listar** e **exportar** clientes — funcionalidades de edição e exclusão ficam explicitamente fora do escopo deste projeto.
