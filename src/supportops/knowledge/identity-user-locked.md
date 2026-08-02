+++
id = "identity-user-locked"
title = "Usuário bloqueado no Active Directory ou Entra ID"
aliases = ["conta bloqueada", "account locked", "bloqueio no AD"]
category = "Identidade"
symptoms = ["Usuário não consegue entrar", "Mensagem de conta bloqueada"]
keywords = ["Active Directory", "Entra ID", "login", "bloqueio"]
risk_notes = ["Não desbloquear sem validar identidade", "Não coletar senha ou MFA"]
escalation_criteria = ["Bloqueios recorrentes", "Sinais de tentativa de acesso indevido"]
revision = "1.0.0"
+++
# Objetivo

Orientar a triagem segura de conta bloqueada sem executar desbloqueio administrativo.

## Evidências seguras

- Registre o horário, o serviço afetado e a mensagem genérica apresentada.
- Confirme se o bloqueio ocorre em um ou vários serviços corporativos.
- Solicite à equipe autorizada a consulta dos eventos de identidade, sem copiar tokens ou dados sensíveis.

## Orientação não executável

Valide a identidade pelo processo corporativo e encaminhe o desbloqueio do Active Directory ou Entra ID ao operador autorizado. Revise dispositivos com credenciais antigas.

## Pare e escale

Escale imediatamente diante de MFA inesperado, origem desconhecida ou bloqueio recorrente.
