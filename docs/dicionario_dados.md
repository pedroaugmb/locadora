# Dicionário de Dados - Sistema de Locadora de Veículos

**Disciplina:** Banco de Dados II (Seminário II)  
**Sistema:** Gestão de Locadora de Veículos  
**SGBD:** MySQL 8.x (Storage Engine: InnoDB, Charset: utf8mb4, Collation: utf8mb4_unicode_ci)

---

## 1. Visão Geral da Arquitetura do Banco de Dados

O banco de dados relacional é composto por **6 tabelas principais**, estruturadas para garantir a integridade referencial, normalização (até a 3ª Forma Normal) e rastreabilidade total das operações de locação, devolução, pagamentos e multas.

Complementarmente, a camada avançada de banco de dados conta com:
- **Índices Secundários (B-Tree)** para otimização de buscas frequentes, filtros de status e junções;
- **Views (Visões Gerenciais)** para consolidação de indicadores e simplificação de relatórios;
- **Stored Procedures** para encapsulamento de regras de fechamento e cálculos financeiros;
- **Triggers** para sincronização automática do status da frota de veículos.

---

## 2. Tabelas Relacionais

### 2.1 Tabela: `funcionarios`
* **Descrição:** Armazena os dados cadastrais e credenciais de acesso dos colaboradores e administradores da locadora.

| Coluna | Tipo | Nulo | Chave | Padrão | Descrição |
|---|---|---|---|---|---|
| `id_funcionario` | `INT` | Não | PK | `AUTO_INCREMENT` | Identificador único sequencial do funcionário. |
| `nome` | `VARCHAR(100)` | Não | - | - | Nome completo do colaborador. |
| `cpf` | `VARCHAR(14)` | Não | UK | - | Cadastro de Pessoa Física formatado (`XXX.XXX.XXX-XX`), obrigatório e exclusivo. |
| `email` | `VARCHAR(100)` | Não | UK | - | Endereço de e-mail institucional do colaborador. |
| `senha_hash` | `VARCHAR(255)` | Sim | - | `NULL` | Hash criptográfico da senha (gerado com scrypt/pbkdf2 via Werkzeug). |
| `telefone` | `VARCHAR(20)` | Sim | - | `NULL` | Telefone de contato do colaborador. |
| `cargo` | `VARCHAR(50)` | Sim | - | `NULL` | Cargo funcional (ex.: `ADMIN`, `ATENDENTE`, `GERENTE`). |
| `usuario` | `VARCHAR(50)` | Não | UK | - | Nome de usuário único para autenticação no sistema. |

---

### 2.2 Tabela: `clientes`
* **Descrição:** Mantém o registro cadastral dos clientes aptos a alugar veículos.

| Coluna | Tipo | Nulo | Chave | Padrão | Descrição |
|---|---|---|---|---|---|
| `cpf` | `VARCHAR(14)` | Não | PK | - | CPF do cliente formatado (`XXX.XXX.XXX-XX`), atuando como chave primária natural. |
| `nome` | `VARCHAR(100)` | Não | - | - | Nome civil completo do cliente. |
| `telefone` | `VARCHAR(20)` | Sim | - | `NULL` | Número de telefone/WhatsApp para contato. |
| `email` | `VARCHAR(100)` | Sim | - | `NULL` | Endereço de e-mail do cliente. |
| `cnh` | `VARCHAR(20)` | Não | UK | - | Número de registro da Carteira Nacional de Habilitação. |

* **Índices Adicionais:**
  - `idx_clientes_nome` em `(nome)` para acelerar consultas e buscas textuais por cliente.

---

### 2.3 Tabela: `veiculos`
* **Descrição:** Catálogo da frota de veículos disponíveis, alugados ou em oficina.

| Coluna | Tipo | Nulo | Chave | Padrão | Descrição |
|---|---|---|---|---|---|
| `placa` | `VARCHAR(10)` | Não | PK | - | Placa do veículo (padrão Mercosul ou antigo), sem formatação ou padronizada em caixa alta. |
| `marca` | `VARCHAR(50)` | Não | - | - | Montadora ou fabricante do automóvel (ex.: `Toyota`, `Fiat`). |
| `modelo` | `VARCHAR(50)` | Não | - | - | Nome comercial do modelo (ex.: `Corolla`, `HB20`). |
| `ano` | `INT` | Não | - | - | Ano de fabricação/modelo do veículo. |
| `valor_diaria` | `DECIMAL(10,2)` | Não | - | - | Preço da diária de locação em reais (R$). |
| `status` | `VARCHAR(20)` | Não | - | `'DISPONIVEL'` | Situação do veículo no pátio: `DISPONIVEL`, `ALUGADO`, `MANUTENCAO`. |

