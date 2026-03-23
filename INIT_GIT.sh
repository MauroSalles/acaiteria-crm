#!/usr/bin/env bash
# Script para inicializar repositório Git do projeto
# Execute apenas uma vez no início do projeto

echo "================================"
echo "🚀 Inicializando Repositório Git"
echo "================================"

# Verificar se já é um repositório
if [ -d .git ]; then
    echo "⚠️  Git já inicializado neste diretório"
    exit 1
fi

# Inicializar repositório
git init
echo "✅ Repositório Git inicializado"

# Adicionar remoto (você precisa criar repo no GitHub primeiro)
# git remote add origin https://github.com/<seu-usuario>/AcaiteriaCRM.git

# Adicionar arquivos
git add .
git add --sparse-checkout .gitignore
echo "✅ Arquivos adicionados"

# Primeiro commit
git commit -m "🚀 Inicial: Setup do Projeto Integrador CRM Açaiteria

- Backend Flask com SQLAlchemy
- Frontend responsivo (HTML/CSS/JS)
- Schema SQL com dados de teste
- Conformidade LGPD
- Documentação completa
- Endpoints de API
- Sistema de relatórios"

echo ""
echo "================================"
echo "✅ Repositório inicializado!"
echo "================================"
echo ""
echo "Próximos passos:"
echo "1. Crie um repositório no GitHub"
echo "2. Execute: git remote add origin <URL_DO_SEU_REPO>"
echo "3. Execute: git push -u origin main"
echo ""
echo "Para mais informações, consulte RUN.md"
