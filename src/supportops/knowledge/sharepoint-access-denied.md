+++
id = "sharepoint-access-denied"
title = "SharePoint folder or library access denied"
aliases = ["SharePoint permission denied", "blocked library", "shared folder access denied"]
category = "Microsoft 365"
symptoms = ["Access denied when opening the library", "The folder does not appear for the user"]
keywords = ["SharePoint", "library", "folder", "permission", "group"]
risk_notes = ["Do not grant access through a public link", "Do not expand groups without approval"]
escalation_criteria = ["Permission inheritance is inconsistent", "Sensitive content or excessive access is involved"]
revision = "1.0.0"
+++
# Objective

Collect evidence for denied SharePoint access without changing permissions.

## Safe evidence

- Record the corporate site, library, or folder name and the displayed message.
- Confirm that the expected access was approved and whether other items in the same site open normally.
- Ask the owning team to validate group membership and inheritance without exposing sensitive links.

## Non-executable guidance

Route group-membership and permission-inheritance review to the authorized owner. Do not create a public link or change groups.

## Stop and escalate

Stop if the change could expose sensitive content or expand access beyond the approved request.
