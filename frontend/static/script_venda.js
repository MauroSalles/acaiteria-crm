/**
 * Script Específico - Página de Vendas
 * Gerenciamento de itens, cálculos e finalização de vendas
 */

let itensVenda = [];
let clienteSelecionado = null;
let produtosDisponiveis = [];
let complementosDisponiveis = [];
let complementosSelecionados = [];
let filtroCompAtual = '';
let cupomAplicado = null; // {codigo, tipo_desconto, valor_desconto, desconto_calculado}

// Inicializar a página de vendas
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await Promise.all([
            carregarClientes(),
            carregarProdutos(),
            carregarComplementos(),
        ]);
    } catch (erro) {
        mostrarAlerta('Erro ao carregar dados. Recarregue a página.', 'erro');
        return;
    }
    
    // Restaurar carrinho salvo (caso usuário recarregou a página)
    const itensSalvos = obterLocal('vendaItens');
    if (itensSalvos && Array.isArray(itensSalvos) && itensSalvos.length > 0) {
        itensVenda = itensSalvos;
        renderizarItens();
        recalcularTotais();
        mostrarAlerta('🔄 Carrinho anterior restaurado automaticamente', 'info');
    }
    const clienteSalvo = obterLocal('vendaClienteAtual');
    if (clienteSalvo && clienteSalvo.id_cliente) {
        const select = document.getElementById('cliente-select');
        select.value = String(clienteSalvo.id_cliente);
        if (select.value) {
            clienteSelecionado = clienteSalvo;
        }
    }
    
    // Event listeners
    document.getElementById('btn-adicionar').addEventListener('click', adicionarItem);
    document.getElementById('desconto-perc').addEventListener('change', recalcularTotais);
    document.getElementById('taxa').addEventListener('change', recalcularTotais);
    document.getElementById('btn-aplicar-cupom').addEventListener('click', validarCupomVenda);
    document.getElementById('btn-finalizar').addEventListener('click', finalizarVenda);
    document.getElementById('btn-cancelar').addEventListener('click', cancelarVenda);
    document.getElementById('cliente-select').addEventListener('change', selecionarCliente);
    document.getElementById('produto-select').addEventListener('change', onProdutoSelecionado);
    document.getElementById('produto-select').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') adicionarItem();
    });
    document.getElementById('quantidade').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') adicionarItem();
    });
});

// Carregar clientes disponíveis (somente com consentimento LGPD)
async function carregarClientes() {
    try {
        const dados = await requisicao('/api/clientes');
        const clientes = dados.clientes || dados;
        const select = document.getElementById('cliente-select');
        
        // Limpar opções existentes deixando a primeira
        select.innerHTML = '<option value="">-- Selecione um cliente --</option>';
        
        // Filtrar e adicionar apenas clientes com consentimento LGPD
        const clientesValidos = (Array.isArray(clientes) ? clientes : []).filter(c => c.consentimento_lgpd);
        
        clientesValidos.forEach(cliente => {
            const option = document.createElement('option');
            option.value = cliente.id_cliente;
            option.textContent = `${cliente.nome}${cliente.telefone ? ' - ' + cliente.telefone : ''}`;
            select.appendChild(option);
        });

        if (clientesValidos.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = '⚠️ Nenhum cliente com consentimento LGPD';
            option.disabled = true;
            select.appendChild(option);
        }
    } catch (erro) {
        console.error('Erro ao carregar clientes:', erro);
        mostrarAlerta('❌ Erro ao carregar clientes', 'erro');
    }
}

