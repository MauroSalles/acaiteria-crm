/**
 * Script Principal - Açaiteria CRM
 * Funções auxiliares e gerais
 */

// ---------- PWA: REGISTRAR SERVICE WORKER ----------
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js').catch(function() {});
}

// ---------- NAVBAR DROPDOWN (mobile) ----------
function navDropdown(el) {
    if (window.innerWidth <= 860) {
        var parent = el.parentElement;
        document.querySelectorAll('.has-dropdown.show').forEach(function(d) {
            if (d !== parent) d.classList.remove('show');
        });
        parent.classList.toggle('show');
    }
}

// Fechar dropdowns ao clicar fora
document.addEventListener('click', function(e) {
    if (!e.target.closest('.has-dropdown')) {
        document.querySelectorAll('.has-dropdown.show').forEach(function(d) {
            d.classList.remove('show');
        });
    }
});

// Função para mostrar alertas personalizados (Toast System)
function mostrarAlerta(mensagem, tipo = 'info') {
    // Garantir container de toasts
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const icones = { sucesso: '✅', erro: '❌', info: 'ℹ️', aviso: '⚠️' };

    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `<span class="toast-icon">${icones[tipo] || 'ℹ️'}</span><span class="toast-msg">${escapeHtml(mensagem)}</span><button class="toast-close" aria-label="Fechar">&times;</button>`;

    toast.querySelector('.toast-close').addEventListener('click', () => removerToast(toast));

    container.appendChild(toast);
    // Trigger reflow for animation
    toast.offsetHeight;
    toast.classList.add('toast-show');

    // Auto-hide
    const duracao = (tipo === 'erro' || tipo === 'aviso') ? 8000 : 4000;
    setTimeout(() => removerToast(toast), duracao);

    // Fallback: also update legacy div#mensagem if present
    const div = document.getElementById('mensagem');
    if (div) {
        div.textContent = mensagem;
        div.className = `alert alert-${tipo}`;
        div.style.display = 'block';
        if (tipo === 'sucesso' || tipo === 'info') {
            setTimeout(() => { div.style.display = 'none'; }, 5000);
        }
    }
}

function removerToast(toast) {
    if (!toast || toast._removing) return;
    toast._removing = true;
    toast.classList.remove('toast-show');
    toast.classList.add('toast-hide');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
    setTimeout(() => toast.remove(), 500); // fallback
}

// Formatador de moeda
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

// Sanitizar texto para uso seguro em innerHTML (prevenir XSS)
function escapeHtml(texto) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(texto));
    return div.innerHTML;
}

// Formatador de data
function formatarData(data) {
    return new Date(data).toLocaleDateString('pt-BR');
}

// Formatador de data e hora
function formatarDataHora(data) {
    return new Date(data).toLocaleString('pt-BR');
}

// Função para fazer requisições fetch com tratamento de erro
async function requisicao(url, opcoes = {}) {
    try {
        const resposta = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...opcoes.headers
            },
            ...opcoes
        });

        if (!resposta.ok) {
            const erro = await resposta.json();
            throw new Error(erro.erro || `Erro HTTP: ${resposta.status}`);
        }

        return await resposta.json();
    } catch (erro) {
        console.error('Erro na requisição:', erro);
        throw erro;
    }
}

// Validar email
function validarEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validar telefone (formato brasileiro)
function validarTelefone(telefone) {
    const re = /^\(?[0-9]{2}\)?[0-9]{4,5}[0-9]{4}$/;
    return re.test(telefone.replace(/\D/g, ''));
}

// Limpar formulário
function limparFormulario(formularioId) {
    const formulario = document.getElementById(formularioId);
    if (formulario) {
        formulario.reset();
    }
}

// Verificar se navegador tem suporte a localStorage
function temLocalStorage() {
    try {
        localStorage.setItem('teste', 'teste');
        localStorage.removeItem('teste');
        return true;
    } catch {
        return false;
    }
}

// Salvar dados localmente
function salvarLocal(chave, valor) {
    if (temLocalStorage()) {
        localStorage.setItem(chave, JSON.stringify(valor));
    }
}

// Obter dados localmente
function obterLocal(chave) {
    if (temLocalStorage()) {
        const valor = localStorage.getItem(chave);
        return valor ? JSON.parse(valor) : null;
    }
    return null;
}

// Remover dados localmente
function removerLocal(chave) {
    if (temLocalStorage()) {
        localStorage.removeItem(chave);
    }
}

