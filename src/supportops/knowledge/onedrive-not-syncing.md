+++
id = "onedrive-not-syncing"
title = "OneDrive sem sincronização"
aliases = ["OneDrive parado", "arquivos não sincronizam", "sync pendente"]
category = "Microsoft 365"
symptoms = ["Ícone de sincronização permanece pendente", "Arquivos locais não chegam à nuvem"]
keywords = ["OneDrive", "sincronização", "nuvem", "quota"]
risk_notes = ["Não excluir cópias locais", "Não redefinir o cliente sem backup validado"]
escalation_criteria = ["Possível perda de dados", "Biblioteca ou conta indisponível"]
revision = "1.0.0"
+++
# Objetivo

Coletar evidências para falha de sincronização do OneDrive preservando os arquivos.

## Evidências seguras

- Observe o estado do ícone, a quantidade aproximada de itens pendentes e a última sincronização.
- Verifique espaço local, quota informada e se o portal autorizado abre normalmente.
- Registre nomes de erro genéricos; não copie conteúdo confidencial dos arquivos.

## Orientação não executável

Confirme conectividade e status da conta. Oriente o usuário a manter os arquivos locais intactos até a equipe autorizada avaliar conflito, quota ou vínculo da biblioteca.

## Pare e escale

Pare antes de desvincular, redefinir ou excluir qualquer pasta quando existir risco de perda de dados.