// Carregar produtos disponíveis (agrupados por categoria)
async function carregarProdutos() {
    try {
        const produtos = await requisicao('/api/produtos');
        const select = document.getElementById('produto-select');
        
        // Limpar opções
        select.innerHTML = '<option value="">-- Selecione um produto --</option>';
        
        // Agrupar por categoria
        const grupos = {};
        produtos.forEach(p => {
            const cat = p.categoria || 'Outros';
            if (!grupos[cat]) grupos[cat] = [];
            grupos[cat].push(p);
        });

        const icones = {'Açaí': '🍇', 'Sorvete': '🍦', 'Complemento': '🥣', 'Bebida': '🥤'};
        const ordemCat = ['Açaí', 'Sorvete', 'Complemento', 'Bebida'];
        const cats = Object.keys(grupos).sort((a, b) => {
            const ia = ordemCat.indexOf(a), ib = ordemCat.indexOf(b);
            return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
        });

        cats.forEach(cat => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = `${icones[cat] || '📦'} ${cat}`;
            grupos[cat].forEach(produto => {
                const opt = document.createElement('option');
                opt.value = produto.id_produto;
                const vol = produto.volume ? ` ${produto.volume}` : '';
                opt.textContent = `${produto.nome_produto}${vol} — R$ ${produto.preco.toFixed(2)}`;
                optgroup.appendChild(opt);
            });
            select.appendChild(optgroup);
        });
        
        // Salvar globalmente
        produtosDisponiveis = produtos;
    } catch (erro) {
        console.error('Erro ao carregar produtos:', erro);
        mostrarAlerta('❌ Erro ao carregar produtos', 'erro');
    }
}

// Carregar complementos/toppings disponíveis
async function carregarComplementos() {
    try {
        complementosDisponiveis = await requisicao('/api/complementos');
        renderComplementosGrid();
    } catch (erro) {
        console.error('Erro ao carregar complementos:', erro);
    }
}

// Exibir/ocultar painel de complementos conforme produto selecionado
function onProdutoSelecionado() {
    const idProduto = document.getElementById('produto-select').value;
    const section = document.getElementById('complementos-section');
    if (!idProduto) {
        section.style.display = 'none';
        return;
    }
    const produto = produtosDisponiveis.find(p => p.id_produto === parseInt(idProduto));
    if (produto && ['Açaí', 'Sorvete'].includes(produto.categoria)) {
        section.style.display = 'block';
        complementosSelecionados = [];
        renderComplementosGrid();
        atualizarInfoCompSelecionados();
    } else {
        section.style.display = 'none';
        complementosSelecionados = [];
    }
}

// Filtrar complementos por categoria
function filtrarComplementos(cat) {
    filtroCompAtual = cat;
    document.querySelectorAll('#filtrosCompCategoria button').forEach(b => {
        b.className = b.getAttribute('data-filtro') === cat
            ? 'btn btn-primary' : 'btn btn-info';
        b.style.fontSize = '.75rem';
        b.style.padding = '.2rem .6rem';
    });
    renderComplementosGrid();
}

// Renderizar grid de complementos
function renderComplementosGrid() {
    const grid = document.getElementById('complementos-grid');
    if (!grid) return;
    let lista = complementosDisponiveis.filter(c => c.ativo !== false);
    if (filtroCompAtual) {
        lista = lista.filter(c => c.categoria === filtroCompAtual);
    }
    if (!lista.length) {
        grid.innerHTML = '<p class="text-muted" style="grid-column:1/-1;text-align:center;font-size:.85rem">Nenhum complemento encontrado</p>';
        return;
    }
    const iconesCat = {'Fruta': '🍓', 'Calda': '🍫', 'Farináceo': '🥜', 'Extra': '⭐'};
    grid.innerHTML = lista.map(c => {
        const sel = complementosSelecionados.includes(c.id_complemento);
        return `<label class="comp-label${sel ? ' selected' : ''}"
            onclick="toggleComplemento(${c.id_complemento})">
            <input type="checkbox" ${sel ? 'checked' : ''} style="pointer-events:none;accent-color:#7B1FA2">
            <span>${iconesCat[c.categoria] || '🥣'} ${escapeHtml(c.nome)}</span>
            ${c.preco_adicional > 0 ? `<span class="comp-price">+R$${c.preco_adicional.toFixed(2)}</span>` : ''}
        </label>`;
    }).join('');
}

// Alternar seleção de complemento
function toggleComplemento(id) {
    const idx = complementosSelecionados.indexOf(id);
    if (idx >= 0) {
        complementosSelecionados.splice(idx, 1);
    } else {
        complementosSelecionados.push(id);
    }
    renderComplementosGrid();
    atualizarInfoCompSelecionados();
}

