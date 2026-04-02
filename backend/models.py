"""
Configuração do banco de dados para Flask-SQLAlchemy
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def _utcnow():
    return datetime.now(timezone.utc)


# =============================================================================
# MODELOS DE DADOS
# =============================================================================


class Usuario(db.Model):
    """Modelo de Usuário do sistema (admin ou operador)"""

    __tablename__ = "usuario"

    id_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    papel = db.Column(
        db.String(20), nullable=False, default="operador"
    )  # 'admin' | 'operador'
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=_utcnow)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "nome": self.nome,
            "email": self.email,
            "papel": self.papel,
            "ativo": self.ativo,
            "data_criacao": (
                self.data_criacao.isoformat() if self.data_criacao else None
            ),
        }

    def __repr__(self):
        return f"<Usuario {self.email} ({self.papel})>"


class Cliente(db.Model):
    """Modelo de Cliente"""

    __tablename__ = "cliente"

    id_cliente = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    data_cadastro = db.Column(db.DateTime, default=_utcnow)
    observacoes = db.Column(db.Text)
    consentimento_lgpd = db.Column(db.Boolean, default=False)
    data_consentimento = db.Column(db.DateTime)
    consentimento_versao = db.Column(db.String(20), nullable=True)
    data_exclusao = db.Column(db.DateTime, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    pontos_fidelidade = db.Column(db.Integer, default=0)

    # Relacionamentos
    vendas = db.relationship(
        "Venda", backref="cliente", lazy=True, cascade="all, delete-orphan"
    )
    historico_consentimento = db.relationship(
        "ConsentimentoHistorico", backref="cliente_hist", lazy=True
    )

    def __repr__(self):
        return f"<Cliente {self.nome}>"

    def to_dict(self):
        return {
            "id_cliente": self.id_cliente,
            "nome": self.nome,
            "telefone": self.telefone,
            "email": self.email,
            "data_cadastro": (
                self.data_cadastro.isoformat() if self.data_cadastro else None
            ),
            "observacoes": self.observacoes,
            "consentimento_lgpd": self.consentimento_lgpd,
            "consentimento_versao": self.consentimento_versao,
            "data_consentimento": (
                self.data_consentimento.isoformat()
                if self.data_consentimento
                else None
            ),
            "ativo": self.ativo,
            "pontos_fidelidade": self.pontos_fidelidade or 0,
        }


class ConsentimentoHistorico(db.Model):
    """Auditoria de consentimento LGPD."""

    __tablename__ = "consentimento_historico"

    id = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(
        db.Integer, db.ForeignKey("cliente.id_cliente"), nullable=False
    )
    acao = db.Column(db.String(20), nullable=False)  # 'concedeu' | 'revogou'
    versao_politica = db.Column(db.String(20), nullable=False, default="v1.0")
    data_acao = db.Column(db.DateTime, default=_utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "id_cliente": self.id_cliente,
            "acao": self.acao,
            "versao_politica": self.versao_politica,
            "data_acao": (
                self.data_acao.isoformat() if self.data_acao else None
            ),
            "ip_address": self.ip_address,
        }


class Produto(db.Model):
    """Modelo de Produto/Sabor"""

    __tablename__ = "produto"

    id_produto = db.Column(db.Integer, primary_key=True)
    nome_produto = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50))
    descricao = db.Column(db.Text)
    preco = db.Column(db.DECIMAL(10, 2), nullable=False)
    estoque_atual = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=_utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )

    # Relacionamento
    itens_venda = db.relationship("ItemVenda", backref="produto", lazy=True)

    def __repr__(self):
        return f"<Produto {self.nome_produto}>"

    def to_dict(self):
        return {
            "id_produto": self.id_produto,
            "nome_produto": self.nome_produto,
            "categoria": self.categoria,
            "descricao": self.descricao,
            "preco": float(self.preco),
            "estoque_atual": self.estoque_atual,
            "estoque_minimo": self.estoque_minimo,
            "ativo": self.ativo,
        }


class Venda(db.Model):
    """Modelo de Venda"""

    __tablename__ = "venda"

    id_venda = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(
        db.Integer, db.ForeignKey("cliente.id_cliente"), nullable=False
    )
    data_venda = db.Column(db.DateTime, default=_utcnow)
    valor_total = db.Column(db.DECIMAL(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50))
    status_pagamento = db.Column(db.String(50), default="Pendente")
    observacoes = db.Column(db.Text)
    recibo_gerado = db.Column(db.Boolean, default=False)
    data_atualizacao = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )

    # Relacionamentos
    itens = db.relationship(
        "ItemVenda", backref="venda", lazy=True, cascade="all, delete-orphan"
    )
    pagamento = db.relationship(
        "Pagamento",
        backref="venda",
        lazy=True,
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Venda {self.id_venda}>"

    def to_dict(self):
        return {
            "id_venda": self.id_venda,
            "id_cliente": self.id_cliente,
            "cliente_nome": self.cliente.nome if self.cliente else None,
            "data_venda": (
                self.data_venda.isoformat() if self.data_venda else None
            ),
            "valor_total": float(self.valor_total),
            "forma_pagamento": self.forma_pagamento,
            "status_pagamento": self.status_pagamento,
            "itens": [item.to_dict() for item in self.itens],
            "observacoes": self.observacoes,
        }


class ItemVenda(db.Model):
    """Modelo de Item da Venda"""

    __tablename__ = "item_venda"

    id_item = db.Column(db.Integer, primary_key=True)
    id_venda = db.Column(
        db.Integer, db.ForeignKey("venda.id_venda"), nullable=False
    )
    id_produto = db.Column(
        db.Integer, db.ForeignKey("produto.id_produto"), nullable=False
    )
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.DECIMAL(10, 2), nullable=False)
    subtotal = db.Column(db.DECIMAL(10, 2), nullable=False)

    def __repr__(self):
        return f"<ItemVenda {self.id_item}>"

    def to_dict(self):
        return {
            "id_item": self.id_item,
            "id_venda": self.id_venda,
            "id_produto": self.id_produto,
            "produto_nome": (
                self.produto.nome_produto if self.produto else None
            ),
            "quantidade": self.quantidade,
            "preco_unitario": float(self.preco_unitario),
            "subtotal": float(self.subtotal),
        }


class Pagamento(db.Model):
    """Modelo de Pagamento"""

    __tablename__ = "pagamento"

    id_pagamento = db.Column(db.Integer, primary_key=True)
    id_venda = db.Column(
        db.Integer, db.ForeignKey("venda.id_venda"), nullable=False
    )
    data_pagamento = db.Column(db.DateTime, default=_utcnow)
    valor_pago = db.Column(db.DECIMAL(10, 2), nullable=False)
    metodo = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="Concluído")
    referencia_transacao = db.Column(db.String(100))
    notas = db.Column(db.Text)

    def __repr__(self):
        return f"<Pagamento {self.id_pagamento}>"

    def to_dict(self):
        return {
            "id_pagamento": self.id_pagamento,
            "id_venda": self.id_venda,
            "data_pagamento": (
                self.data_pagamento.isoformat()
                if self.data_pagamento
                else None
            ),
            "valor_pago": float(self.valor_pago),
            "metodo": self.metodo,
            "status": self.status,
            "referencia_transacao": self.referencia_transacao,
        }


class LogAcao(db.Model):
    """Modelo de Histórico/Audit Log de ações do sistema"""

    __tablename__ = "log_acao"

    id_log = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=True
    )
    acao = db.Column(
        db.String(50), nullable=False
    )  # 'criar', 'editar', 'excluir', 'login', 'logout'
    entidade = db.Column(
        db.String(50), nullable=False
    )  # 'cliente', 'produto', 'venda', 'usuario'
    id_entidade = db.Column(db.Integer)
    detalhes = db.Column(db.Text)
    ip = db.Column(db.String(45))
    data_hora = db.Column(db.DateTime, default=_utcnow)

    usuario = db.relationship("Usuario", backref="logs", lazy=True)

    def to_dict(self):
        return {
            "id_log": self.id_log,
            "id_usuario": self.id_usuario,
            "usuario_nome": self.usuario.nome if self.usuario else None,
            "acao": self.acao,
            "entidade": self.entidade,
            "id_entidade": self.id_entidade,
            "detalhes": self.detalhes,
            "ip": self.ip,
            "data_hora": (
                self.data_hora.isoformat() if self.data_hora else None
            ),
        }


class TicketSuporte(db.Model):
    """Ticket de suporte — dúvidas, problemas, contato com admin/operador"""

    __tablename__ = "ticket_suporte"

    id_ticket = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    assunto = db.Column(db.String(200), nullable=False)
    categoria = db.Column(
        db.String(50), nullable=False, default="duvida"
    )  # 'duvida' | 'problema' | 'sugestao' | 'outro'
    status = db.Column(
        db.String(20), nullable=False, default="aberto"
    )  # 'aberto' | 'em_andamento' | 'resolvido' | 'fechado'
    prioridade = db.Column(
        db.String(20), nullable=False, default="normal"
    )  # 'baixa' | 'normal' | 'alta' | 'urgente'
    data_criacao = db.Column(db.DateTime, default=_utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )

    criador = db.relationship("Usuario", backref="tickets_criados", lazy=True)
    mensagens = db.relationship(
        "MensagemTicket",
        backref="ticket",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="MensagemTicket.data_envio",
    )

    def to_dict(self):
        return {
            "id_ticket": self.id_ticket,
            "id_usuario": self.id_usuario,
            "criador_nome": self.criador.nome if self.criador else None,
            "assunto": self.assunto,
            "categoria": self.categoria,
            "status": self.status,
            "prioridade": self.prioridade,
            "data_criacao": (
                self.data_criacao.isoformat() if self.data_criacao else None
            ),
            "data_atualizacao": (
                self.data_atualizacao.isoformat()
                if self.data_atualizacao
                else None
            ),
            "mensagens": [m.to_dict() for m in self.mensagens],
            "total_mensagens": len(self.mensagens),
        }


class MensagemTicket(db.Model):
    """Mensagem dentro de um ticket de suporte (chat)"""

    __tablename__ = "mensagem_ticket"

    id_mensagem = db.Column(db.Integer, primary_key=True)
    id_ticket = db.Column(
        db.Integer, db.ForeignKey("ticket_suporte.id_ticket"), nullable=False
    )
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    conteudo = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, default=_utcnow)

    autor = db.relationship("Usuario", lazy=True)

    def to_dict(self):
        return {
            "id_mensagem": self.id_mensagem,
            "id_ticket": self.id_ticket,
            "id_usuario": self.id_usuario,
            "autor_nome": self.autor.nome if self.autor else None,
            "autor_papel": self.autor.papel if self.autor else None,
            "conteudo": self.conteudo,
            "data_envio": (
                self.data_envio.isoformat() if self.data_envio else None
            ),
        }
