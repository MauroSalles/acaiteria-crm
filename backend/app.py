"""
CRM Simples - Açaiteria Combina Açaí
Aplicação Flask para gerenciamento de clientes e vendas

Desenvolvido por: Grupo 22 - Projeto Integrador UNIVESP
Data: 2026
"""

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_restx import Api, Namespace, Resource
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps
import csv
import io
import os
import hashlib
import secrets
from pydantic import BaseModel, EmailStr, ValidationError, field_validator

from .models import db, Cliente, Produto, Venda, ItemVenda, Pagamento, ConsentimentoHistorico

# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================

import os
from dotenv import load_dotenv

load_dotenv()

# Resolver caminhos absolutos para templates e arquivos estáticos
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
template_dir = os.path.join(basedir, 'frontend')
static_dir = os.path.join(basedir, 'frontend', 'static')

app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir,
            static_url_path='/static')

# Chave secreta para sessões (obrigatória em produção)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Desabilitar Swagger em produção
_doc_path = '/api/docs' if os.environ.get('FLASK_ENV') != 'production' else False

api = Api(
    app,
    version='1.0',
    title='Acaiteria CRM API',
    description='API REST do CRM — validação Pydantic, conformidade LGPD, rate-limiting.',
    doc=_doc_path,
    prefix='/api'
)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per hour"],
    storage_uri="memory://"
)

health_ns = Namespace('health', description='Healthcheck e metadados da API', path='/')
api.add_namespace(health_ns)

