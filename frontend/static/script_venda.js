/**
 * Script Específico - Página de Vendas
 * Gerenciamento de itens, cálculos e finalização de vendas
 */

let itensVenda = [];
let clienteSelecionado = null;
let produtosDisponiveis = [];

// Inicializar a página de vendas
document.addEventListener('DOMContentLoaded', async () => {
    console.log('📦 Script de Vendas carregado');
    
    await carregarClientes();
    await carregarProdutos();
    
    // Event listeners
    document.getElementById('btn-adicionar').addEventListener('click', adicionarItem);
    document.getElementById('desconto-perc').addEventListener('change', recalcularTotais);
    document.getElementById('taxa').addEventListener('change', recalcularTotais);
    document.getElementById('btn-finalizar').addEventListener('click', finalizarVenda);
    document.getElementById('btn-cancelar').addEventListener('click', cancelarVenda);
    document.getElementById('cliente-select').addEventListener('change', selecionarCliente);
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

// Carregar produtos disponíveis
async function carregarProdutos() {
    try {
        const produtos = await requisicao('/api/produtos');
        const select = document.getElementById('produto-select');
        
        // Limpar opções
        select.innerHTML = '<option value="">-- Selecione um produto --</option>';
        
        // Adicionar produtos
        produtos.forEach(produto => {
            const option = document.createElement('option');
            option.value = produto.id_produto;
            option.textContent = `${produto.nome_produto} (R$ ${produto.preco.toFixed(2)})`;
            select.appendChild(option);
        });
        
        // Salvar globalmente
        produtosDisponiveis = produtos;
    } catch (erro) {
        console.error('Erro ao carregar produtos:', erro);
        mostrarAlerta('❌ Erro ao carregar produtos', 'erro');
    }
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
            infoEl.style.cssText = 'margin-top:0.5rem;padding:0.5rem;background:#f3e5f5;border-radius:8px;font-size:0.9rem;';
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
    
    // Verificar se produto já está na lista
    const itemExistente = itensVenda.find(i => i.id_produto === parseInt(idProduto));
    
    if (itemExistente) {
        // Aumentar quantidade
        itemExistente.quantidade += quantidade;
        itemExistente.subtotal = itemExistente.quantidade * itemExistente.preco_unitario;
    } else {
        // Adicionar novo item
        itensVenda.push({
            id_produto: parseInt(idProduto),
            nome_produto: produto.nome_produto,
            quantidade: quantidade,
            preco_unitario: parseFloat(produto.preco),
            subtotal: quantidade * parseFloat(produto.preco)
        });
    }
    
    // Resetar formulário
    document.getElementById('produto-select').value = '';
    document.getElementById('quantidade').value = '1';
    selectProduto.focus();
    
    // Atualizar interface
    renderizarItens();
    recalcularTotais();
    salvarLocal('vendaItens', itensVenda);
    
    mostrarAlerta(`✅ ${produto.nome_produto} adicionado!`, 'sucesso');
}

// Renderizar items na lista
function renderizarItens() {
    const lista = document.getElementById('itens-lista');
    
    if (itensVenda.length === 0) {
        lista.innerHTML = '<p class="placeholder">Nenhum item adicionado ainda...</p>';
        return;
    }
    
    lista.innerHTML = itensVenda.map((item, index) => `
        <div class="item-venda">
            <div>
                <div class="item-nome">${escapeHtml(item.nome_produto)}</div>
                <div class="item-valor">
                    Qtd: ${item.quantidade} × R$ ${item.preco_unitario.toFixed(2)} = 
                    <strong>${formatarMoeda(item.subtotal)}</strong>
                </div>
            </div>
            <button type="button" class="btn-remover" onclick="removerItem(${index})">
                ❌ Remover
            </button>
        </div>
    `).join('');
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

// Recalcular totais
function recalcularTotais() {
    // Subtotal
    const subtotal = itensVenda.reduce((total, item) => total + item.subtotal, 0);
    document.getElementById('subtotal').textContent = formatarMoeda(subtotal);
    
    // Desconto
    const descontoPerc = parseFloat(document.getElementById('desconto-perc').value) || 0;
    const descontoValor = subtotal * (descontoPerc / 100);
    document.getElementById('desconto-valor').textContent = formatarMoeda(descontoValor);
    
    // Taxa
    const taxa = parseFloat(document.getElementById('taxa').value) || 0;
    
    // Total final
    const totalFinal = subtotal - descontoValor + taxa;
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
        itens: itensVenda.map(item => ({
            id_produto: item.id_produto,
            quantidade: item.quantidade
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
        ${venda.itens.map(item => `
        ${item.produto_nome}
        Qtd: ${item.quantidade} × R$ ${item.preco_unitario.toFixed(2)} = R$ ${item.subtotal.toFixed(2)}
        `).join('')}
        
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

// Restaurar venda incompleta ao carregar página
window.addEventListener('load', () => {
    const itensRestaurados = obterLocal('vendaItens');
    const clienteRestaurado = obterLocal('vendaClienteAtual');
    
    if (itensRestaurados && itensRestaurados.length > 0) {
        const confirmar = confirm('📌 Você tem uma venda incompleta. Deseja continuar?');
        
        if (confirmar) {
            itensVenda = itensRestaurados;
            clienteSelecionado = clienteRestaurado;
            
            // Restaurar seleção do cliente
            if (clienteSelecionado && clienteSelecionado.id_cliente) {
                document.getElementById('cliente-select').value = clienteSelecionado.id_cliente;
            }
            
            renderizarItens();
            recalcularTotais();
        } else {
            removerLocal('vendaItens');
            removerLocal('vendaClienteAtual');
        }
    }
});