// Função para copiar para clipboard
async function copiarParaClipboard(texto) {
    try {
        await navigator.clipboard.writeText(texto);
        mostrarAlerta('✅ Copiado para área de transferência!', 'sucesso');
    } catch (erro) {
        console.error('Erro ao copiar:', erro);
        mostrarAlerta('❌ Erro ao copiar', 'erro');
    }
}

// Compartilhar texto via WhatsApp (abre em nova aba)
function compartilharWhatsApp(texto) {
    window.open('https://wa.me/?text=' + encodeURIComponent(texto), '_blank');
}

// Compartilhar comprovante de venda via WhatsApp
async function compartilharVendaWhatsApp(idVenda) {
    try {
        const venda = await requisicao('/api/vendas/' + idVenda);
        let texto = '🍇 *Combina Açaí — Comprovante*\n';
        texto += '━━━━━━━━━━━━━━━━━\n';
        texto += '📋 Venda #' + venda.id_venda + '\n';
        texto += '📅 ' + formatarData(venda.data_venda) + '\n';
        texto += '👤 ' + (venda.cliente_nome || 'N/A') + '\n\n';
        texto += '*Itens:*\n';
        (venda.itens || []).forEach(function(item) {
            texto += '  • ' + item.produto_nome + ' x' + item.quantidade;
            texto += ' — R$ ' + item.subtotal.toFixed(2) + '\n';
        });
        texto += '\n💰 *Total: R$ ' + venda.valor_total.toFixed(2) + '*\n';
        texto += '💳 ' + (venda.forma_pagamento || 'N/A') + '\n';
        texto += '━━━━━━━━━━━━━━━━━\n';
        texto += 'Obrigado pela preferência! 💜';
        compartilharWhatsApp(texto);
    } catch (e) {
        mostrarAlerta('❌ Erro ao compartilhar: ' + e.message, 'erro');
    }
}

// Exportar para CSV
function exportarCSV(dados, nomeArquivo = 'exportacao.csv') {
    if (!Array.isArray(dados) || dados.length === 0) {
        mostrarAlerta('Nenhum dado para exportar', 'aviso');
        return;
    }

    // Pegar cabeçalhos
    const cabecalhos = Object.keys(dados[0]);
    
    // Criar CSV
    let csv = cabecalhos.join(',') + '\n';
    dados.forEach(linha => {
        const valores = cabecalhos.map(cabecalho => {
            let valor = linha[cabecalho];
            // Escape para valores com vírgula ou aspas
            if (typeof valor === 'string' && (valor.includes(',') || valor.includes('"') || valor.includes('\n'))) {
                valor = `"${valor.replace(/"/g, '""')}"`;
            }
            return valor;
        });
        csv += valores.join(',') + '\n';
    });

    // Criar blob e download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = nomeArquivo;
    link.click();
}

// Debounce para funções de busca
function debounce(funcao, delay = 300) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => funcao.apply(this, args), delay);
    };
}

// Throttle para funções que disparam frequentemente
function throttle(funcao, delay = 300) {
    let ultimaChamada = 0;
    return function(...args) {
        const agora = Date.now();
        if (agora - ultimaChamada >= delay) {
            ultimaChamada = agora;
            funcao.apply(this, args);
        }
    };
}

// Mostrar loading
function mostrarLoading(elemento) {
    if (typeof elemento === 'string') {
        elemento = document.getElementById(elemento);
    }
    if (elemento) {
        elemento.innerHTML = '⏳ Carregando...';
        elemento.style.opacity = '0.5';
    }
}

// Esconder loading
function esconderLoading(elemento) {
    if (typeof elemento === 'string') {
        elemento = document.getElementById(elemento);
    }
    if (elemento) {
        elemento.style.opacity = '1';
    }
}

// Event listener do documento pronto
document.addEventListener('DOMContentLoaded', () => {
    console.log('🍓 Açaiteria CRM - Script carregado com sucesso!');
    
    // Adicionar classes de suporte ao navegador
    if (!temLocalStorage()) {
        console.warn('⚠️ LocalStorage não disponível');
    }
});

// Tratador global de erros
window.addEventListener('error', (evento) => {
    console.error('Erro global:', evento.error);
    mostrarAlerta('❌ Ocorreu um erro. Tente novamente.', 'erro');
});

// Tratador para promessas não capturadas
window.addEventListener('unhandledrejection', (evento) => {
    console.error('Promise rejeitada não tratada:', evento.reason);
    mostrarAlerta('❌ Erro na requisição. Tente novamente.', 'erro');
});