// Atualizar texto de complementos selecionados
function atualizarInfoCompSelecionados() {
    const el = document.getElementById('complementos-selecionados');
    if (!el) return;
    if (!complementosSelecionados.length) {
        el.textContent = '';
        return;
    }
    const nomes = complementosSelecionados.map(id => {
        const c = complementosDisponiveis.find(x => x.id_complemento === id);
        return c ? c.nome : '';
    }).filter(Boolean);
    const totalComp = complementosSelecionados.reduce((t, id) => {
        const c = complementosDisponiveis.find(x => x.id_complemento === id);
        return t + (c ? (c.preco_adicional || 0) : 0);
    }, 0);
    el.innerHTML = `🥣 <strong>${nomes.length}</strong> selecionado(s): ${nomes.join(', ')}` +
        (totalComp > 0 ? ` — <strong>+${formatarMoeda(totalComp)}</strong>/un` : '');
}

// Selecionar cliente
async function selecionarCliente() {
    const idCliente = document.getElementById('cliente-select').value;
    
    if (!idCliente) {
        clienteSelecionado = null;
        const infoEl = document.getElementById('cliente-pontos-info');
        if (infoEl) infoEl.style.display = 'none';
        return;
    }
    
    // Encontrar cliente na lista
    const select = document.getElementById('cliente-select');
    const option = select.options[select.selectedIndex];
    if (!option) return;
    
    clienteSelecionado = {
        id_cliente: parseInt(idCliente),
        nome: option.textContent.split(' - ')[0]
    };
    
    // Salvar para caso de desistência
    salvarLocal('vendaClienteAtual', clienteSelecionado);

    // Buscar pontos de fidelidade
    try {
        const pontos = await requisicao(`/api/clientes/${idCliente}/pontos`);
        let infoEl = document.getElementById('cliente-pontos-info');
        if (!infoEl) {
            infoEl = document.createElement('div');
            infoEl.id = 'cliente-pontos-info';
            infoEl.className = 'cupom-info';
            select.parentElement.appendChild(infoEl);
        }
        infoEl.style.display = 'block';
        const ptTotal = pontos.pontos || 0;
        const descDisponivel = Math.floor(ptTotal / 100) * 5;
        infoEl.innerHTML = `🌟 <strong>${ptTotal}</strong> pontos` +
            (descDisponivel > 0 ? ` — Pode resgatar até <strong>R$ ${descDisponivel.toFixed(2)}</strong> de desconto` : '');
    } catch(e) { /* silencioso */ }
}

// Adicionar item à venda
function adicionarItem() {
    const selectProduto = document.getElementById('produto-select');
    const idProduto = selectProduto.value;
    const quantidade = parseInt(document.getElementById('quantidade').value) || 1;
    
    if (!clienteSelecionado) {
        mostrarAlerta('⚠️ Selecione um cliente primeiro!', 'aviso');
        return;
    }
    
    if (!idProduto) {
        mostrarAlerta('⚠️ Selecione um produto!', 'aviso');
        return;
    }
    
    if (quantidade <= 0) {
        mostrarAlerta('⚠️ Quantidade deve ser maior que zero!', 'aviso');
        return;
    }
    
    // Encontrar produto
    const produto = produtosDisponiveis.find(p => p.id_produto === parseInt(idProduto));
    if (!produto) {
        mostrarAlerta('❌ Produto não encontrado!', 'erro');
        return;
    }

    // Calcular preço de complementos selecionados
    const compsItem = complementosSelecionados.map(id => {
        const c = complementosDisponiveis.find(x => x.id_complemento === id);
        return c ? { id_complemento: c.id_complemento, nome: c.nome, preco: c.preco_adicional || 0 } : null;
    }).filter(Boolean);
    const precoComps = compsItem.reduce((t, c) => t + c.preco, 0);
    const precoUnitarioTotal = parseFloat(produto.preco) + precoComps;
    
    // Sempre adicionar como novo item (complementos diferentes = item diferente)
    itensVenda.push({
        id_produto: parseInt(idProduto),
        nome_produto: produto.nome_produto,
        volume: produto.volume || '',
        quantidade: quantidade,
        preco_unitario: parseFloat(produto.preco),
        complementos: compsItem,
        preco_complementos: precoComps,
        subtotal: quantidade * precoUnitarioTotal,
    });
    
    // Resetar formulário
    document.getElementById('produto-select').value = '';
    document.getElementById('quantidade').value = '1';
    complementosSelecionados = [];
    document.getElementById('complementos-section').style.display = 'none';
    selectProduto.focus();
    
    // Atualizar interface
    renderizarItens();
    recalcularTotais();
    salvarLocal('vendaItens', itensVenda);
    
    const compMsg = compsItem.length ? ` + ${compsItem.length} complemento(s)` : '';
    mostrarAlerta(`✅ ${produto.nome_produto}${compMsg} adicionado!`, 'sucesso');
}