* **Restrições (Constraints):**
  - `ck_veiculo_status`: `CHECK (status IN ('DISPONIVEL', 'ALUGADO', 'MANUTENCAO'))`.
* **Índices Adicionais:**
  - `idx_veiculos_status` em `(status)` para agilizar a filtragem de carros disponíveis para locação imediata.

---

### 2.4 Tabela: `locacoes`
* **Descrição:** Entidade central do domínio; registra os contratos de locação realizados entre cliente, funcionário e veículo.

| Coluna | Tipo | Nulo | Chave | Padrão | Descrição |
|---|---|---|---|---|---|
| `id_locacao` | `INT` | Não | PK | `AUTO_INCREMENT` | Identificador numérico exclusivo do contrato de locação. |
| `cpf_cliente` | `VARCHAR(14)` | Não | FK | - | CPF do cliente contratante (referencia `clientes.cpf`). |
| `placa_veiculo` | `VARCHAR(10)` | Não | FK | - | Placa do carro alugado (referencia `veiculos.placa`). |
| `id_funcionario` | `INT` | Não | FK | - | ID do atendente responsável (referencia `funcionarios.id_funcionario`). |
| `data_retirada` | `DATE` | Não | - | - | Data de início do período de locação. |
| `data_devolucao` | `DATE` | Não | - | - | Data prevista ou realizada de devolução do veículo. |
| `valor_total` | `DECIMAL(10,2)` | Não | - | - | Valor total da locação consolidado (diárias + eventuais multas). |
| `status` | `VARCHAR(20)` | Não | - | `'ATIVA'` | Estado do contrato: `ATIVA`, `FINALIZADA` ou `CANCELADA`. |

* **Restrições de Chave Estrangeira:**
  - `fk_locacao_cliente`: `FOREIGN KEY (cpf_cliente) REFERENCES clientes(cpf) ON UPDATE CASCADE ON DELETE RESTRICT`
  - `fk_locacao_veiculo`: `FOREIGN KEY (placa_veiculo) REFERENCES veiculos(placa) ON UPDATE CASCADE ON DELETE RESTRICT`
  - `fk_locacao_funcionario`: `FOREIGN KEY (id_funcionario) REFERENCES funcionarios(id_funcionario) ON UPDATE CASCADE ON DELETE RESTRICT`
  - `ck_locacao_status`: `CHECK (status IN ('ATIVA', 'FINALIZADA', 'CANCELADA'))`
* **Índices Adicionais:**
  - `idx_locacoes_status_data`: Índice composto em `(status, data_retirada)`.
  - `idx_locacoes_cliente`: Índice em `(cpf_cliente)` para histórico de locações.
  - `idx_locacoes_veiculo`: Índice em `(placa_veiculo)` para rotatividade do veículo.

---

### 2.5 Tabela: `pagamentos`
* **Descrição:** Histórico de lançamentos financeiros efetuados para quitação de uma locação.

| Coluna | Tipo | Nulo | Chave | Padrão | Descrição |
|---|---|---|---|---|---|
| `id_pagamento` | `INT` | Não | PK | `AUTO_INCREMENT` | Identificador único do pagamento. |
| `id_locacao` | `INT` | Não | FK | - | Locação a que se refere o pagamento (referencia `locacoes.id_locacao`). |
| `valor` | `DECIMAL(10,2)` | Não | - | - | Quantia paga em reais. |
| `forma_pagamento` | `VARCHAR(30)` | Não | - | - | Método de quitação (ex.: `PIX`, `CARTAO_CREDITO`, `CARTAO_DEBITO`, `DINHEIRO`). |
| `data_pagamento` | `DATE` | Não | - | - | Data efetiva da transação financeira. |

* **Restrições de Chave Estrangeira:**
  - `fk_pagamento_locacao`: `FOREIGN KEY (id_locacao) REFERENCES locacoes(id_locacao) ON UPDATE CASCADE ON DELETE CASCADE`
