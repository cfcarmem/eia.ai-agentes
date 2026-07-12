# Relatório de QA — Aplicação de Cadastro de Clientes (Streamlit)

**Data:** 2026-07-12
**Escopo revisado:** `app.py`, `validacoes.py`, `repositorio_clientes.py`, `requirements.txt`, confrontados com `docs/requisitos.md` e `docs/arquitetura.md`.
**Método:** leitura estática do código + execução real de scripts de teste ad-hoc contra `repositorio_clientes.py` e `validacoes.py` (Python 3.13.5, pandas 2.2.3, streamlit 1.45.1, todos instalados no ambiente). `python -m py_compile` executado com sucesso nos três arquivos.

---

## 1. Lista de Problemas Encontrados

### P1 — [CRÍTICO] Corrupção silenciosa de dados quando o CSV existente tem colunas em ordem diferente de `COLUNAS`
- **Arquivo/linha:** `repositorio_clientes.py`, função `salvar_cliente` (linhas 40-54), especificamente linhas 44-51.
- **Descrição:** `salvar_cliente` monta `df_novo = pd.DataFrame([cliente], columns=COLUNAS)` (ordem fixa `nome, email, telefone, cidade`) e grava com `mode="a", header=not arquivo_ja_tem_cabecalho`. Se o arquivo `clientes.csv` já existente tiver as colunas em ordem diferente (por exemplo, editado manualmente, gerado por outra versão do app, ou corrompido), o `to_csv` em modo append escreve os valores **posicionalmente**, sem verificar/realinhar com o cabeçalho real do arquivo. O resultado é que os valores do novo cliente são gravados sob as colunas erradas, sem qualquer erro ou aviso.
- **Confirmado experimentalmente:** com um arquivo cujo cabeçalho é `email,nome,cidade,telefone` e uma linha válida, ao chamar `salvar_cliente({"nome":"Maria Souza","email":"maria@ex.com","telefone":"11999998888","cidade":"SP"})`, o arquivo resultante foi:
  ```
  email,nome,cidade,telefone
  joao@ex.com,Joao Silva,Curitiba,11987654321
  Maria Souza,maria@ex.com,11999998888,SP
  ```
  Ou seja, a coluna "email" da nova linha contém `Maria Souza` (o nome!) e a coluna "nome" contém o email. Isso viola RF06/RN06 (persistência correta) e é o problema mais grave encontrado, pois corrompe silenciosamente a fonte única de verdade da aplicação sem gerar nenhum erro visível ao usuário.
- **Cenário de disparo real:** não é preciso editar o CSV manualmente para ordem diferente — basta que uma versão futura do código mude `COLUNAS`, ou que o arquivo seja aberto/salvo no Excel (que pode reordenar colunas), para o bug aparecer em produção.
- **Sugestão de correção:** ao fazer append, ler o cabeçalho real do arquivo existente (ou usar `pandas.read_csv(..., nrows=0)` para obter as colunas) e reindexar `df_novo` com `df_novo = df_novo.reindex(columns=colunas_do_arquivo)` antes de gravar; ou, mais simples, sempre ler o arquivo inteiro, fazer `pd.concat` com o DataFrame padronizado e reescrever o arquivo completo (trade-off de performance aceitável nesta escala). Alternativamente, validar/normalizar o cabeçalho do arquivo na leitura (`garantir_arquivo_existe`/`ler_clientes`) e rejeitar ou corrigir arquivos com cabeçalho fora do padrão esperado.

### P2 — [ALTO] Regex de e-mail aceita formatos claramente inválidos, violando RN02/RF03
- **Arquivo/linha:** `validacoes.py`, linha 12 (`REGEX_EMAIL`) e função `validar_email` (linhas 32-36).
- **Descrição:** a regex `^[^@\s]+@[^@\s]+\.[^@\s]+$` aceita casos que a RN02 ("padrão básico `texto@texto.dominio`") não deveria permitir como válidos, e que testes reais confirmaram serem aceitos:
  - `a@b..com` → aceito (dois pontos seguidos no domínio)
  - `a@b.com.` → aceito (ponto final sobrando)
  - `.a@b.com` → aceito (ponto no início da parte local)
  - `a@b.c` → aceito (TLD de 1 caractere, não é um domínio real)
  Isso não impede o funcionamento básico do sistema, mas é uma inconsistência entre o que a RN02 pretende (formato "básico" razoável) e o que é de fato aceito, deixando passar entradas de baixa qualidade.