// Renderizar items na lista
function renderizarItens() {
    const lista = document.getElementById('itens-lista');
    
    if (itensVenda.length === 0) {
        lista.innerHTML = '<p class="placeholder">Nenhum item adicionado ainda...</p>';
        return;
    }
    
    lista.innerHTML = itensVenda.map((item, index) => {
        const comps = (item.complementos || []);
        const compsHtml = comps.length
            ? `<div class="comp-info">🥣 ${comps.map(c => c.nome).join(', ')}${item.preco_complementos > 0 ? ` (+${formatarMoeda(item.preco_complementos)}/un)` : ''}</div>`
            : '';
        const vol = item.volume ? ` <span class="vol-badge">${escapeHtml(item.volume)}</span>` : '';
        return `<div class="item-venda">
            <div>
                <div class="item-nome">${escapeHtml(item.nome_produto)}${vol}</div>
                ${compsHtml}
                <div class="item-valor">
                    Qtd: ${item.quantidade} × R$ ${(item.preco_unitario + (item.preco_complementos || 0)).toFixed(2)} = 
                    <strong>${formatarMoeda(item.subtotal)}</strong>
                </div>
            </div>
            <button type="button" class="btn-remover" onclick="removerItem(${index})">
                ❌ Remover
            </button>
        </div>`;
    }).join('');
}

// Remover item da venda
function removerItem(index) {
    const itemRemovido = itensVenda[index];
    itensVenda.splice(index, 1);
    
    renderizarItens();
    recalcularTotais();
    salvarLocal('vendaItens', itensVenda);
    
    mostrarAlerta(`✅ ${itemRemovido.nome_produto} removido!`, 'sucesso');
}

// Validar e aplicar cupom de desconto
async function validarCupomVenda() {
    const codigoInput = document.getElementById('cupom-codigo');
    const codigo = codigoInput.value.trim().toUpperCase();
    const infoDiv = document.getElementById('cupom-info');

    if (!codigo) {
        mostrarAlerta('⚠️ Digite o código do cupom!', 'aviso');
        return;
    }

    const subtotal = itensVenda.reduce((t, i) => t + i.subtotal, 0);
    if (subtotal <= 0) {
        mostrarAlerta('⚠️ Adicione itens à venda antes de aplicar o cupom!', 'aviso');
        return;
    }

    try {
        const resp = await requisicao('/api/cupons/validar', {
            method: 'POST',
            body: JSON.stringify({ codigo, valor_pedido: subtotal })
        });

        cupomAplicado = {
            codigo: resp.codigo,
            tipo_desconto: resp.tipo_desconto,
            valor_desconto: resp.valor_desconto,
            desconto_calculado: resp.desconto_calculado
        };

        infoDiv.style.display = 'block';
        infoDiv.style.background = '#e8f5e9';
        infoDiv.innerHTML = `✅ Cupom <strong>${resp.codigo}</strong> aplicado! Desconto: <strong>${formatarMoeda(resp.desconto_calculado)}</strong>`;
        codigoInput.readOnly = true;
        document.getElementById('btn-aplicar-cupom').textContent = '❌ Remover';
        document.getElementById('btn-aplicar-cupom').onclick = removerCupom;

        recalcularTotais();
        mostrarAlerta(`🎟️ Cupom ${resp.codigo} aplicado!`, 'sucesso');
    } catch (erro) {
        cupomAplicado = null;
        infoDiv.style.display = 'block';
        infoDiv.style.background = '#ffebee';
        infoDiv.innerHTML = `❌ ${erro.message || 'Cupom inválido'}`;
    }
}

