+++
id = "shared-mailbox-access-denied"
title = "Shared mailbox access denied in Outlook"
aliases = ["shared mailbox", "mailbox access denied", "Outlook permission error"]
category = "Microsoft 365"
symptoms = ["Access denied when opening the mailbox", "The mailbox does not appear in Outlook"]
keywords = ["Outlook", "mailbox", "permission", "automapping"]
risk_notes = ["Do not change permissions without authorization", "Do not request credentials"]
escalation_criteria = ["Permission is missing or inconsistent", "The issue persists in more than one client"]
revision = "1.0.0"
+++
# Objective

Guide safe evidence collection when access to a shared mailbox is denied.

## Safe evidence

- Record the displayed message, the time, and whether the mailbox appears in Outlook on the web.
- Confirm only the corporate mailbox name and the expected access type with the responsible owner.
- Compare the behavior in an authorized Outlook on the web session without collecting a password or token.

## Non-executable guidance

Confirm that the access request was approved and route the Full Access and automapping verification to the authorized team. Do not run PowerShell or change delegation settings.

## Stop and escalate

Stop if there is suspected compromise, possible access to unauthorized data, or any need for administrative privilege.
