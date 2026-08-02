+++
id = "shared-mailbox-access-denied"
title = "Acesso negado à caixa compartilhada no Outlook"
aliases = ["caixa compartilhada", "shared mailbox", "Outlook sem permissão"]
category = "Microsoft 365"
symptoms = ["Acesso negado ao abrir a caixa", "A caixa não aparece no Outlook"]
keywords = ["Outlook", "mailbox", "permissão", "automapping"]
risk_notes = ["Não alterar permissões sem autorização", "Não solicitar credenciais"]
escalation_criteria = ["Permissão ausente ou divergente", "Falha persiste em mais de um cliente"]
revision = "1.0.0"
+++
# Objetivo

Orientar a coleta segura de evidências quando uma caixa compartilhada apresenta acesso negado.

## Evidências seguras

- Registre a mensagem exibida, o horário e se a caixa aparece no Outlook Web.
- Confirme com o responsável apenas o nome corporativo da caixa e o tipo de acesso esperado.
- Compare o comportamento em uma sessão autorizada do Outlook Web, sem coletar senha ou token.

## Orientação não executável

Verifique se a solicitação de acesso foi aprovada e encaminhe a conferência de Full Access e automapping à equipe autorizada. Não execute PowerShell nem altere delegações.

## Pare e escale

Interrompa se houver suspeita de comprometimento, acesso a dados indevidos ou necessidade de privilégio administrativo.
