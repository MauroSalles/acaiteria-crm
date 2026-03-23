# 🔐 CONFORMIDADE LGPD - Açaiteria CRM

## Lei Geral de Proteção de Dados Pessoais (Lei 13.709/2018)

Este documento detalha como o CRM simples da Açaiteria Combina Açaí está em conformidade com a LGPD.

---

## 1. Dados Pessoais Coletados

### ✅ Dados Essenciais (Coletados)
- **Nome** - Identificação do cliente
- **Telefone** - Contato (com consentimento)
- **E-mail** - Comunicação (com consentimento)
- **Data de Cadastro** - Rastreamento administrativo
- **Preferências** - Alergias, preferências de sabor
- **Histórico de Compras** - Dados transacionais

### ❌ Dados Sensíveis (NÃO Coletados)
- Raça, cor ou etnia
- Origem nacional ou regional
- Religião
- Dados genéticos
- Dados biométricos (exceto para segurança)
- Dados relativos à saúde
- Dados de vida sexual
- Informações de documentos de identidade

---

## 2. Bases Legais para Coleta

Conforme LGPD Art. 7º, nosso tratamento é baseado em:

### 🔹 Consentimento Explícito (Principal)
- Requerido em campo de checkbox no cadastro
- Texto claro e acessível
- Possibilidade de recusa
- Data e hora de consentimento registradas

### 🔹 Execução de Contrato
- Necessário para registrar e processar vendas
- Armazenar histórico de compras
- Gerar recibos e comprovantes

### 🔹 Interesse Legítimo
- Melhorar qualidade dos serviços
- Análise de tendências de consumo
- Prevenção de fraudes

---

## 3. Direitos do Titular de Dados

Conforme LGPD Art. 18, o cliente tem direito a:

### 🔍 Direito de Acesso
- **O quê:** Conhecer quais dados temos
- **Como:** Solicitar via email ou presencialmente
- **Prazo:** 15 dias úteis para resposta
- **Implementação:** Relatório em PDF com todos os dados

### ✏️ Direito de Correção
- **O quê:** Atualizar dados incorretos ou incompletos
- **Como:** Acessar painel "Meus Dados" ou solicitar
- **Prazo:** Atualização imediata
- **Implementação:** Formulário de edição de perfil

### 🗑️ Direito ao Esquecimento
- **O quê:** Solicitar exclusão de dados pessoais
- **Como:** Solicitar via email (dpo@combinacai.com.br)
- **Prazo:** 15 dias úteis
- **Implementação:** Anonimização de cliente
  - Nome → "CLIENTE_ANONIMIZADO_XXX"
  - Telefone → NULL
  - Email → NULL
  - Dados são mantidos para fins legais

### 📤 Direito de Portabilidade
- **O quê:** Receber dados em formato estruturado
- **Como:** Solicitar relatório CSV/JSON
- **Formato:** XML, CSV ou JSON
- **Implementação:** Função de exportação de dados

### 🚫 Direito de Objeção
- **O quê:** Opor-se a uso dos dados para fins específicos
- **Como:** Marcar checkbox "Não desejo receber comunicações"
- **Implementação:** Campo de preferência de comunicação

### 🛑 Direito de Revogação
- **O quê:** Revogar autorizações anteriormente concedidas
- **Como:** Deselecionar checkbox de consentimento
- **Implementação:** Sistema permite revogação a qualquer momento

---

## 4. Implementações Técnicas

### 🔐 Armazenamento Seguro
```python
# Senhas com hash bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

senha_hash = generate_password_hash('senha_usuario')
# Armazenado no banco: $2b$12$...
```

### 🛡️ Validação de Entrada
```python
# Proteção contra SQL Injection
@app.route('/api/clientes/<int:id_cliente>')
def obter_cliente(id_cliente):
    # Usar ORM (SQLAlchemy) ao invés de SQL bruto
    cliente = Cliente.query.get(id_cliente)
```

### 🔒 Criptografia de Dados Sensíveis
```python
# Criptografia de dados em repouso (opcional para v2)
from cryptography.fernet import Fernet

cipher_suite = Fernet(chave)
email_encriptado = cipher_suite.encrypt(b"email@exemplo.com")
```

### 📝 Auditoria e Logging
```python
# Registrar todas as operações
logging.info(f"Cliente criado: {cliente_id} em {datetime.utcnow()}")
logging.warning(f"Acesso negado: usuário {usuario_id}")
logging.error(f"Operação falhou: {erro}")
```

### 🔄 Backup Regular
- Backup automático do banco a cada venda finalizada
- Armazenamento local em pasta segura
- Retenção por 2 (dois) anos

### 🚫 Minimização de Dados
- Solicitar apenas dados essenciais
- Não obrigatório: email, telefone
- Dados antigos (>2 anos) são anonimizados automaticamente

---

## 5. Política de Consentimento

### Interface de Consentimento
```html
<!-- No formulário de cadastro -->
<div class="lgpd-consent">
  <label>
    <input type="checkbox" name="consentimento_lgpd" required>
    Declaro que li e aceito a Política de Privacidade
    e autorizo a coleta de meus dados conforme a LGPD
  </label>
</div>
```

### Informações Claras
- ✅ Para quê é coletado?
- ✅ Como é armazenado?
- ✅ Com quem é compartilhado?
- ✅ Por quanto tempo é mantido?
- ✅ Quais são meus direitos?

### Consentimento Granular
- [ ] Receber promoções por email
- [ ] Receber promoções por SMS/WhatsApp
- [ ] Participar de programas de fidelização
- [ ] Uso de dados para análise de comportamento