* **Índices Adicionais:**
  - `idx_pagamentos_locacao` em `(id_locacao)` para otimizar agregações de totais pagos.

---

### 2.6 Tabela: `multas`
* **Descrição:** Penalidades financeiras aplicadas a uma locação (ex.: avarias, atrasos na devolução, infrações de trânsito).

| Coluna | Tipo | Nulo | Chave | Padrão | Descrição |
|---|---|---|---|---|---|
| `id_multa` | `INT` | Não | PK | `AUTO_INCREMENT` | Identificador único da multa. |
| `id_locacao` | `INT` | Não | FK | - | Locação vinculada (referencia `locacoes.id_locacao`). |
| `motivo` | `VARCHAR(255)` | Não | - | - | Descrição textual da infração ou motivo da penalidade. |
| `valor` | `DECIMAL(10,2)` | Não | - | - | Valor cobrado pela multa em reais. |
| `data_multa` | `DATE` | Não | - | - | Data em que a multa foi aplicada/registrada. |

* **Restrições de Chave Estrangeira:**
  - `fk_multa_locacao`: `FOREIGN KEY (id_locacao) REFERENCES locacoes(id_locacao) ON UPDATE CASCADE ON DELETE CASCADE`
* **Índices Adicionais:**
  - `idx_multas_locacao` em `(id_locacao)` para acelerar consultas e cálculos de extrato.

---

## 3. Visões (Views) Gerenciais

### 3.1 `vw_locacoes_detalhadas`
* **Objetivo:** Unificar as informações do contrato de locação com os dados do cliente, do carro alugado, do funcionário responsável e os subtotais calculados de pagamentos e multas.
* **Colunas Retornadas:** `id_locacao`, `status_locacao`, `data_retirada`, `data_devolucao`, `valor_total`, `cpf_cliente`, `nome_cliente`, `telefone_cliente`, `placa_veiculo`, `marca_veiculo`, `modelo_veiculo`, `valor_diaria`, `id_funcionario`, `nome_funcionario`, `total_pago`, `total_multas`.

### 3.2 `vw_veiculos_disponiveis`
* **Objetivo:** Filtrar rapidamente apenas os automóveis cujo status seja `'DISPONIVEL'`, permitindo seleção instantânea na tela de nova locação.
* **Colunas Retornadas:** `placa`, `marca`, `modelo`, `ano`, `valor_diaria`, `status`.

### 3.3 `vw_faturamento_frota`
* **Objetivo:** Consolidar métricas operacionais agregadas por marca e modelo, exibindo o número total de locações concretizadas e o faturamento total acumulado.
* **Colunas Retornadas:** `marca`, `modelo`, `total_locacoes`, `receita_total`.

---

## 4. Stored Procedures e Triggers

### 4.1 Stored Procedure: `sp_finalizar_locacao(IN p_id_locacao INT)`
* **Objetivo:** Encapsular a lógica de encerramento contratual diretamente no SGBD com garantia ACID:
  1. Verifica a existência da locação e valida se já não está finalizada;
  2. Calcula a quantidade de diárias (`DATEDIFF(data_devolucao, data_retirada)`) multiplicadas pelo valor unitário da diária do veículo;
  3. Recupera o total de multas cadastradas para a locação (`COALESCE(SUM(valor), 0.00)`);
  4. Atualiza a tabela `locacoes` com `status = 'FINALIZADA'` e `valor_total = total_diarias + total_multas`;
  5. Aciona indiretamente a trigger `trg_locacao_after_update`, liberando o veículo automaticamente para `DISPONIVEL`.

### 4.2 Triggers de Frota
* **`trg_locacao_after_insert` (AFTER INSERT em `locacoes`):**
  Se a locação for inserida com status `'ATIVA'`, atualiza o status do carro vinculado para `'ALUGADO'`.
* **`trg_locacao_after_update` (AFTER UPDATE em `locacoes`):**
  Se o status transitar de `'ATIVA'` para `'FINALIZADA'` ou `'CANCELADA'`, altera o status do carro para `'DISPONIVEL'`. Caso ocorra troca de veículo no contrato, libera o antigo e aluga o novo.
* **`trg_locacao_after_delete` (AFTER DELETE em `locacoes`):**
  Se uma locação `'ATIVA'` for excluída, restaura o status do veículo para `'DISPONIVEL'`.