// Remover cupom aplicado
function removerCupom() {
    cupomAplicado = null;
    document.getElementById('cupom-codigo').value = '';
    document.getElementById('cupom-codigo').readOnly = false;
    document.getElementById('cupom-info').style.display = 'none';
    const btn = document.getElementById('btn-aplicar-cupom');
    btn.textContent = 'Aplicar';
    btn.onclick = validarCupomVenda;
    recalcularTotais();
    mostrarAlerta('Cupom removido.', 'info');
}

// Recalcular totais
function recalcularTotais() {
    // Subtotal
    const subtotal = itensVenda.reduce((total, item) => total + item.subtotal, 0);
    document.getElementById('subtotal').textContent = formatarMoeda(subtotal);
    
    // Desconto percentual
    const descontoPerc = parseFloat(document.getElementById('desconto-perc').value) || 0;
    let descontoValor = subtotal * (descontoPerc / 100);

    // Desconto cupom
    if (cupomAplicado) {
        descontoValor += cupomAplicado.desconto_calculado;
    }
    document.getElementById('desconto-valor').textContent = formatarMoeda(descontoValor);
    
    // Taxa
    const taxa = parseFloat(document.getElementById('taxa').value) || 0;
    
    // Total final
    const totalFinal = Math.max(subtotal - descontoValor + taxa, 0);
    document.getElementById('total-final').textContent = `${formatarMoeda(totalFinal)}`;
}

// Finalizar venda
async function finalizarVenda() {
    if (itensVenda.length === 0) {
        mostrarAlerta('⚠️ Nenhum item adicionado à venda!', 'aviso');
        return;
    }
    
    if (!clienteSelecionado) {
        mostrarAlerta('⚠️ Selecione um cliente!', 'aviso');
        return;
    }
    
    // Preparar dados
    const descontoPerc = parseFloat(document.getElementById('desconto-perc').value) || 0;
    const taxa = parseFloat(document.getElementById('taxa').value) || 0;
    
    // Calcular valor total com desconto e taxa
    const subtotal = itensVenda.reduce((total, item) => total + item.subtotal, 0);
    const descontoValor = subtotal * (descontoPerc / 100);
    const valorTotal = subtotal - descontoValor + taxa;
    
    const dadosVenda = {
        id_cliente: clienteSelecionado.id_cliente,
        forma_pagamento: document.getElementById('forma-pagamento').value,
        observacoes: document.getElementById('observacoes').value || '',
        desconto_percentual: descontoPerc,
        taxa: taxa,
        cupom_codigo: cupomAplicado ? cupomAplicado.codigo : null,
        itens: itensVenda.map(item => ({
            id_produto: item.id_produto,
            quantidade: item.quantidade,
            complementos: (item.complementos || []).map(c => c.id_complemento),
        }))
    };
    
    try {
        // Desabilitar botão enquanto processa
        const btn = document.getElementById('btn-finalizar');
        btn.disabled = true;
        btn.textContent = '⏳ Finalizando...';
        
        const resposta = await requisicao('/api/vendas', {
            method: 'POST',
            body: JSON.stringify(dadosVenda)
        });
        
        const venda = resposta;
        
        // Sucesso!
        let msg = `✅ Venda #${venda.id_venda} finalizada com sucesso!`;
        if (venda.pontos_ganhos) {
            msg += ` 🌟 +${venda.pontos_ganhos} pontos (total: ${venda.pontos_total})`;
        }
        mostrarAlerta(msg, 'sucesso');
        
        // Limpar localStorage
        removerLocal('vendaItens');
        removerLocal('vendaClienteAtual');
        
        // Limpar formulário
        itensVenda = [];
        clienteSelecionado = null;
        document.getElementById('cliente-select').value = '';
        document.getElementById('desconto-perc').value = '0';
        document.getElementById('taxa').value = '0';
        document.getElementById('observacoes').value = '';
        document.getElementById('quantidade').value = '1';
        document.getElementById('produto-select').value = '';
        cupomAplicado = null;
        document.getElementById('cupom-codigo').value = '';
        document.getElementById('cupom-codigo').readOnly = false;
        document.getElementById('cupom-info').style.display = 'none';
        complementosSelecionados = [];
        document.getElementById('complementos-section').style.display = 'none';
        const btnCupom = document.getElementById('btn-aplicar-cupom');
        btnCupom.textContent = 'Aplicar';
        btnCupom.onclick = validarCupomVenda;
        
        renderizarItens();
        recalcularTotais();
        
        // Gerar recibo
        exibirRecibo(venda);

        // Mostrar botão de compartilhar via WhatsApp
        const msgEl = document.getElementById('mensagem');
        if (msgEl) {
            const btnWa = document.createElement('button');
            btnWa.className = 'btn btn-success';
            btnWa.style.cssText = 'margin-top:0.5rem;';
            btnWa.textContent = '📱 Enviar Comprovante via WhatsApp';
            btnWa.onclick = function() { compartilharVendaWhatsApp(venda.id_venda); };
            msgEl.appendChild(document.createElement('br'));
            msgEl.appendChild(btnWa);
        }
        
        // Reabilitar botão
        setTimeout(() => {
            btn.disabled = false;
            btn.textContent = '✅ Finalizar Venda';
        }, 2000);
    } catch (erro) {
        console.error('Erro ao finalizar venda:', erro);
        mostrarAlerta(`❌ Erro: ${erro.message}`, 'erro');
        
        // Reabilitar botão
        const btn = document.getElementById('btn-finalizar');
        btn.disabled = false;
        btn.textContent = '✅ Finalizar Venda';
    }
}