- **Sugestão de correção:** reforçar a regex para não aceitar pontos duplicados/adjacentes ao `@` e exigir TLD com pelo menos 2 caracteres, por exemplo algo como `^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$` combinado com uma verificação de que não há `..` na string.

### P3 — [ALTO] Risco de CSV Injection (fórmulas maliciosas) ao abrir a exportação no Excel
- **Arquivo/linha:** `repositorio_clientes.py` (`salvar_cliente`, `garantir_arquivo_existe`) e `app.py` (`exibir_botao_exportacao`, linha 47).
- **Descrição:** nenhum campo é sanitizado antes de ser escrito no CSV. Se um usuário cadastrar um nome/cidade começando com `=`, `+`, `-` ou `@` (ex.: `=cmd|'/c calc'!A1`), o valor é gravado literalmente no CSV. Confirmado por teste: o arquivo gerado contém a linha `=cmd|'/c calc'!A1,a@b.com,11987654321,SP` sem qualquer escape. Ao abrir esse CSV no Excel/LibreOffice (cenário previsto no requisito RF08 — "uso externo, ex.: Excel"), a célula pode ser interpretada como fórmula, um vetor conhecido de ataque (CSV Injection / Formula Injection).
- **Sugestão de correção:** ao gravar/exportar, prefixar campos que comecem com `=`, `+`, `-`, `@`, tab ou CR com um apóstrofo (`'`) ou espaço neutralizante, ou validar/rejeitar esses caracteres como primeiro caractere de nome/cidade.

### P4 — [MÉDIO] Checagem de duplicidade de email possui race condition (TOCTOU) entre leitura e escrita
- **Arquivo/linha:** `app.py`, linhas 65-72 (`email_ja_cadastrado` seguido de `salvar_cliente`); `repositorio_clientes.py`, `email_ja_cadastrado` (linha 57) e `salvar_cliente` (linha 40).
- **Descrição:** a verificação de duplicidade lê o arquivo inteiro, e só depois (em uma chamada separada) o novo cliente é acrescentado. Não há lock nem transação — entre a leitura e a escrita, o arquivo pode ser alterado (por exemplo, duas abas do navegador streamlit rodando simultaneamente, ou dois processos). Embora o documento de arquitetura declare explicitamente que concorrência está fora de escopo (`docs/arquitetura.md`, seção 7, e `docs/requisitos.md`, seção 5), vale registrar como achado formal de QA pois RN04 promete bloqueio de duplicidade, e o mecanismo é vulnerável em qualquer uso com mais de uma sessão simultânea (algo bastante comum mesmo em uso didático, ex. dois alunos testando ao mesmo tempo).
- **Sugestão de correção:** se for aceitável manter fora de escopo, apenas documentar essa limitação de forma explícita no próprio código/README. Caso se decida tratar, um lock de arquivo simples (ex. `filelock`) ou verificação atômica (ler+gravar dentro de uma seção crítica) resolveria.

### P5 — [MÉDIO] Nenhuma normalização do e-mail antes de persistir (case original é mantido)
- **Arquivo/linha:** `app.py`, linha 28 (`"email": email.strip()`); `repositorio_clientes.py`, `email_ja_cadastrado` (linhas 57-64).
- **Descrição:** o e-mail é salvo exatamente como digitado (mantendo maiúsculas/minúsculas), e a checagem de duplicidade em `email_ja_cadastrado` é case-insensitive (`.str.lower()`), o que está correto para *bloquear* duplicatas. Porém, como o dado persistido não é normalizado, o arquivo `clientes.csv` pode conter, por exemplo, `Maria@Exemplo.com` e futuramente (se o bug P1 for corrigido ou se o arquivo for editado manualmente) `maria@exemplo.com` explicitamente lado a lado antes de qualquer cadastro pela aplicação — não é um bug de bloqueio (isso funciona), mas gera inconsistência estética/de relatório e viola a expectativa implícita de "email como identificador único" de forma mais robusta (ex.: em uma exportação, o mesmo cliente poderia aparecer com capitalizações diferentes ao longo do tempo se o dado for editado fora da aplicação).
- **Sugestão de correção:** normalizar (`.lower()`) o e-mail no momento de salvar (em `app.py` antes de montar `dados_formulario`, ou dentro de `salvar_cliente`), preservando apenas a apresentação visual se necessário.