// Confirmação antes de sair se houver dados não salvos
window.addEventListener('beforeunload', (evento) => {
    const temDadosNaoSalvos = obterLocal('vendaNaoFinalizada');
    if (temDadosNaoSalvos) {
        evento.preventDefault();
        evento.returnValue = '';
        return '';
    }
});

// =============================================================================
// DARK MODE
// =============================================================================
(function() {
    const saved = localStorage.getItem('theme');
    if (saved) document.documentElement.setAttribute('data-theme', saved);

    document.addEventListener('DOMContentLoaded', function() {
        const btn = document.getElementById('darkToggle');
        if (!btn) return;
        btn.textContent = (document.documentElement.getAttribute('data-theme') === 'dark') ? '☀️' : '🌙';
        btn.addEventListener('click', function() {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            const newTheme = isDark ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            btn.textContent = isDark ? '🌙' : '☀️';
        });
    });
})();

// =============================================================================
// CONFIRMATION MODAL
// =============================================================================
function confirmar(titulo, mensagem, callbackSim, icone = '⚠️') {
    // Remove modal anterior se existir
    const old = document.getElementById('confirmModal');
    if (old) old.remove();

    const overlay = document.createElement('div');
    overlay.id = 'confirmModal';
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-box" role="alertdialog" aria-modal="true" aria-labelledby="modal-titulo" aria-describedby="modal-msg">
            <div class="modal-icon">${icone}</div>
            <h3 id="modal-titulo">${escapeHtml(titulo)}</h3>
            <p id="modal-msg">${escapeHtml(mensagem)}</p>
            <div class="modal-actions">
                <button class="btn btn-secondary" id="modal-cancel">Cancelar</button>
                <button class="btn btn-danger" id="modal-confirm">Confirmar</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);

    // Trigger reflow then open
    overlay.offsetHeight;
    overlay.classList.add('open');

    const fechar = () => { overlay.classList.remove('open'); setTimeout(() => overlay.remove(), 300); };

    overlay.querySelector('#modal-cancel').addEventListener('click', fechar);
    overlay.querySelector('#modal-confirm').addEventListener('click', () => { fechar(); callbackSim(); });
    overlay.addEventListener('click', (e) => { if (e.target === overlay) fechar(); });
    // ESC key
    const escHandler = (e) => { if (e.key === 'Escape') { fechar(); document.removeEventListener('keydown', escHandler); } };
    document.addEventListener('keydown', escHandler);

    // Focus trap
    overlay.querySelector('#modal-cancel').focus();
}

// =============================================================================
// GLOBAL SEARCH
// =============================================================================
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        const input = document.getElementById('globalSearch');
        const results = document.getElementById('searchResults');
        if (!input || !results) return;

        const buscar = debounce(async function(q) {
            if (q.length < 2) { results.classList.remove('open'); return; }
            try {
                const resp = await fetch('/api/busca?q=' + encodeURIComponent(q));
                if (!resp.ok) { results.classList.remove('open'); return; }
                const dados = await resp.json();
                let html = '';
                if (dados.clientes.length) {
                    html += '<div class="search-results-group"><h4>👥 Clientes</h4>';
                    dados.clientes.forEach(function(c) {
                        html += '<a href="/clientes"><span class="sr-name">' + escapeHtml(c.nome) + '</span><span class="sr-detail">' + escapeHtml(c.telefone || c.email || '') + '</span></a>';
                    });
                    html += '</div>';
                }
                if (dados.produtos.length) {
                    html += '<div class="search-results-group"><h4>📦 Produtos</h4>';
                    dados.produtos.forEach(function(p) {
                        html += '<a href="/produtos"><span class="sr-name">' + escapeHtml(p.nome) + '</span><span class="sr-detail">' + formatarMoeda(p.preco) + (p.categoria ? ' · ' + escapeHtml(p.categoria) : '') + '</span></a>';
                    });
                    html += '</div>';
                }
                if (!html) html = '<div class="search-no-results">Nenhum resultado para "' + escapeHtml(q) + '"</div>';
                results.innerHTML = html;
                results.classList.add('open');
            } catch (_) {
                results.classList.remove('open');
            }
        }, 300);

        input.addEventListener('input', function() { buscar(this.value.trim()); });
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.navbar-search')) results.classList.remove('open');
        });
    });
})();

