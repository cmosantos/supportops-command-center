+++
id = "identity-user-locked"
title = "User locked in Active Directory or Entra ID"
aliases = ["account locked", "locked user", "Active Directory lockout"]
category = "Identity"
symptoms = ["The user cannot sign in", "A locked-account message is displayed"]
keywords = ["Active Directory", "Entra ID", "login", "lockout"]
risk_notes = ["Do not unlock the account before validating identity", "Do not collect passwords or MFA codes"]
escalation_criteria = ["Repeated lockouts", "Signs of unauthorized access attempts"]
revision = "1.0.0"
+++
# Objective

Guide the safe triage of a locked account without performing an administrative unlock.

## Safe evidence

- Record the time, the affected service, and the generic message shown to the user.
- Confirm whether the lockout affects one or several corporate services.
- Ask the authorized team to review identity events without copying tokens or sensitive data.

## Non-executable guidance

Validate identity through the corporate process and route the Active Directory or Entra ID unlock to an authorized operator. Review devices that may still store old credentials.

## Stop and escalate

Escalate immediately when there is unexpected MFA activity, an unknown source, or repeated lockouts.