### P6 — [MÉDIO] `st.form` mistura `clear_on_submit=True` com strip aplicado somente após o submit — mensagens de erro não preservam o que o usuário digitou
- **Arquivo/linha:** `app.py`, linhas 15-32 (`exibir_formulario_cadastro`).
- **Descrição:** o formulário usa `clear_on_submit=True`. Isso significa que, ao clicar em "Cadastrar" e o cadastro falhar (por exemplo, e-mail inválido), o Streamlit reexecuta o script, os erros são exibidos via `st.error`, mas os campos do formulário já foram limpos automaticamente pelo `clear_on_submit=True`. Do ponto de vista de UX, o usuário perde tudo o que digitou e precisa preencher o formulário inteiro novamente mesmo que só um campo estivesse errado (ex.: telefone). Isso não viola nenhum RF/RN explicitamente, mas é uma fricção de UX relevante e contraria a boa prática usual (mensagens de erro devem preservar o que já foi digitado corretamente).
- **Sugestão de correção:** usar `clear_on_submit=False` e limpar os campos manualmente apenas quando o cadastro for bem-sucedido (por exemplo, usando `st.session_state` com chaves nos widgets e resetando-as só no caminho de sucesso).

### P7 — [MÉDIO] `validar_cliente` interrompe validação no primeiro tipo de erro (campos obrigatórios), mas não é totalmente exaustivo mesmo quando os campos estão preenchidos
- **Arquivo/linha:** `validacoes.py`, linhas 52-80 (`validar_cliente`).
- **Descrição:** quando há campos vazios, a função retorna imediatamente (linha 64: `return erros`) sem rodar as demais validações — isso é uma escolha de design aceitável e documentada no comentário. Porém, quando os campos estão preenchidos mas o e-mail é inválido (`erro_email`), a checagem de duplicidade é pulada (`elif email_existe`, linha 73) mesmo que o e-mail *coincidentemente* já exista após uma futura correção de regex — comportamento correto e esperado. O ponto de atenção real é que **a validação de duplicidade de e-mail (RN04) depende de uma leitura de arquivo feita uma única vez em `app.py` antes de chamar `validar_cliente`** (linha 65 de `app.py`), e não há revalidação entre a checagem e o `salvar_cliente` — reforça o achado P4, mas também implica que se o e-mail informado tiver espaços/maiúsculas diferentes do cadastrado, a UI mostra a mensagem de erro apontando duplicidade (correto), mas o dado exibido ao usuário no campo de erro não é normalizado, o que pode confundir levemente. Baixo impacto, mas junto com P1 mostra fragilidade geral na camada de dados compartilhados entre validação e persistência.
- **Sugestão de correção:** nenhuma ação obrigatória além das já sugeridas em P4/P5; opcionalmente adicionar teste de integração cobrindo o fluxo completo "ler → validar → salvar" para pegar regressões futuras.

### P8 — [BAIXO] `email_ja_cadastrado` e `ler_clientes` não tratam coluna "email" ausente (KeyError) se o CSV estiver malformado sem essa coluna
- **Arquivo/linha:** `repositorio_clientes.py`, linha 63 (`clientes["email"]`).
- **Descrição:** se o arquivo `clientes.csv` existir mas, por qualquer motivo (edição manual, versão antiga do app, corrupção), não tiver a coluna `email`, `clientes["email"]` lança `KeyError`, que não é capturado por nenhum `except` em `email_ja_cadastrado` nem propagado como `RuntimeError` amigável — o erro cru vazaria até `app.py`, que só captura `RuntimeError` (linha 79), resultando em uma tela de erro não tratada (stack trace do Streamlit) para o usuário final, contrariando a intenção de "nunca expor stack trace" descrita em `docs/arquitetura.md` (seção 7).
- **Sugestão de correção:** validar as colunas esperadas logo após a leitura (`ler_clientes`) e levantar `RuntimeError` com mensagem amigável se o cabeçalho não corresponder ao esperado, ou normalizar/realinhar automaticamente.

### P9 — [BAIXO] Nenhuma validação de tamanho máximo para os campos (nome, cidade, telefone) — não é requisito, mas há risco de exportação/exibição degradada
- **Arquivo/linha:** `validacoes.py` (ausência de verificação de tamanho máximo).
- **Descrição:** não há limite superior de caracteres para nome/cidade. Não é um requisito (RN01-RN08 não menciona), mas strings extremamente longas podem degradar a experiência da tabela (`st.dataframe`) e do CSV exportado. Achado de baixa severidade, apenas para registro.
- **Sugestão de correção:** opcional; considerar limite razoável (ex.: 100-150 caracteres) se o time de produto desejar.

