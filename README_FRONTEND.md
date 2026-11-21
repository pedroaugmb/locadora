# Front-end JavaScript - Locadora

Este front-end foi criado em HTML, CSS e JavaScript puro para consumir a API Flask existente.

## Como rodar

1. Ligue o MySQL.
2. Configure usuário/senha do banco em `database.py`, se necessário.
3. Entre na pasta do backend:

```bash
cd locadora_backend
```

4. Crie e ative o ambiente virtual, se ainda não tiver feito:

```bash
python -m venv venv
venv\Scripts\activate
```

5. Instale as dependências:

```bash
pip install -r requirements.txt
```

6. Rode o Flask:

```bash
python app.py
```

7. Abra o front-end no navegador:

```text
http://127.0.0.1:5000/app
```

## O que o front-end faz

- Login de funcionário em `/funcionarios/login`
- Cadastro, listagem, edição e exclusão de funcionários
- Cadastro, listagem, edição e exclusão de clientes
- Cadastro, listagem, edição e exclusão de veículos
- Cadastro, listagem, edição e exclusão de locações
- Cadastro, listagem e exclusão de pagamentos
- Cadastro, listagem e exclusão de multas
- Dashboard com totais principais

## Observação

Pagamentos e multas não receberam botão de edição porque as rotas atuais do backend só implementam `GET`, `POST` e `DELETE` nesses dois módulos.
