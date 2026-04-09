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
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
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
    nome = db.Column(db.String(150), nullable=False, index=True)
    telefone = db.Column(db.String(20), index=True)
    email = db.Column(db.String(100), index=True)
    senha_hash = db.Column(db.String(256), nullable=True)
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

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        if not self.senha_hash:
            return False
        return check_password_hash(self.senha_hash, senha)

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
    nome_produto = db.Column(db.String(100), nullable=False, index=True)
    categoria = db.Column(db.String(50), index=True)
    descricao = db.Column(db.Text)
    preco = db.Column(db.DECIMAL(10, 2), nullable=False)
    volume = db.Column(db.String(20))  # "10L", "5L" — recipiente
    estoque_atual = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=0)
    preco_promocional = db.Column(db.DECIMAL(10, 2), nullable=True)
    ativo = db.Column(db.Boolean, default=True, index=True)
    foto_url = db.Column(db.String(500), nullable=True)
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
            "volume": self.volume,
            "estoque_atual": self.estoque_atual,
            "estoque_minimo": self.estoque_minimo,
            "preco_promocional": (
                float(self.preco_promocional)
                if self.preco_promocional
                else None
            ),
            "foto_url": self.foto_url,
            "ativo": self.ativo,
        }


class Complemento(db.Model):
    """Modelo de Complemento/Topping para self-service"""

    __tablename__ = "complemento"

    id_complemento = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50))  # Fruta, Calda, Farináceo, Extra
    unidade_medida = db.Column(db.String(30))  # g, ml, unidade
    preco_adicional = db.Column(db.DECIMAL(10, 2), default=0)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f"<Complemento {self.nome}>"

    def to_dict(self):
        return {
            "id_complemento": self.id_complemento,
            "nome": self.nome,
            "categoria": self.categoria,
            "unidade_medida": self.unidade_medida,
            "preco_adicional": (
                float(self.preco_adicional)
                if self.preco_adicional
                else 0
            ),
            "ativo": self.ativo,
        }


class Venda(db.Model):
    """Modelo de Venda"""

    __tablename__ = "venda"
    __table_args__ = (
        db.Index('ix_venda_data_status', 'data_venda', 'status_pagamento'),
    )

    id_venda = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(
        db.Integer, db.ForeignKey("cliente.id_cliente"), nullable=False,
        index=True,
    )
    data_venda = db.Column(db.DateTime, default=_utcnow, index=True)
    valor_total = db.Column(db.DECIMAL(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50))
    status_pagamento = db.Column(db.String(50), default="Pendente")
    status_pedido = db.Column(
        db.String(30), default="Recebido"
    )  # Recebido | Preparando | Pronto | Entregue | Cancelado
    observacoes = db.Column(db.Text)
    motivo_cancelamento = db.Column(db.Text)
    desconto_aplicado = db.Column(
        db.DECIMAL(10, 2), default=0
    )  # valor total de desconto aplicado (R$)
    data_agendamento = db.Column(db.DateTime, nullable=True)
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
            "desconto_aplicado": float(self.desconto_aplicado or 0),
            "forma_pagamento": self.forma_pagamento,
            "status_pagamento": self.status_pagamento,
            "status_pedido": self.status_pedido or "Recebido",
            "itens": [item.to_dict() for item in self.itens],
            "observacoes": self.observacoes,
            "motivo_cancelamento": self.motivo_cancelamento,
        }


class ItemVenda(db.Model):
    """Modelo de Item da Venda"""

    __tablename__ = "item_venda"

    id_item = db.Column(db.Integer, primary_key=True)
    id_venda = db.Column(
        db.Integer, db.ForeignKey("venda.id_venda"), nullable=False,
        index=True,
    )
    id_produto = db.Column(
        db.Integer, db.ForeignKey("produto.id_produto"), nullable=False,
        index=True,
    )
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.DECIMAL(10, 2), nullable=False)
    subtotal = db.Column(db.DECIMAL(10, 2), nullable=False)

    # Relacionamento com complementos do item
    complementos = db.relationship(
        "ItemVendaComplemento", backref="item_venda",
        lazy=True, cascade="all, delete-orphan",
    )

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
            "complementos": [c.to_dict() for c in self.complementos],
        }


