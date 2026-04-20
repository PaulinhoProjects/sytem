# Gestão Agro Café ☕

Sistema modular de gestão para produtores de café, focado em produtividade, controle de estoque e monitoramento fitossanitário.

## 🚀 Funcionalidades Atuais

- **📦 Gestão de Estoque Profissional**:
    - Controle de produtos, categorias e unidades de medida.
    - Movimentações de entrada/saída com suporte a Notas Fiscais.
    - Cálculo de saldo em tempo real e avisos de estoque crítico.
    - Soft delete para preservação de dados históricos.

- **💊 Controle de Pulverização**:
    - Cronogramas de aplicação planejados.
    - Registro detalhado de aplicações (clima, equipamento, operador).
    - Monitoramento de pragas e doenças com registro fotográfico.
    - Controle automático do período de carência.

- **🤖 Inteligência e Alertas**:
    - Dashboards dinâmicos.
    - Alertas de produção baseados em dados (módulo ML).
    - Relatórios em PDF.

## 🛠️ Tecnologias

- **Backend**: Flask (Python 3.10+)
- **Banco de Dados**: PostgreSQL (via SQLAlchemy)
- **Migrações**: Flask-Migrate (Alembic)
- **Frontend**: Jinja2 + CSS Moderno

## ⚙️ Como Rodar

1. Certifique-se de ter o Python instalado.
2. Clone o repositório.
3. Configure o arquivo `.env` com suas credenciais do PostgreSQL.
4. Execute o arquivo `run_app.bat` para:
    - Criar/Ativar o ambiente virtual.
    - Instalar dependências.
    - Rodar o servidor.

## 🧪 Testes

Para rodar os testes unitários básicos:
```bash
python -m unittest tests/test_basics.py
```

## 📂 Estrutura do Projeto

- `models/`: Pacote de submodelos modulares.
- `routes/`: Blueprints de cada módulo do sistema.
- `templates/`: Interfaces organizadas por módulo.
- `migrations/`: Histórico de versões do banco de dados.
- `app.py`: Fábrica da aplicação e rotas centrais.