// =============================================================================
// API CLIENT MODULE — Mapeamento completo JS → Flask REST API
// Açaiteria CRM | Grupo 22 - UNIVESP 2026
//
// MAPA DE ENDPOINTS:
//   CLIENTES
//   GET    /api/clientes                                → ClienteAPI.listar()
//   POST   /api/clientes                                → ClienteAPI.criar(dados)
//   GET    /api/clientes/:id                            → ClienteAPI.obter(id)
//   PUT    /api/clientes/:id                            → ClienteAPI.atualizar(id, dados)
//   DELETE /api/clientes/:id                            → ClienteAPI.anonimizar(id)
//   PUT    /api/clientes/:id/consentimento              → ClienteAPI.atualizarConsentimento(id, consentiu)
//   GET    /api/clientes/:id/consentimento/historico    → ClienteAPI.historicoConsentimento(id)
//
//   PRODUTOS
//   GET    /api/produtos                                → ProdutoAPI.listar()
//   POST   /api/produtos                                → ProdutoAPI.criar(dados)
//
//   VENDAS
//   GET    /api/vendas                                  → VendaAPI.listar()
//   POST   /api/vendas                                  → VendaAPI.criar(dados)
//   GET    /api/vendas/:id                              → VendaAPI.obter(id)
//
//   RELATÓRIOS
//   GET    /api/relatorios/dia-atual                    → RelatorioAPI.diaAtual()
//   GET    /api/relatorios/clientes-frequentes          → RelatorioAPI.clientesFrequentes()
//   GET    /api/relatorios/produtos-ranking             → RelatorioAPI.produtosRanking()
//
//   EXPORTAÇÃO
//   GET    /api/exportar/clientes-csv                   → ExportAPI.clientesCsv()
// =============================================================================

/** Utilitário base — todas as chamadas passam por aqui */
async function _req(url, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.erro || `Erro HTTP ${res.status}`);
    return data;
}

// ----- CLIENTES -----
const ClienteAPI = {
    /** GET /api/clientes — lista todos os clientes ativos */
    listar: () => _req('/api/clientes'),

    /** GET /api/clientes/:id — detalhes + total de compras e faturamento */
    obter: (id) => _req(`/api/clientes/${id}`),

    /**
     * POST /api/clientes — cria novo cliente
     * @param {Object} dados { nome*, telefone, email, observacoes,
     *                         consentimento_lgpd, versao_politica }
     * ⚠️ Sem consentimento_lgpd=true, vendas serão bloqueadas pela API.
     */
    criar: (dados) => _req('/api/clientes', 'POST', dados),

    /**
     * PUT /api/clientes/:id — atualiza campos cadastrais
     * Para consentimento use atualizarConsentimento().
     */
    atualizar: (id, dados) => _req(`/api/clientes/${id}`, 'PUT', dados),

    /**
     * DELETE /api/clientes/:id
     * ⚠️ NÃO APAGA — anonimiza dados pessoais conforme obrigação LGPD.
     * Histórico de vendas mantido sem identificação.
     */
    anonimizar: (id) => _req(`/api/clientes/${id}`, 'DELETE'),

    /**
     * PUT /api/clientes/:id/consentimento
     * Concede ou revoga consentimento LGPD com registro no histórico de auditoria.
     * @param {boolean} consentiu  true=concede | false=revoga
     * @param {string}  versao     versão da política, ex: 'v1.0'
     */
    atualizarConsentimento: (id, consentiu, versao = 'v1.0') =>
        _req(`/api/clientes/${id}/consentimento`, 'PUT',
             { consentimento_lgpd: consentiu, versao_politica: versao }),

    /** GET /api/clientes/:id/consentimento/historico — auditoria LGPD completa */
    historicoConsentimento: (id) =>
        _req(`/api/clientes/${id}/consentimento/historico`),
};

// ----- PRODUTOS -----
const ProdutoAPI = {
    /** GET /api/produtos */
    listar: () => _req('/api/produtos'),

    /**
     * POST /api/produtos
     * @param {Object} dados { nome_produto*, preco*, categoria, descricao }
     */
    criar: (dados) => _req('/api/produtos', 'POST', dados),
};