class ItemVendaComplemento(db.Model):
    """Complemento/topping associado a um item de venda."""

    __tablename__ = "item_venda_complemento"

    id = db.Column(db.Integer, primary_key=True)
    id_item = db.Column(
        db.Integer, db.ForeignKey("item_venda.id_item"),
        nullable=False, index=True,
    )
    id_complemento = db.Column(
        db.Integer, db.ForeignKey("complemento.id_complemento"),
        nullable=False, index=True,
    )
    preco_unitario = db.Column(db.DECIMAL(10, 2), default=0)

    complemento = db.relationship("Complemento", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "id_complemento": self.id_complemento,
            "nome": (
                self.complemento.nome if self.complemento else None
            ),
            "categoria": (
                self.complemento.categoria
                if self.complemento else None
            ),
            "preco_unitario": float(
                self.preco_unitario or 0
            ),
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
    __table_args__ = (
        db.Index('ix_log_data_entidade', 'data_hora', 'entidade'),
    )

    id_log = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey(
            "usuario.id_usuario", ondelete="SET NULL"
        ), nullable=True
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


# =============================================================================
# FORNECEDOR & COMPRAS DE ESTOQUE
# =============================================================================


class Fornecedor(db.Model):
    """Fornecedor de insumos/produtos da açaiteria."""

    __tablename__ = "fornecedor"

    id_fornecedor = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18), unique=True)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    endereco = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=_utcnow)

    compras = db.relationship(
        "CompraEstoque", backref="fornecedor", lazy=True
    )

    def to_dict(self):
        return {
            "id_fornecedor": self.id_fornecedor,
            "nome": self.nome,
            "cnpj": self.cnpj,
            "telefone": self.telefone,
            "email": self.email,
            "endereco": self.endereco,
            "observacoes": self.observacoes,
            "ativo": self.ativo,
            "data_criacao": (
                self.data_criacao.isoformat() if self.data_criacao else None
            ),
        }


class CompraEstoque(db.Model):
    """Registro de compra de estoque (reposição de insumos)."""

    __tablename__ = "compra_estoque"

    id_compra = db.Column(db.Integer, primary_key=True)
    id_fornecedor = db.Column(
        db.Integer, db.ForeignKey("fornecedor.id_fornecedor"), nullable=False,
        index=True,
    )
    data_compra = db.Column(db.DateTime, default=_utcnow, index=True)
    valor_total = db.Column(db.DECIMAL(10, 2), nullable=False, default=0)
    nota_fiscal = db.Column(db.String(50))
    status = db.Column(
        db.String(30), default="Pendente"
    )  # Pendente | Recebido | Cancelado
    observacoes = db.Column(db.Text)
    data_atualizacao = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )

    itens = db.relationship(
        "ItemCompra", backref="compra", lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id_compra": self.id_compra,
            "id_fornecedor": self.id_fornecedor,
            "fornecedor_nome": (
                self.fornecedor.nome if self.fornecedor else None
            ),
            "data_compra": (
                self.data_compra.isoformat() if self.data_compra else None
            ),
            "valor_total": float(self.valor_total),
            "nota_fiscal": self.nota_fiscal,
            "status": self.status,
            "observacoes": self.observacoes,
            "itens": [i.to_dict() for i in self.itens],
        }


class ItemCompra(db.Model):
    """Item individual de uma compra de estoque."""

    __tablename__ = "item_compra"

    id_item = db.Column(db.Integer, primary_key=True)
    id_compra = db.Column(
        db.Integer, db.ForeignKey("compra_estoque.id_compra"), nullable=False,
        index=True,
    )
    id_produto = db.Column(
        db.Integer, db.ForeignKey("produto.id_produto"), nullable=False,
    )
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.DECIMAL(10, 2), nullable=False)
    subtotal = db.Column(db.DECIMAL(10, 2), nullable=False)

    produto = db.relationship("Produto", lazy=True)

    def to_dict(self):
        return {
            "id_item": self.id_item,
            "id_compra": self.id_compra,
            "id_produto": self.id_produto,
            "produto_nome": (
                self.produto.nome_produto if self.produto else None
            ),
            "quantidade": self.quantidade,
            "preco_unitario": float(self.preco_unitario),
            "subtotal": float(self.subtotal),
        }