// Exibir recibo
function exibirRecibo(venda) {
    const recibo = `
        ╔════════════════════════════════╗
        ║  🍓 AÇAITERIA COMBINA AÇAÍ  ║
        ║      Recibo de Venda            ║
        ╚════════════════════════════════╝
        
        Venda #${venda.id_venda}
        Data: ${new Date(venda.data_venda).toLocaleString('pt-BR')}
        
        ────────────────────────────────
        Cliente: ${venda.cliente_nome}
        ────────────────────────────────
        
        Itens:
        ${venda.itens.map(item => {
            const comps = (item.complementos || []);
            const compTxt = comps.length
                ? `\n          🥣 ${comps.map(c => c.nome).join(', ')}`
                : '';
            return `\n        ${item.produto_nome}${compTxt}\n        Qtd: ${item.quantidade} × R$ ${item.preco_unitario.toFixed(2)} = R$ ${item.subtotal.toFixed(2)}`;
        }).join('')}
        
        ────────────────────────────────
        Total: R$ ${(venda.valor_total).toFixed(2)}
        Pagamento: ${venda.forma_pagamento}
        Status: ${venda.status_pagamento}
        
        ════════════════════════════════
        Muito obrigado pela compra! 😊
        ════════════════════════════════
    `;
    
    // Mostrar no console
    console.log(recibo);
    
    // Copiar para clipboard
    copiarParaClipboard(recibo);
    
    // Mostrar em alert
    alert(recibo);
}

// Cancelar venda
function cancelarVenda() {
    if (itensVenda.length === 0) {
        window.location.href = '/';
        return;
    }
    
    const confirmar = confirm('⚠️ Tem certeza que deseja cancelar a venda?\nOs dados não salvos serão perdidos.');
    
    if (confirmar) {
        // Limpar localStorage
        removerLocal('vendaItens');
        removerLocal('vendaClienteAtual');
        
        // Redirecionar
        window.location.href = '/';
    }
}

// NOTA: a restauração do carrinho já é feita no DOMContentLoaded acima.
// Não duplicar com window.addEventListener('load') para evitar conflitos.