### P10 — [BAIXO] `requirements.txt` não fixa versões, o que pode causar quebras futuras de compatibilidade
- **Arquivo/linha:** `requirements.txt` (linhas 1-2: `streamlit`, `pandas`).
- **Descrição:** o arquivo lista apenas os nomes dos pacotes, sem versão mínima/fixada (`streamlit>=...`, `pandas>=...` ou `==`). Isso está de acordo com o que `docs/arquitetura.md` sugere textualmente (seção 6: "Arquivo requirements.txt sugerido: streamlit / pandas"), então não é uma divergência de arquitetura, mas é uma prática frágil: uma atualização futura do streamlit ou pandas com breaking changes (ex.: comportamento de `st.form`, `to_csv`, ou depreciações de parâmetros como `use_container_width`) pode quebrar a aplicação silenciosamente sem que o time perceba a causa. Ambiente testado usa `streamlit==1.45.1` e `pandas==2.2.3`, ambos funcionais com o código atual.
- **Sugestão de correção:** fixar ao menos versões mínimas testadas, ex.: `streamlit>=1.45,<2`, `pandas>=2.2,<3`.

### P11 — [BAIXO] Mensagem de erro de campos obrigatórios não indica claramente qual regra de negócio foi violada quando nome tem espaços em branco apenas
- **Arquivo/linha:** `validacoes.py`, `validar_campos_obrigatorios` (linhas 15-22) vs `validar_nome` (linhas 25-29).
- **Descrição:** confirmado por teste: `validar_campos_obrigatorios({"nome": "   ", ...})` corretamente identifica "nome" como vazio (por causa do `.strip()` na linha 20) e interrompe a validação ali (RN01 tratado corretamente). Já `{"nome": " ab ", ...}` passa pela checagem de "obrigatório" (pois `" ab ".strip()` não é vazio) e só é pega depois por `validar_nome`, que corretamente rejeita por ter menos de 3 caracteres após strip. O comportamento está correto, mas o teste evidenciou que o app confia no `.strip()` já ter sido aplicado em `app.py` (linha 27-30) antes de chamar `validar_cliente` — se no futuro alguém reusar `validacoes.py` chamando as funções diretamente com dados não "stripados" antes (ex.: em um teste automatizado ou outra integração), o comportamento pode divergir sutilmente da regra de negócio esperada, pois `validar_nome` e `validar_campos_obrigatorios` fazem `.strip()` internamente de forma redundante, mas nem toda função do módulo o faz de forma consistente (ex.: `validar_email` também usa `.strip()` internamente, então está OK). Achado apenas informativo / de robustez, não é um bug ativo hoje.
- **Sugestão de correção:** nenhuma ação obrigatória; considerar centralizar o `.strip()` em um único ponto (ex.: no início de `validar_cliente`) para reduzir duplicação.

---

## 2. Checklist de Requisitos Funcionais (RF01-RF10)

| Código | Status | Observações |
|--------|--------|-------------|
| RF01 — Cadastro de cliente | **OK** | Fluxo completo implementado em `app.py` (`exibir_formulario_cadastro` + `salvar_cliente`). Sujeito ao risco de corrupção descrito em P1 quando o CSV de destino tem colunas fora de ordem. |
| RF02 — Validação de campos obrigatórios | **OK** | `validar_campos_obrigatorios` cobre corretamente strings vazias e só espaços (confirmado por teste). |
| RF03 — Validação de formato de email | **Problema (ver P2)** | Implementado e funcional para o caso comum, mas aceita formatos claramente inválidos (`a@b..com`, `a@b.com.`, `.a@b.com`, `a@b.c`). |
| RF04 — Validação de formato de telefone | **OK** | `validar_telefone` cobre corretamente letras/símbolos inválidos e intervalo de 10-11 dígitos (confirmado por teste). |
| RF05 — Bloqueio de email duplicado | **Problema (ver P4)** | Bloqueio funcional no caso de uso único/sequencial, mas com race condition (TOCTOU) em uso concorrente. |
| RF06 — Persistência em clientes.csv | **Problema (ver P1)** | Funciona no caminho feliz (arquivo criado pela própria aplicação), mas sofre corrupção silenciosa de dados se o arquivo existente tiver colunas em ordem diferente da esperada. |
| RF07 — Listagem de clientes | **OK** | `exibir_listagem_clientes` exibe corretamente via `st.dataframe`, inclusive tratando o caso vazio com `st.info`. |
| RF08 — Exportação em CSV | **Problema (ver P3)** | Exportação funcional e fiel aos dados exibidos (RN08 atendido), porém sem sanitização contra CSV/Formula Injection ao abrir no Excel. |
| RF09 — Mensagens de sucesso/erro | **OK** | `st.success`/`st.error` cobrem os caminhos de sucesso e todos os tipos de erro de validação, além de erros técnicos de I/O (`RuntimeError` capturado em `main`). Ressalva menor em P8 (KeyError não capturado). |
| RF10 — Atualização automática da lista | **OK** | Streamlit reexecuta o script após submissão do form e `ler_clientes()` é chamado novamente antes da listagem, atendendo ao requisito sem código adicional de refresh, conforme previsto na arquitetura. |