# =============================================================================
# CUPONS DE DESCONTO
# =============================================================================


class CupomDesconto(db.Model):
    """Cupom de desconto para promoções e campanhas."""

    __tablename__ = "cupom_desconto"

    id_cupom = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(
        db.String(30), unique=True, nullable=False, index=True
    )
    descricao = db.Column(db.String(200))
    tipo_desconto = db.Column(
        db.String(20), nullable=False, default="percentual"
    )  # percentual | fixo
    valor_desconto = db.Column(db.DECIMAL(10, 2), nullable=False)
    valor_minimo_pedido = db.Column(db.DECIMAL(10, 2), default=0)
    usos_maximos = db.Column(db.Integer, default=0)  # 0 = ilimitado
    usos_realizados = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    data_inicio = db.Column(db.DateTime, default=_utcnow)
    data_fim = db.Column(db.DateTime, nullable=True)
    data_criacao = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id_cupom": self.id_cupom,
            "codigo": self.codigo,
            "descricao": self.descricao,
            "tipo_desconto": self.tipo_desconto,
            "valor_desconto": float(self.valor_desconto),
            "valor_minimo_pedido": float(
                self.valor_minimo_pedido or 0
            ),
            "usos_maximos": self.usos_maximos,
            "usos_realizados": self.usos_realizados,
            "ativo": self.ativo,
            "data_inicio": (
                self.data_inicio.isoformat() if self.data_inicio else None
            ),
            "data_fim": (
                self.data_fim.isoformat() if self.data_fim else None
            ),
        }

    @property
    def valido(self):
        """Verifica se o cupom está válido para uso."""
        if not self.ativo:
            return False
        agora = _utcnow()
        # Normalizar para comparação: se campo não tem tz, adicionar UTC
        if self.data_inicio:
            di = self.data_inicio if self.data_inicio.tzinfo else self.data_inicio.replace(tzinfo=timezone.utc)
            if agora < di:
                return False
        if self.data_fim:
            df = self.data_fim if self.data_fim.tzinfo else self.data_fim.replace(tzinfo=timezone.utc)
            if agora > df:
                return False
        if self.usos_maximos > 0 and self.usos_realizados >= self.usos_maximos:
            return False
        return True


# =============================================================================
# BADGES / GAMIFICAÇÃO
# =============================================================================


class BadgeCliente(db.Model):
    """Badge conquistado por um cliente (gamificação)."""

    __tablename__ = "badge_cliente"

    id_badge = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(
        db.Integer, db.ForeignKey("cliente.id_cliente"),
        nullable=False, index=True,
    )
    codigo = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200))
    icone = db.Column(db.String(10), default="🏅")
    data_conquista = db.Column(db.DateTime, default=_utcnow)

    cliente = db.relationship(
        "Cliente", backref=db.backref("badges", lazy=True)
    )

    def to_dict(self):
        return {
            "id_badge": self.id_badge,
            "id_cliente": self.id_cliente,
            "codigo": self.codigo,
            "nome": self.nome,
            "descricao": self.descricao,
            "icone": self.icone,
            "data_conquista": (
                self.data_conquista.isoformat()
                if self.data_conquista
                else None
            ),
        }


# =============================================================================
# LANÇAMENTOS FINANCEIROS (receitas / despesas manuais)
# =============================================================================