// ----- VENDAS -----
const VendaAPI = {
    /** GET /api/vendas — com filtros opcionais (data_inicio, data_fim, id_cliente, forma_pagamento, pagina) */
    listar: (filtros = {}) => {
        const params = new URLSearchParams();
        Object.entries(filtros).forEach(([k, v]) => { if (v) params.set(k, v); });
        const qs = params.toString();
        return _req('/api/vendas' + (qs ? '?' + qs : ''));
    },

    /** GET /api/vendas/:id — com itens e pagamento */
    obter: (id) => _req(`/api/vendas/${id}`),

    /**
     * POST /api/vendas
     * ⚠️ LGPD: API retorna 400 se cliente não tiver consentimento_lgpd=true.
     *    Sempre valide no frontend antes de chamar (veja exemplo abaixo).
     * @param {Object} dados {
     *   id_cliente*, itens*: [{id_produto, quantidade}],
     *   forma_pagamento: 'Dinheiro'|'Cartão'|'Pix', observacoes
     * }
     */
    criar: (dados) => _req('/api/vendas', 'POST', dados),
};

// ----- RELATÓRIOS -----
const RelatorioAPI = {
    /** GET /api/relatorios/dia-atual — fechamento diário com ticket médio */
    diaAtual: () => _req('/api/relatorios/dia-atual'),

    /** GET /api/relatorios/clientes-frequentes — top 10 (últimos 30 dias) */
    clientesFrequentes: () => _req('/api/relatorios/clientes-frequentes'),

    /** GET /api/relatorios/produtos-ranking — top 15 produtos mais vendidos */
    produtosRanking: () => _req('/api/relatorios/produtos-ranking'),
};

// ----- EXPORTAÇÃO -----
const ExportAPI = {
    /** Dispara download do CSV de clientes com consentimento LGPD */
    clientesCsv: () => { window.location.href = '/api/exportar/clientes-csv'; },
};

// ----- EXEMPLO: criar venda com validação LGPD no frontend -----
/*
async function registrarVendaComLGPD(id_cliente, itens, forma_pagamento) {
    // 1. Verifica consentimento ANTES de chamar a API de vendas
    const cliente = await ClienteAPI.obter(id_cliente);
    if (!cliente.consentimento_lgpd) {
        mostrarAlerta('Cliente sem consentimento LGPD — solicite antes de registrar venda.', 'aviso');
        return null;
    }
    // 2. Registra a venda
    const venda = await VendaAPI.criar({ id_cliente, itens, forma_pagamento });
    mostrarAlerta(`Venda #${venda.id_venda} criada — ${formatarMoeda(venda.valor_total)}`, 'sucesso');
    return venda;
}
*/

// =============================================================================
// FIM DO API CLIENT MODULE
// =============================================================================

// =============================================================================
// FAB — Floating Action Button (ações rápidas)
// =============================================================================
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        // Não mostrar na página de login/totem
        if (location.pathname === '/login' || location.pathname === '/totem') return;

        const fab = document.createElement('div');
        fab.className = 'fab-container';
        fab.innerHTML = `
            <div class="fab-menu">
                <a href="/nova-venda" class="fab-action"><span class="fab-action-icon">🛒</span> Nova Venda</a>
                <a href="/cadastro-cliente" class="fab-action"><span class="fab-action-icon">👤</span> Novo Cliente</a>
                <a href="/suporte" class="fab-action"><span class="fab-action-icon">🎧</span> Suporte</a>
                <a href="/relatorios" class="fab-action"><span class="fab-action-icon">📊</span> Relatórios</a>
                <button class="fab-action" onclick="mostrarAtalhos()"><span class="fab-action-icon">⌨️</span> Atalhos</button>
            </div>
            <button class="fab-btn" aria-label="Ações rápidas" title="Ações rápidas">＋</button>
        `;
        document.body.appendChild(fab);

        fab.querySelector('.fab-btn').addEventListener('click', function() {
            fab.classList.toggle('open');
            this.classList.toggle('open');
        });

        // Fechar ao clicar fora
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.fab-container')) {
                fab.classList.remove('open');
                fab.querySelector('.fab-btn').classList.remove('open');
            }
        });
    });
})();

