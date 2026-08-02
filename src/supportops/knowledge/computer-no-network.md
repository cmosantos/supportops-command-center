+++
id = "computer-no-network"
title = "Computador sem acesso à rede"
aliases = ["sem internet", "rede indisponível", "offline"]
category = "Conectividade"
symptoms = ["Computador não acessa recursos internos", "Conexão aparece desconectada"]
keywords = ["rede", "Wi-Fi", "Ethernet", "DNS", "VPN"]
risk_notes = ["Não alterar configuração de rede administrativa", "Não desativar controles de segurança"]
escalation_criteria = ["Múltiplos usuários afetados", "Suspeita de incidente de segurança"]
revision = "1.0.0"
+++
# Objetivo

Orientar diagnóstico observacional de computador sem acesso à rede.

## Evidências seguras

- Identifique se a conexão é Wi-Fi, Ethernet ou VPN e quais serviços estão afetados.
- Observe indicadores físicos, estado exibido pelo sistema e se outros dispositivos autorizados funcionam.
- Registre horário e mensagens genéricas, sem executar comandos administrativos.

## Orientação não executável

Confira cabos, modo avião e seleção da rede conforme procedimentos do local. Encaminhe testes de DNS, endereço IP ou equipamento à equipe autorizada.

## Pare e escale

Escale quando o impacto for coletivo, houver alertas de segurança ou a correção exigir privilégio.
