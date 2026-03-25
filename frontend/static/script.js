/**
 * Script Principal - Açaiteria CRM
 * Funções auxiliares e gerais
 */

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

// Função para mostrar alertas personalizados
function mostrarAlerta(mensagem, tipo = 'info') {
    const alertIds = {
        'sucesso': 'alertSucesso',
        'erro': 'alertErro',
        'info': 'alertInfo',
        'aviso': 'alertAviso'
    };

    const div = document.getElementById('mensagem');
    if (!div) return;

    div.textContent = mensagem;
    div.className = `alert alert-${tipo}`;
    div.style.display = 'block';

    // Auto-hide após 5 segundos
    if (tipo === 'sucesso' || tipo === 'info') {
        setTimeout(() => {
            div.style.display = 'none';
        }, 5000);
    }
}

// Formatador de moeda
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
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
    /** GET /api/vendas — mais recentes primeiro */
    listar: () => _req('/api/vendas'),

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