# Configuração do banco de dados
# Railway fornece postgres:// mas SQLAlchemy 2.x exige postgresql://
database_url = os.environ.get('DATABASE_URL', 'sqlite:///acaiteria.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = os.environ.get('FLASK_ENV') == 'development'

# Inicializar banco de dados
db.init_app(app)

# Criar tabelas automaticamente no primeiro request (necessário em produção/cloud)
with app.app_context():
    db.create_all()


class ClienteCreateSchema(BaseModel):
    nome: str
    telefone: str | None = None
    email: EmailStr | None = None
    observacoes: str | None = None
    consentimento_lgpd: bool = False
    versao_politica: str = 'v1.0'

    @field_validator('nome')
    @classmethod
    def nome_obrigatorio(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError('Nome deve ter ao menos 2 caracteres')
        return value


class ProdutoCreateSchema(BaseModel):
    nome_produto: str
    categoria: str | None = None
    descricao: str | None = None
    preco: float


class VendaItemSchema(BaseModel):
    id_produto: int
    quantidade: int


class VendaCreateSchema(BaseModel):
    id_cliente: int
    forma_pagamento: str = 'Dinheiro'
    observacoes: str | None = None
    desconto_percentual: float = 0.0
    taxa: float = 0.0
    itens: list[VendaItemSchema]

    @field_validator('desconto_percentual')
    @classmethod
    def desconto_valido(cls, v: float) -> float:
        if v < 0 or v > 100:
            raise ValueError('Desconto deve estar entre 0 e 100%')
        return v

    @field_validator('taxa')
    @classmethod
    def taxa_valida(cls, v: float) -> float:
        if v < 0:
            raise ValueError('Taxa não pode ser negativa')
        return v


class ConsentimentoSchema(BaseModel):
    consentimento_lgpd: bool
    versao_politica: str = 'v1.0'


class ProdutoUpdateSchema(BaseModel):
    nome_produto: str | None = None
    categoria: str | None = None
    descricao: str | None = None
    preco: float | None = None
    ativo: bool | None = None


def validar_payload(schema_cls):
    dados = request.get_json(silent=True) or {}
    try:
        return schema_cls.model_validate(dados).model_dump()
    except ValidationError as e:
        raise ValueError(e.errors())


# =============================================================================
# AUTENTICAÇÃO — PIN simples para proteger o sistema
# =============================================================================

# PIN padrão (pode ser alterado via variável de ambiente)
APP_PIN = os.environ.get('APP_PIN', '1234')


def login_required(f):
    """Decorator que protege rotas HTML exigindo login por PIN."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('autenticado'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    """Decorator que protege rotas API exigindo login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('autenticado'):
            return jsonify({'erro': 'Autenticação necessária'}), 401
        return f(*args, **kwargs)
    return decorated


@health_ns.route('/health')
class HealthResource(Resource):
    def get(self):
        return {
            'status': 'ok',
            'service': 'acaiteria-crm',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, 200

# =============================================================================
# ROTAS - AUTENTICAÇÃO
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login com PIN"""
    if request.method == 'POST':
        pin = request.form.get('pin', '')
        if pin == APP_PIN:
            session['autenticado'] = True
            return redirect('/')
        return render_template('login.html', erro='PIN incorreto. Tente novamente.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Encerrar sessão"""
    session.clear()
    return redirect('/login')


# =============================================================================
# ROTAS - PÁGINA INICIAL
# =============================================================================

@app.route('/')
@login_required
def index():
    """Página inicial - Dashboard"""
    try:
        # Estatísticas gerais
        total_clientes = Cliente.query.filter_by(ativo=True).count()
        total_vendas = Venda.query.count()
        faturamento_total = db.session.query(db.func.sum(Venda.valor_total)).scalar() or 0
        
        # Últimas vendas (últimos 7 dias)
        vendas_semana = Venda.query.filter(
            Venda.data_venda >= datetime.now(timezone.utc) - timedelta(days=7)
        ).count()
        
        # Clientes com permissão LGPD
        clientes_consentimento = Cliente.query.filter_by(
            ativo=True, 
            consentimento_lgpd=True
        ).count()
        
        stats = {
            'total_clientes': total_clientes,
            'total_vendas': total_vendas,
            'faturamento_total': float(faturamento_total) if faturamento_total else 0,
            'vendas_semana': vendas_semana,
            'clientes_consentimento': clientes_consentimento,
            'taxa_consentimento': round((clientes_consentimento / total_clientes * 100) if total_clientes > 0 else 0, 2)
        }
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        stats_default = {
            'total_clientes': 0,
            'total_vendas': 0,
            'faturamento_total': 0,
            'vendas_semana': 0,
            'clientes_consentimento': 0,
            'taxa_consentimento': 0,
        }
        return render_template('index.html', stats=stats_default, error=str(e))


# =============================================================================
# ROTAS - CLIENTES
# =============================================================================

@app.route('/api/clientes', methods=['GET'])
@limiter.limit("120 per minute")
def listar_clientes():
    """Listar todos os clientes ativos com busca e paginação"""
    try:
        query = Cliente.query.filter_by(ativo=True)

        # Busca por nome, telefone ou email
        busca = request.args.get('busca', '').strip()
        if busca:
            filtro = f'%{busca}%'
            query = query.filter(
                db.or_(
                    Cliente.nome.ilike(filtro),
                    Cliente.telefone.ilike(filtro),
                    Cliente.email.ilike(filtro)
                )
            )

        # Paginação
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = request.args.get('por_pagina', 50, type=int)
        por_pagina = min(por_pagina, 100)  # limite máximo

        total = query.count()
        clientes = query.order_by(Cliente.nome).offset(
            (pagina - 1) * por_pagina
        ).limit(por_pagina).all()

        return jsonify({
            'clientes': [cliente.to_dict() for cliente in clientes],
            'total': total,
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total_paginas': (total + por_pagina - 1) // por_pagina
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/clientes', methods=['POST'])
@limiter.limit("30 per minute")
def criar_cliente():
    """Criar novo cliente"""
    try:
        dados = validar_payload(ClienteCreateSchema)
        
        # Verificar LGPD
        consentimento = dados.get('consentimento_lgpd', False)
        data_consentimento = None
        
        if consentimento:
            data_consentimento = datetime.now(timezone.utc)
        
        # Criar cliente
        cliente = Cliente(
            nome=dados.get('nome'),
            telefone=dados.get('telefone'),
            email=dados.get('email'),
            observacoes=dados.get('observacoes'),
            consentimento_lgpd=consentimento,
            data_consentimento=data_consentimento,
            consentimento_versao=dados.get('versao_politica', 'v1.0') if consentimento else None,
            ativo=True
        )

        db.session.add(cliente)
        db.session.flush()  # gera id_cliente antes do commit

        # Registrar histórico LGPD quando há consentimento
        if consentimento:
            entrada = ConsentimentoHistorico(
                id_cliente=cliente.id_cliente,
                acao='concedeu',
                versao_politica=dados.get('versao_politica', 'v1.0'),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:255]
            )
            db.session.add(entrada)

        db.session.commit()

        return jsonify(cliente.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        if isinstance(e, ValueError):
            return jsonify({'erro': 'Payload invalido', 'detalhes': str(e)}), 400
        return jsonify({'erro': str(e)}), 500


@app.route('/api/clientes/<int:id_cliente>', methods=['GET'])
def obter_cliente(id_cliente):
    """Obter detalhes de um cliente"""
    try:
        cliente = Cliente.query.get(id_cliente)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        # Detalhes com histórico de vendas
        cliente_dict = cliente.to_dict()
        cliente_dict['total_vendas'] = len(cliente.vendas)
        cliente_dict['faturamento_total'] = float(
            sum(v.valor_total for v in cliente.vendas)
        )
        
        return jsonify(cliente_dict)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/clientes/<int:id_cliente>', methods=['PUT'])
def atualizar_cliente(id_cliente):
    """Atualizar dados de um cliente"""
    try:
        cliente = Cliente.query.get(id_cliente)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        dados = request.get_json()
        
        cliente.nome = dados.get('nome', cliente.nome)
        cliente.telefone = dados.get('telefone', cliente.telefone)
        cliente.email = dados.get('email', cliente.email)
        cliente.observacoes = dados.get('observacoes', cliente.observacoes)
        
        db.session.commit()
        
        return jsonify(cliente.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@app.route('/api/clientes/<int:id_cliente>', methods=['DELETE'])
def deletar_cliente(id_cliente):
    """Deletar (anonimizar) um cliente - LGPD"""
    try:
        cliente = Cliente.query.get(id_cliente)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        # Anonimizar ao invés de deletar (LGPD)
        cliente.nome = f'CLIENTE_ANONIMIZADO_{id_cliente}'
        cliente.telefone = None
        cliente.email = None
        cliente.observacoes = None
        cliente.ativo = False
        cliente.data_exclusao = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({'mensagem': 'Cliente anonimizado conforme LGPD'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


# =============================================================================
# ROTAS - LGPD (consentimento e histórico de auditoria)
# =============================================================================

@app.route('/api/clientes/<int:id_cliente>/consentimento', methods=['PUT'])
@limiter.limit("30 per minute")
def atualizar_consentimento(id_cliente):
    """Concede ou revoga consentimento LGPD e registra no histórico de auditoria"""
    try:
        cliente = Cliente.query.get(id_cliente)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        dados = validar_payload(ConsentimentoSchema)
        consentiu = bool(dados.get('consentimento_lgpd'))
        versao = dados.get('versao_politica', 'v1.0')

        cliente.consentimento_lgpd = consentiu
        cliente.consentimento_versao = versao if consentiu else None
        cliente.data_consentimento = datetime.now(timezone.utc) if consentiu else None

        entrada = ConsentimentoHistorico(
            id_cliente=id_cliente,
            acao='concedeu' if consentiu else 'revogou',
            versao_politica=versao,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(entrada)
        db.session.commit()

        return jsonify({
            'mensagem': f'Consentimento {"concedido" if consentiu else "revogado"} com sucesso',
            'cliente': cliente.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        if isinstance(e, ValueError):
            return jsonify({'erro': 'Payload invalido', 'detalhes': str(e)}), 400
        return jsonify({'erro': str(e)}), 500


@app.route('/api/clientes/<int:id_cliente>/consentimento/historico', methods=['GET'])
@limiter.limit("120 per minute")
def historico_consentimento(id_cliente):
    """Retorna histórico completo de auditoria LGPD do cliente"""
    try:
        cliente = Cliente.query.get(id_cliente)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        historico = ConsentimentoHistorico.query.filter_by(
            id_cliente=id_cliente
        ).order_by(ConsentimentoHistorico.data_acao.desc()).all()

        return jsonify({
            'id_cliente': id_cliente,
            'nome': cliente.nome,
            'consentimento_atual': cliente.consentimento_lgpd,
            'versao_atual': cliente.consentimento_versao,
            'historico': [h.to_dict() for h in historico]
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# =============================================================================
# ROTAS - PRODUTOS
# =============================================================================

@app.route('/api/produtos', methods=['GET'])
@limiter.limit("120 per minute")
def listar_produtos():
    """Listar todos os produtos ativos"""
    try:
        produtos = Produto.query.filter_by(ativo=True).all()
        return jsonify([produto.to_dict() for produto in produtos])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/produtos', methods=['POST'])
@limiter.limit("30 per minute")
def criar_produto():
    """Criar novo produto"""
    try:
        dados = validar_payload(ProdutoCreateSchema)
        
        produto = Produto(
            nome_produto=dados.get('nome_produto'),
            categoria=dados.get('categoria'),
            descricao=dados.get('descricao'),
            preco=Decimal(str(dados.get('preco'))),
            ativo=True
        )
        
        db.session.add(produto)
        db.session.commit()
        
        return jsonify(produto.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        if isinstance(e, ValueError):
            return jsonify({'erro': 'Payload invalido', 'detalhes': str(e)}), 400
        return jsonify({'erro': str(e)}), 500


@app.route('/api/produtos/<int:id_produto>', methods=['GET'])
def obter_produto(id_produto):
    """Obter detalhes de um produto"""
    try:
        produto = Produto.query.get(id_produto)
        if not produto:
            return jsonify({'erro': 'Produto não encontrado'}), 404
        return jsonify(produto.to_dict())
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/produtos/<int:id_produto>', methods=['PUT'])
@limiter.limit("30 per minute")
def atualizar_produto(id_produto):
    """Atualizar dados de um produto"""
    try:
        produto = Produto.query.get(id_produto)
        if not produto:
            return jsonify({'erro': 'Produto não encontrado'}), 404

        dados = request.get_json(silent=True) or {}

        if 'nome_produto' in dados and dados['nome_produto']:
            produto.nome_produto = dados['nome_produto']
        if 'categoria' in dados:
            produto.categoria = dados['categoria']
        if 'descricao' in dados:
            produto.descricao = dados['descricao']
        if 'preco' in dados and dados['preco'] is not None:
            produto.preco = Decimal(str(dados['preco']))
        if 'ativo' in dados:
            produto.ativo = bool(dados['ativo'])

        db.session.commit()
        return jsonify(produto.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@app.route('/api/produtos/<int:id_produto>', methods=['DELETE'])
@limiter.limit("30 per minute")
def deletar_produto(id_produto):
    """Desativar produto (soft delete)"""
    try:
        produto = Produto.query.get(id_produto)
        if not produto:
            return jsonify({'erro': 'Produto não encontrado'}), 404

        produto.ativo = False
        db.session.commit()
        return jsonify({'mensagem': f'Produto desativado com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


# =============================================================================
# ROTAS - VENDAS
# =============================================================================

@app.route('/api/vendas', methods=['GET'])
@limiter.limit("120 per minute")
def listar_vendas():
    """Listar todas as vendas"""
    try:
        vendas = Venda.query.order_by(Venda.data_venda.desc()).all()
        return jsonify([venda.to_dict() for venda in vendas])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/vendas', methods=['POST'])
@limiter.limit("40 per minute")
def criar_venda():
    """Criar nova venda"""
    try:
        dados = validar_payload(VendaCreateSchema)

        # Validação complementar de negócio
        if not dados.get('itens') or len(dados['itens']) == 0:
            return jsonify({'erro': 'Venda deve ter pelo menos um item'}), 400
        
        # Verificar se cliente existe
        cliente = Cliente.query.get(dados['id_cliente'])
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # LGPD: bloquear venda sem consentimento
        if not cliente.consentimento_lgpd:
            return jsonify({'erro': 'Venda não permitida: cliente sem consentimento LGPD'}), 400

        # Calcular valor total
        valor_total = Decimal('0.00')
        
        # Criar venda
        venda = Venda(
            id_cliente=dados['id_cliente'],
            forma_pagamento=dados.get('forma_pagamento', 'Dinheiro'),
            status_pagamento='Pendente',
            observacoes=dados.get('observacoes')
        )
        
        # Adicionar itens
        for item_dados in dados['itens']:
            produto = Produto.query.get(item_dados['id_produto'])
            if not produto:
                return jsonify({'erro': f'Produto {item_dados["id_produto"]} não encontrado'}), 404

            # Validar produto ativo
            if not produto.ativo:
                return jsonify({'erro': f'Produto "{produto.nome_produto}" está desativado e não pode ser vendido'}), 400
            
            quantidade = int(item_dados['quantidade'])
            preco_unitario = Decimal(str(produto.preco))
            subtotal = preco_unitario * quantidade
            
            item = ItemVenda(
                id_produto=item_dados['id_produto'],
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                subtotal=subtotal
            )
            venda.itens.append(item)
            valor_total += subtotal

        # Aplicar desconto e taxa
        desconto_perc = Decimal(str(dados.get('desconto_percentual', 0)))
        taxa = Decimal(str(dados.get('taxa', 0)))
        desconto_valor = valor_total * desconto_perc / Decimal('100')
        valor_total = valor_total - desconto_valor + taxa

        venda.valor_total = valor_total
        
        # Criar pagamento
        pagamento = Pagamento(
            valor_pago=valor_total,
            metodo=dados.get('forma_pagamento', 'Dinheiro'),
            status='Concluído'
        )
        venda.pagamento = pagamento
        venda.status_pagamento = 'Concluído'
        
        db.session.add(venda)
        db.session.commit()
        
        return jsonify(venda.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        if isinstance(e, ValueError):
            return jsonify({'erro': 'Payload invalido', 'detalhes': str(e)}), 400
        return jsonify({'erro': str(e)}), 500


@app.route('/api/vendas/<int:id_venda>', methods=['GET'])
def obter_venda(id_venda):
    """Obter detalhes de uma venda"""
    try:
        venda = Venda.query.get(id_venda)
        if not venda:
            return jsonify({'erro': 'Venda não encontrada'}), 404
        
        return jsonify(venda.to_dict())
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# =============================================================================
# ROTAS - RELATÓRIOS
# =============================================================================

@app.route('/api/relatorios/dia-atual', methods=['GET'])
def relatorio_dia_atual():
    """Relatório de vendas do dia atual"""
    try:
        hoje = datetime.now(timezone.utc).date()
        
        vendas_hoje = Venda.query.filter(
            db.func.date(Venda.data_venda) == hoje
        ).all()
        
        total_vendas = len(vendas_hoje)
        faturamento = sum(v.valor_total for v in vendas_hoje)
        
        # Por forma de pagamento
        por_forma = {}
        for venda in vendas_hoje:
            forma = venda.forma_pagamento or 'Indefinido'
            if forma not in por_forma:
                por_forma[forma] = Decimal('0.00')
            por_forma[forma] += venda.valor_total
        
        return jsonify({
            'data': hoje.isoformat(),
            'total_vendas': total_vendas,
            'faturamento_total': float(faturamento),
            'por_forma_pagamento': {k: float(v) for k, v in por_forma.items()},
            'ticket_medio': float(faturamento / total_vendas) if total_vendas > 0 else 0
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/relatorios/por-data', methods=['GET'])
def relatorio_por_data():
    """Relatório de vendas filtrado por data (YYYY-MM-DD)"""
    try:
        data_str = request.args.get('data', '')
        if not data_str:
            return jsonify({'erro': 'Parâmetro "data" é obrigatório (formato YYYY-MM-DD)'}), 400

        from datetime import date as date_type
        try:
            data_filtro = date_type.fromisoformat(data_str)
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

        vendas_dia = Venda.query.filter(
            db.func.date(Venda.data_venda) == data_filtro
        ).all()

        total_vendas = len(vendas_dia)
        faturamento = sum(v.valor_total for v in vendas_dia)

        por_forma = {}
        for venda in vendas_dia:
            forma = venda.forma_pagamento or 'Indefinido'
            if forma not in por_forma:
                por_forma[forma] = {'quantidade': 0, 'total': Decimal('0.00')}
            por_forma[forma]['quantidade'] += 1
            por_forma[forma]['total'] += venda.valor_total

        return jsonify({
            'data': data_filtro.isoformat(),
            'total_vendas': total_vendas,
            'faturamento_total': float(faturamento),
            'por_forma_pagamento': {
                k: {'quantidade': v['quantidade'], 'total': float(v['total'])}
                for k, v in por_forma.items()
            },
            'ticket_medio': float(faturamento / total_vendas) if total_vendas > 0 else 0,
            'vendas': [v.to_dict() for v in vendas_dia]
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/relatorios/clientes-frequentes', methods=['GET'])
def relatorio_clientes_frequentes():
    """Clientes mais frequentes (últimos 30 dias)"""
    try:
        data_limite = datetime.now(timezone.utc) - timedelta(days=30)
        
        clientes_freq = db.session.query(
            Cliente.id_cliente,
            Cliente.nome,
            Cliente.telefone,
            db.func.count(Venda.id_venda).label('total_compras'),
            db.func.sum(Venda.valor_total).label('faturamento'),
            db.func.max(Venda.data_venda).label('ultima_compra')
        ).join(Venda).filter(
            Venda.data_venda >= data_limite,
            Cliente.ativo == True
        ).group_by(
            Cliente.id_cliente,
            Cliente.nome,
            Cliente.telefone
        ).order_by(
            db.func.count(Venda.id_venda).desc()
        ).limit(10).all()
        
        resultado = []
        for cliente in clientes_freq:
            resultado.append({
                'id_cliente': cliente.id_cliente,
                'nome': cliente.nome,
                'telefone': cliente.telefone,
                'total_compras': cliente.total_compras,
                'faturamento': float(cliente.faturamento),
                'ultima_compra': cliente.ultima_compra.isoformat() if cliente.ultima_compra else None
            })
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/relatorios/produtos-ranking', methods=['GET'])
def relatorio_produtos_ranking():
    """Produtos mais vendidos"""
    try:
        produtos_rank = db.session.query(
            Produto.id_produto,
            Produto.nome_produto,
            db.func.count(ItemVenda.id_item).label('quantidade'),
            db.func.sum(ItemVenda.subtotal).label('faturamento')
        ).join(ItemVenda).filter(
            Produto.ativo == True
        ).group_by(
            Produto.id_produto,
            Produto.nome_produto
        ).order_by(
            db.func.count(ItemVenda.id_item).desc()
        ).limit(15).all()
        
        resultado = []
        for produto in produtos_rank:
            resultado.append({
                'id_produto': produto.id_produto,
                'nome_produto': produto.nome_produto,
                'quantidade_vendida': produto.quantidade,
                'faturamento': float(produto.faturamento)
            })
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# =============================================================================
# ROTAS - EXPORTAÇÃO
# =============================================================================

@app.route('/api/exportar/clientes-csv', methods=['GET'])
def exportar_clientes_csv():
    """Exportar lista de clientes em CSV"""
    try:
        clientes = Cliente.query.filter_by(ativo=True, consentimento_lgpd=True).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Nome', 'Telefone', 'Email', 'Data de Cadastro'])
        
        for cliente in clientes:
            writer.writerow([
                cliente.nome,
                cliente.telefone or '',
                cliente.email or '',
                cliente.data_cadastro.strftime('%Y-%m-%d') if cliente.data_cadastro else ''
            ])
        
        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)
        
        return send_file(
            bytes_output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'clientes_export_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# =============================================================================
# PÁGINAS HTML
# =============================================================================

@app.route('/cadastro-cliente')
@login_required
def pagina_cadastro_cliente():
    """Página de cadastro de cliente"""
    return render_template('cadastro_cliente.html')


@app.route('/nova-venda')
@login_required
def pagina_nova_venda():
    """Página de registro de venda"""
    return render_template('venda.html')


@app.route('/relatorios')
@login_required
def pagina_relatorios():
    """Página de relatórios"""
    return render_template('relatorios.html')


@app.route('/clientes')
@login_required
def pagina_clientes():
    """Página de gerenciamento de clientes"""
    return render_template('clientes.html')


@app.route('/produtos')
@login_required
def pagina_produtos():
    """Página de gerenciamento de produtos"""
    return render_template('produtos.html')


@app.route('/fechamento')
@login_required
def pagina_fechamento():
    """Página de fechamento diário"""
    return render_template('fechamento.html')


@app.route('/politica-privacidade')
def politica_privacidade():
    """Página com política de privacidade LGPD"""
    return render_template('politica_privacidade.html')


# =============================================================================
# TRATAMENTO DE ERROS
# =============================================================================

@app.errorhandler(404)
def nao_encontrado(erro):
    return jsonify({'erro': 'Endpoint não encontrado'}), 404


@app.errorhandler(500)
def erro_interno(erro):
    return jsonify({'erro': 'Erro interno do servidor'}), 500


# =============================================================================
# CRIAR TABELAS (usado pelo gunicorn na nuvem)
# =============================================================================

with app.app_context():
    db.create_all()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
