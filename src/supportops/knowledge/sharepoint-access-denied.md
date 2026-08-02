+++
id = "sharepoint-access-denied"
title = "Acesso negado a pasta ou biblioteca do SharePoint"
aliases = ["SharePoint sem permissão", "biblioteca bloqueada", "pasta compartilhada negada"]
category = "Microsoft 365"
symptoms = ["Acesso negado ao abrir a biblioteca", "Pasta não aparece para o usuário"]
keywords = ["SharePoint", "biblioteca", "pasta", "permissão", "grupo"]
risk_notes = ["Não conceder acesso por link público", "Não ampliar grupos sem aprovação"]
escalation_criteria = ["Herança de permissão divergente", "Conteúdo sensível ou acesso excessivo"]
revision = "1.0.0"
+++
# Objetivo

Coletar evidências de acesso negado no SharePoint sem modificar permissões.

## Evidências seguras

- Registre o nome corporativo do site, biblioteca ou pasta e a mensagem apresentada.
- Confirme se o acesso esperado foi aprovado e se outros itens do mesmo site abrem.
- Peça à equipe proprietária a validação de grupo e herança, sem divulgar links sensíveis.

## Orientação não executável

Encaminhe a revisão de associação ao grupo e herança de permissões ao proprietário autorizado. Não crie link público nem altere grupos.

## Pare e escale

Pare se a mudança puder expor conteúdo sensível ou ampliar acesso além da solicitação aprovada.