class LancamentoFinanceiro(db.Model):
    """Lançamento financeiro manual (receita ou despesa)."""

    __tablename__ = "lancamento_financeiro"
    __table_args__ = (
        db.Index('ix_lanc_data_tipo', 'data_lancamento', 'tipo'),
    )

    id_lancamento = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(
        db.String(20), nullable=False, index=True
    )  # receita | despesa
    categoria = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(300))
    valor = db.Column(db.DECIMAL(10, 2), nullable=False)
    data_lancamento = db.Column(db.Date, nullable=False, index=True)
    forma_pagamento = db.Column(db.String(50))
    status = db.Column(
        db.String(30), default="Pago"
    )  # Pago | Pendente | Cancelado
    comprovante = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario")
    )
    data_criacao = db.Column(db.DateTime, default=_utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )

    usuario = db.relationship("Usuario", lazy=True)

    def to_dict(self):
        return {
            "id_lancamento": self.id_lancamento,
            "tipo": self.tipo,
            "categoria": self.categoria,
            "descricao": self.descricao,
            "valor": float(self.valor),
            "data_lancamento": (
                self.data_lancamento.isoformat()
                if self.data_lancamento
                else None
            ),
            "forma_pagamento": self.forma_pagamento,
            "status": self.status,
            "comprovante": self.comprovante,
            "observacoes": self.observacoes,
            "usuario_nome": (
                self.usuario.nome if self.usuario else None
            ),
            "data_criacao": (
                self.data_criacao.isoformat()
                if self.data_criacao
                else None
            ),
        }


# =============================================================================
# 2FA — TWO-FACTOR AUTHENTICATION
# =============================================================================


class TwoFactorSecret(db.Model):
    """Segredo TOTP para autenticação em dois fatores (admin)."""

    __tablename__ = "two_factor_secret"

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"),
        nullable=False, unique=True,
    )
    secret = db.Column(db.String(32), nullable=False)
    ativo = db.Column(db.Boolean, default=False)
    data_ativacao = db.Column(db.DateTime)

    usuario = db.relationship(
        "Usuario", backref=db.backref("two_factor", uselist=False, lazy=True)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "id_usuario": self.id_usuario,
            "ativo": self.ativo,
            "data_ativacao": (
                self.data_ativacao.isoformat()
                if self.data_ativacao else None
            ),
        }


# =============================================================================
# COMBOS / KITS — Agrupamento de produtos com preço especial
# =============================================================================


class ComboKit(db.Model):
    """Combo/Kit de produtos com preço promocional."""

    __tablename__ = "combo_kit"

    id_combo = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    preco_combo = db.Column(db.DECIMAL(10, 2), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=_utcnow)

    itens = db.relationship(
        "ComboKitItem", backref="combo", lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        preco_individual = sum(
            float(i.produto.preco) * i.quantidade
            for i in self.itens if i.produto
        )
        return {
            "id_combo": self.id_combo,
            "nome": self.nome,
            "descricao": self.descricao,
            "preco_combo": float(self.preco_combo),
            "preco_individual": round(preco_individual, 2),
            "economia": round(preco_individual - float(self.preco_combo), 2),
            "ativo": self.ativo,
            "itens": [i.to_dict() for i in self.itens],
        }


class ComboKitItem(db.Model):
    """Item individual de um combo/kit."""

    __tablename__ = "combo_kit_item"

    id = db.Column(db.Integer, primary_key=True)
    id_combo = db.Column(
        db.Integer, db.ForeignKey("combo_kit.id_combo"), nullable=False
    )
    id_produto = db.Column(
        db.Integer, db.ForeignKey("produto.id_produto"), nullable=False
    )
    quantidade = db.Column(db.Integer, default=1)

    produto = db.relationship("Produto", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "id_produto": self.id_produto,
            "produto_nome": (
                self.produto.nome_produto if self.produto else None
            ),
            "quantidade": self.quantidade,
            "preco_unitario": (
                float(self.produto.preco) if self.produto else 0
            ),
        }


# =============================================================================
# PROGRAMA DE INDICAÇÃO
# =============================================================================


class Indicacao(db.Model):
    """Registro de indicação entre clientes (programa de referral)."""

    __tablename__ = "indicacao"

    id_indicacao = db.Column(db.Integer, primary_key=True)
    id_cliente_indicador = db.Column(
        db.Integer, db.ForeignKey("cliente.id_cliente"), nullable=False
    )
    id_cliente_indicado = db.Column(
        db.Integer, db.ForeignKey("cliente.id_cliente"), nullable=True
    )
    codigo_indicacao = db.Column(
        db.String(20), nullable=False, index=True
    )
    bonus_concedido = db.Column(db.Boolean, default=False)
    data_indicacao = db.Column(db.DateTime, default=_utcnow)

    indicador = db.relationship(
        "Cliente", foreign_keys=[id_cliente_indicador],
        backref="indicacoes_feitas",
    )
    indicado = db.relationship(
        "Cliente", foreign_keys=[id_cliente_indicado],
        backref="indicacao_recebida",
    )

    def to_dict(self):
        return {
            "id_indicacao": self.id_indicacao,
            "indicador_nome": (
                self.indicador.nome if self.indicador else None
            ),
            "indicado_nome": (
                self.indicado.nome if self.indicado else None
            ),
            "codigo_indicacao": self.codigo_indicacao,
            "bonus_concedido": self.bonus_concedido,
            "data_indicacao": (
                self.data_indicacao.isoformat()
                if self.data_indicacao else None
            ),
        }


# =============================================================================
# ASSINATURAS / PLANOS MENSAIS
# =============================================================================


class Assinatura(db.Model):
    """Plano de assinatura mensal (ex: 10 açaís/mês)."""

    __tablename__ = "assinatura"

    id_assinatura = db.Column(db.Integer, primary_key=True)
    nome_plano = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco_mensal = db.Column(db.DECIMAL(10, 2), nullable=False)
    limite_usos = db.Column(db.Integer, default=10)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=_utcnow)

    clientes = db.relationship(
        "AssinaturaCliente", backref="assinatura", lazy=True
    )

    def to_dict(self):
        return {
            "id_assinatura": self.id_assinatura,
            "nome_plano": self.nome_plano,
            "descricao": self.descricao,
            "preco_mensal": float(self.preco_mensal),
            "limite_usos": self.limite_usos,
            "ativo": self.ativo,
        }