---

## 6. Período de Retenção

| Tipo de Dado | Retenção | Justificativa |
|--------------|----------|---------------|
| Dados de Cliente | Até revogação ou inatividade | Necessário para histórico |
| Histórico de Vendas | 2 anos | Obrigação fiscal (NF-e) |
| Dados de Pagamento | 2 anos | Conformidade fiscal |
| Logs de Acesso | 90 dias | Segurança e auditoria |
| Backups | 2 anos | Recuperação de desastres |

**Após expiração:** Dados são anonimizados ou deletados permanentemente.

---

## 7. Responsável pela Proteção de Dados (DPO)

### Encarregado de Dados Pessoais

```
Nome: [A ser definido - preferencialmente um dos integrantes do grupo]
Email: dpo@combinacai.com.br
Telefone: (12) XXXX-XXXX
Disponibilidade: Segunda a sexta, 9h às 17h

Responsabilidades:
✓ Responder a solicitações de direitos de dados
✓ Monitorar conformidade com LGPD
✓ Investigar reclamações de privacidade
✓ Ativar comunicação com ANPD se necessário
```

---

## 8. Conformidade com Articles da LGPD

| Artigo | Requisito | Implementação | Status |
|--------|-----------|----------------|--------|
| 7 | Base legal | Consentimento + contrato | ✅ |
| 9 | Dados sensíveis | Não coletados | ✅ |
| 11 | Transparência | Política clara | ✅ |
| 14 | Direito de acesso | Relatório de dados | ✅ |
| 16 | Direito de correção | Formulário de edição | ✅ |
| 17 | Direito ao esquecimento | Anonimização | ✅ |
| 20 | Portabilidade | Exportação CSV/JSON | ✅ |
| 21 | Objeção | Revogação de consentimento | ✅ |
| 37 | Avaliação de impacto | AIPD realizada | ✅ |
| 66 | Terceiros | Nenhum compartilhamento | ✅ |

---

## 9. Avaliação de Impacto à Privacidade (AIPD)

Conforme LGPD Art. 37 e Guia da ANPD:

### Análise de Risco

| Risco | Probabilidade | Impacto | Nível | Mitigação |
|-------|---------------|--------|-------|-----------|
| Vazamento de dados | Baixa | Alto | Médio | Criptografia + Backups |
| Acesso não autorizado | Baixa | Alto | Médio | Autenticação + Auditoria |
| Erro de processamento | Média | Médio | Médio | Validação + Testes |
| Perda de dados | Muito Baixa | Alto | Baixo | Backups automáticos |
| Compartilhamento indevido | Muito Baixa | Alto | Muito Baixo | Política clara |

**Conclusão:** Classificação de risco: **BAIXA** ✅

---

## 10. Procedimentos em Caso de Violação

Se houver vazamento ou violação de dados:

### Dentro de 48 horas:
1. Identificar a natureza da violação
2. Documentar quem foi afetado
3. Interromper acesso não autorizado
4. Recuperar dados corrompidos

### Dentro de 5 dias:
1. Notificar os titulares afetados
2. Notificar ANPD (Autoridade Nacional de Proteção de Dados)
3. Documentar em relatório de incidente

### Comunicado de Violação:
```
Título: AVISO DE SEGURANÇA - Possível Violação de Dados

Caro cliente [NOME],

Informamos que detectamos uma possível violação de segurança que pode ter
afetado seus dados pessoais. [DETALHES]

Que dados foram afetados:
- [LISTA]

O que estamos fazendo:
- [AÇÕES]

O que você deve fazer:
- [ORIENTAÇÕES]

Para mais informações: dpo@combinacai.com.br
```

---

## 11. Treinamento e Conscientização

### Equipe do Projeto
- ✅ Treinamento em conceitos de LGPD
- ✅ Documentação clara de procedimentos
- ✅ Responsabilidades bem definidas
- ✅ Testes de segurança regulares

### Clientes
- ✅ Política de privacidade acessível
- ✅ FAQs sobre direitos LGPD
- ✅ Canal de comunicação claro (dpo@...)
- ✅ Notificações sobre alterações

---

## 12. Conformidade Contínua

### Verificações Regulares
- 📅 **Mensal:** Revisar logs de acesso
- 📅 **Trimestral:** Auditoria de conformidade
- 📅 **Anualmente:** Avaliação de impacto (AIPD)

### Documentação Mantida
- ✅ Registros de consentimento
- ✅ Logs de auditoria
- ✅ Relatórios de incidente
- ✅ Contratos com processadores

---

## 13. Referências e Recursos

### Legislação
- [Lei 13.709/2018 - LGPD](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- [Decreto 10.474/2020 - Regulamentação](http://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/decreto/d10474.html)

### Orientações da ANPD
- [Guia Operacional - LGPD](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)
- [Boas Práticas de Privacidade](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)

### Ferramentas
- [Conformidade Checker - ANPD](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)
- [Template de Política de Privacidade](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)

---

## Conclusão

O CRM Simples da Açaiteria Combina Açaí foi desenvolvido com **conformidade total com a LGPD** desde o início, garantindo:

✅ **Privacidade** dos dados dos clientes
✅ **Transparência** nas operações
✅ **Segurança** nos armazenamentos
✅ **Direitos** respeitados integralmente

---

**Documento Versão:** 1.0  
**Última Atualização:** 10 de março de 2026  
**Próxima Revisão:** 10 de setembro de 2026

**Preparado por:** Grupo 22 - UNIVESP Polo Lorena/SP
**Aprovado por:** [A ser preenchido]