## 3. Checklist de Regras de Negócio (RN01-RN08)

| Código | Status | Observações |
|--------|--------|-------------|
| RN01 — Campos obrigatórios | **OK** | Confirmado por teste: campo só com espaços é tratado como vazio. |
| RN02 — Formato de email | **Problema (ver P2)** | Regex permissiva demais para alguns casos de borda. |
| RN03 — Formato de telefone | **OK** | Confirmado por teste: aceita 10-11 dígitos com/sem símbolos `() - espaço`; rejeita letras e quantidades fora do intervalo. |
| RN04 — Duplicidade de email | **Problema (ver P4, P5)** | Bloqueio funciona de forma case-insensitive (confirmado por teste), mas sujeito a race condition e a ausência de normalização na persistência. |
| RN05 — Nome mínimo 3 caracteres | **OK** | Confirmado por teste (`validar_nome`), inclusive após `.strip()`. |
| RN06 — Persistência incremental (append) | **Problema (ver P1)** | O append em si preserva registros anteriores (não sobrescreve), mas pode gravar valores nas colunas erradas se o cabeçalho do arquivo existente estiver fora da ordem padrão. |
| RN07 — Criação automática do arquivo com cabeçalho | **OK** | `garantir_arquivo_existe` cria o arquivo com cabeçalho correto (`COLUNAS`) quando ausente; confirmado por teste (arquivo 0 bytes / inexistente). |
| RN08 — Exportação fiel aos dados exibidos | **OK (com ressalva P3)** | O CSV exportado é gerado diretamente do mesmo DataFrame exibido em tela (sem filtros adicionais), atendendo à regra; a ressalva é apenas quanto à ausência de sanitização contra fórmulas maliciosas, não quanto à fidelidade dos dados em si. |

---

## Resumo Executivo

**Contagem de problemas por severidade:**
- Crítico: 1 (P1)
- Alto: 2 (P2, P3)
- Médio: 4 (P4, P5, P6, P7)
- Baixo: 4 (P8, P9, P10, P11)
- **Total: 11 problemas**

**Os 3 problemas mais importantes:**

1. **P1 (Crítico) — Corrupção silenciosa de dados no append.** Se o arquivo `clientes.csv` existente tiver colunas em ordem diferente da constante `COLUNAS` (`nome, email, telefone, cidade`), `salvar_cliente` grava os valores do novo cliente nas posições erradas, sem qualquer erro. Isso compromete a integridade da única fonte de dados da aplicação, violando RF06/RN06.
2. **P3 (Alto) — Risco de CSV/Formula Injection.** Nenhum campo é sanitizado antes de salvar/exportar; um valor começando com `=`, `+`, `-` ou `@` é gravado literalmente e pode ser interpretado como fórmula ao abrir no Excel/LibreOffice — cenário de uso explicitamente previsto no requisito RF08.
3. **P2 (Alto) — Regex de email permissiva demais.** Aceita formatos claramente inválidos (`a@b..com`, `a@b.com.`, `.a@b.com`, `a@b.c`), divergindo da intenção da RN02 de validar um "padrão básico" razoável.

Todos os arquivos `.py` compilam sem erros (`python -m py_compile`), e as bibliotecas `streamlit`/`pandas` estão instaladas e compatíveis com o código no ambiente de teste (Python 3.13.5, streamlit 1.45.1, pandas 2.2.3).