class AssinaturaCliente(db.Model):
    """Vínculo de assinatura ativa de um cliente."""

    __tablename__ = "assinatura_cliente"

    id = db.Column(db.Integer, primary_key=True)
    id_assinatura = db.Column(
        db.Integer, db.ForeignKey("assinatura.id_assinatura"), nullable=False
    )
    id_cliente = db.Column(
        db.Integer, db.ForeignKey("cliente.id_cliente"), nullable=False
    )
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    usos_realizados = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="ativa")
    data_criacao = db.Column(db.DateTime, default=_utcnow)

    cliente = db.relationship("Cliente", backref="assinaturas")

    @property
    def usos_restantes(self):
        if not self.assinatura:
            return 0
        return max(0, self.assinatura.limite_usos - self.usos_realizados)

    def to_dict(self):
        return {
            "id": self.id,
            "plano": (
                self.assinatura.nome_plano if self.assinatura else None
            ),
            "cliente_nome": (
                self.cliente.nome if self.cliente else None
            ),
            "data_inicio": (
                self.data_inicio.isoformat()
                if self.data_inicio else None
            ),
            "data_fim": (
                self.data_fim.isoformat() if self.data_fim else None
            ),
            "usos_realizados": self.usos_realizados,
            "usos_restantes": self.usos_restantes,
            "status": self.status,
        }


# =============================================================================
# WEBHOOK CONFIG — Notificação de eventos para sistemas externos
# =============================================================================


class WebhookConfig(db.Model):
    """Configuração de webhook para eventos do sistema."""

    __tablename__ = "webhook_config"

    id_webhook = db.Column(db.Integer, primary_key=True)
    evento = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    secret = db.Column(db.String(64))
    data_criacao = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id_webhook": self.id_webhook,
            "evento": self.evento,
            "url": self.url,
            "ativo": self.ativo,
            "data_criacao": (
                self.data_criacao.isoformat()
                if self.data_criacao else None
            ),
        }


# =============================================================================
# MULTI-LOJA — Suporte a múltiplas unidades
# =============================================================================


class Loja(db.Model):
    """Unidade/filial da açaiteria."""

    __tablename__ = "loja"

    id_loja = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    endereco = db.Column(db.Text)
    telefone = db.Column(db.String(20))
    cnpj = db.Column(db.String(18))
    ativa = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id_loja": self.id_loja,
            "nome": self.nome,
            "endereco": self.endereco,
            "telefone": self.telefone,
            "cnpj": self.cnpj,
            "ativa": self.ativa,
        }
