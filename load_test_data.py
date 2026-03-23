#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para carregar dados de teste no banco de dados
Executa apenas UMA VEZ para popular o banco
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o caminho do projeto
projeto_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, projeto_root)

from backend.app import app, db
from backend.models import Cliente, Produto, Venda, ItemVenda, Pagamento

def carregar_dados_teste():
    """Carregar dados de teste no banco"""
    with app.app_context():
        # Verificar se já tem dados
        total_clientes = db.session.query(Cliente).count()
        if total_clientes > 0:
            print("⚠️  Banco de dados já possui dados. Pulando inserção.")
            return
        
        print("📦 Carregando dados de teste...")
        
        # Criar clientes
        clientes = [
            Cliente(
                nome='Gabriel da Silva',
                telefone='1299999001',
                email='gabriel@email.com',
                observacoes='Cliente frequente, prefere açaí com granola',
                consentimento_lgpd=True,
                data_consentimento=datetime.now(),
                ativo=True
            ),
            Cliente(
                nome='Marina Costa',
                telefone='1299999002',
                email='marina@email.com',
                observacoes='Alérgica a amendoim',
                consentimento_lgpd=True,
                data_consentimento=datetime.now(),
                ativo=True
            ),
            Cliente(
                nome='João Pereira',
                telefone='1299999003',
                email='joao@email.com',
                observacoes='Prefere diabético',
                consentimento_lgpd=True,
                data_consentimento=datetime.now(),
                ativo=True
            ),
            Cliente(
                nome='Ana Paula',
                telefone='1299999004',
                email='ana@email.com',
                consentimento_lgpd=True,
                data_consentimento=datetime.now(),
                ativo=True
            ),
            Cliente(
                nome='Carlos Mendes',
                telefone='1299999005',
                email=None,
                observacoes='Compra grandes quantidades para eventos',
                consentimento_lgpd=True,
                data_consentimento=datetime.now(),
                ativo=True
            ),
            Cliente(
                nome='Paula Rodrigues',
                telefone='1299999006',
                email='paula@email.com',
                consentimento_lgpd=False,
                ativo=True
            ),
        ]
        db.session.add_all(clientes)
        db.session.flush()
        print(f"✅ {len(clientes)} clientes inseridos")
        
        # Criar produtos
        produtos = [
            Produto(nome_produto='Açaí com Granola', categoria='Açaí Premium', descricao='Açaí puro com granola caseira', preco=25.00, ativo=True),
            Produto(nome_produto='Açaí com Banana', categoria='Açaí Premium', descricao='Açaí com banana fatiada', preco=24.00, ativo=True),
            Produto(nome_produto='Açaí Simples', categoria='Açaí Básico', descricao='Açaí puro, sem adições', preco=18.00, ativo=True),
            Produto(nome_produto='Açaí Diabético', categoria='Açaí Especial', descricao='Açaí com adoçante, sem açúcar', preco=22.00, ativo=True),
            Produto(nome_produto='Açaí Festa (500ml)', categoria='Açaí Grande', descricao='Porção grande para compartilhar', preco=35.00, ativo=True),
            Produto(nome_produto='Suco Natural - Laranja', categoria='Bebidas', descricao='Suco de laranja natural', preco=8.00, ativo=True),
            Produto(nome_produto='Suco Natural - Morango', categoria='Bebidas', descricao='Suco de morango natural', preco=10.00, ativo=True),
            Produto(nome_produto='Água', categoria='Bebidas', descricao='Água mineral', preco=3.00, ativo=True),
            Produto(nome_produto='Refrigerante', categoria='Bebidas', descricao='Refrigerante 350ml', preco=5.00, ativo=True),
            Produto(nome_produto='Granola Extra', categoria='Adicionais', descricao='Granola caseira extra', preco=5.00, ativo=True),
        ]
        db.session.add_all(produtos)
        db.session.flush()
        print(f"✅ {len(produtos)} produtos inseridos")
        
        # Criar vendas
        vendas_dados = [
            (1, 10, 25.00, 'Dinheiro', 'Concluído'),
            (2, 9, 49.00, 'Débito', 'Concluído'),
            (3, 8, 22.00, 'Dinheiro', 'Concluído'),
            (1, 7, 35.00, 'Crédito', 'Concluído'),
            (4, 6, 30.00, 'Dinheiro', 'Concluído'),
            (5, 5, 105.00, 'Dinheiro', 'Concluído'),
            (1, 4, 25.00, 'Dinheiro', 'Concluído'),
            (2, 3, 34.00, 'Débito', 'Concluído'),
            (3, 2, 50.00, 'Crédito', 'Concluído'),
            (4, 1, 72.00, 'Dinheiro', 'Concluído'),
        ]
        
        vendas = []
        for i, (id_cliente, dias_atras, valor, forma, status) in enumerate(vendas_dados):
            v = Venda(
                id_cliente=id_cliente,
                data_venda=datetime.now() - timedelta(days=dias_atras),
                valor_total=valor,
                forma_pagamento=forma,
                status_pagamento=status,
                recibo_gerado=True
            )
            vendas.append(v)
        
        db.session.add_all(vendas)
        db.session.flush()
        print(f"✅ {len(vendas)} vendas inseridas")
        
        # Criar itens de venda
        itens_dados = [
            (1, 1, 1, 25.00),
            (2, 1, 1, 25.00),
            (2, 6, 1, 8.00),
            (2, 9, 1, 5.00),
            (3, 4, 1, 22.00),
            (4, 1, 1, 25.00),
            (5, 1, 2, 25.00),
            (5, 7, 1, 10.00),
            (5, 9, 1, 5.00),
            (6, 1, 3, 25.00),
            (6, 2, 2, 24.00),
            (6, 10, 2, 5.00),
            (7, 3, 1, 18.00),
            (7, 10, 1, 5.00),
            (7, 8, 1, 3.00),
            (8, 1, 1, 25.00),
            (8, 7, 1, 10.00),
            (9, 2, 2, 24.00),
            (9, 10, 1, 5.00),
            (10, 1, 2, 25.00),
            (10, 9, 2, 5.00),
            (10, 6, 1, 8.00),
            (10, 8, 1, 3.00),
        ]
        
        itens = []
        for id_venda, id_produto, quantidade, preco in itens_dados:
            iv = ItemVenda(
                id_venda=id_venda,
                id_produto=id_produto,
                quantidade=quantidade,
                preco_unitario=preco,
                subtotal=quantidade * preco
            )
            itens.append(iv)
        
        db.session.add_all(itens)
        db.session.flush()
        print(f"✅ {len(itens)} itens de venda inseridos")
        
        # Criar pagamentos
        pagamentos = []
        formas_pagamento = ['Dinheiro', 'Débito', 'Crédito']
        refs = ['CASH', 'DEBIT', 'CREDIT']
        
        for i, venda in enumerate(vendas):
            p = Pagamento(
                id_venda=venda.id_venda,
                data_pagamento=venda.data_venda,
                valor_pago=venda.valor_total,
                metodo=formas_pagamento[i % 3],
                status='Concluído',
                referencia_transacao=f"{refs[i % 3]}-{str(i+1).zfill(3)}"
            )
            pagamentos.append(p)
        
        db.session.add_all(pagamentos)
        db.session.flush()
        print(f"✅ {len(pagamentos)} pagamentos inseridos")
        
        # Confirmar transação
        db.session.commit()
        print("\n✅ Todos os dados de teste foram carregados com sucesso!")
        print(f"\n📊 Resumo:")
        print(f"   • {len(clientes)} clientes")
        print(f"   • {len(produtos)} produtos")
        print(f"   • {len(vendas)} vendas")
        print(f"   • {len(itens)} itens de venda")
        print(f"   • {len(pagamentos)} pagamentos")

if __name__ == '__main__':
    try:
        carregar_dados_teste()
    except Exception as erro:
        print(f"❌ Erro ao carregar dados: {erro}")
        sys.exit(1)