// =============================================================================
// NOTIFICATION BADGES — Estoque baixo + Tickets abertos
// =============================================================================
(function() {
    document.addEventListener('DOMContentLoaded', async function() {
        if (location.pathname === '/login' || location.pathname === '/totem') return;

        try {
            // Badge estoque baixo no link Produtos
            const respEstoque = await fetch('/api/produtos/estoque-baixo');
            if (respEstoque.ok) {
                const produtos = await respEstoque.json();
                if (produtos.length > 0) {
                    const linkProdutos = document.querySelector('a[href="/produtos"]');
                    if (linkProdutos) {
                        const badge = document.createElement('span');
                        badge.className = 'nav-badge';
                        badge.textContent = produtos.length;
                        badge.title = produtos.length + ' produto(s) com estoque baixo';
                        linkProdutos.appendChild(badge);
                    }
                }
            }
        } catch (_) {}

        try {
            // Badge tickets abertos no link Suporte (se existir)
            const respTickets = await fetch('/api/suporte/tickets?status=aberto');
            if (respTickets.ok) {
                const json = await respTickets.json();
                const total = json.total || 0;
                if (total > 0) {
                    const linkSuporte = document.querySelector('a[href="/suporte"]');
                    if (linkSuporte) {
                        const badge = document.createElement('span');
                        badge.className = 'nav-badge';
                        badge.textContent = total;
                        badge.title = total + ' ticket(s) aberto(s)';
                        linkSuporte.appendChild(badge);
                    }
                }
            }
        } catch (_) {}
    });
})();

// =============================================================================
// KEYBOARD SHORTCUTS — Atalhos globais de teclado
// =============================================================================
(function() {
    const atalhos = [
        { tecla: 'h', desc: 'Dashboard', acao: function() { location.href = '/'; } },
        { tecla: 'v', desc: 'Nova Venda', acao: function() { location.href = '/nova-venda'; } },
        { tecla: 'c', desc: 'Clientes', acao: function() { location.href = '/clientes'; } },
        { tecla: 'p', desc: 'Produtos', acao: function() { location.href = '/produtos'; } },
        { tecla: 'r', desc: 'Relatórios', acao: function() { location.href = '/relatorios'; } },
        { tecla: 's', desc: 'Suporte', acao: function() { location.href = '/suporte'; } },
        { tecla: '/', desc: 'Busca global', acao: function() { var el = document.getElementById('globalSearch'); if (el) el.focus(); } },
        { tecla: '?', desc: 'Ver atalhos', acao: function() { mostrarAtalhos(); } },
    ];

    document.addEventListener('keydown', function(e) {
        // Ignorar se está digitando em input/textarea/select
        var tag = (e.target.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable) return;
        // Ignorar se Ctrl/Cmd/Alt pressionado
        if (e.ctrlKey || e.metaKey || e.altKey) return;

        var tecla = e.key.toLowerCase();
        for (var i = 0; i < atalhos.length; i++) {
            if (atalhos[i].tecla === tecla) {
                e.preventDefault();
                atalhos[i].acao();
                return;
            }
        }
    });

    window.mostrarAtalhos = function() {
        var overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.style.display = 'flex';
        overlay.innerHTML = `
            <div class="modal-box" style="max-width:480px">
                <h3>⌨️ Atalhos de Teclado</h3>
                <div class="shortcuts-grid">
                    ${atalhos.map(function(a) {
                        return '<div class="shortcut-item"><kbd>' + a.tecla + '</kbd><span>' + a.desc + '</span></div>';
                    }).join('')}
                </div>
                <div style="text-align:right;margin-top:1rem;">
                    <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">Fechar</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.remove();
        });
        document.addEventListener('keydown', function handler(e) {
            if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', handler); }
        });
    };
})();

// =============================================================================
// WELCOME BANNER — Saudação personalizada com hora do dia
// =============================================================================
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var hero = document.querySelector('.hero');
        if (!hero || location.pathname !== '/') return;

        var h = new Date().getHours();
        var saudacao, emoji;
        if (h < 6) { saudacao = 'Boa madrugada'; emoji = '🌙'; }
        else if (h < 12) { saudacao = 'Bom dia'; emoji = '☀️'; }
        else if (h < 18) { saudacao = 'Boa tarde'; emoji = '🌤️'; }
        else { saudacao = 'Boa noite'; emoji = '🌙'; }

        var nome = (document.querySelector('.nav-user-info') || {}).textContent || '';
        nome = nome.replace(/^👤\s*/, '').trim();

        if (!nome) return;

        var banner = document.createElement('div');
        banner.className = 'welcome-banner';
        banner.innerHTML = `
            <div class="welcome-emoji">${emoji}</div>
            <div class="welcome-text">
                <h2>${saudacao}, ${escapeHtml(nome)}!</h2>
                <p>Pronto para mais um dia na Combina Açaí?</p>
            </div>
        `;

        hero.parentNode.insertBefore(banner, hero);
    });
})();
