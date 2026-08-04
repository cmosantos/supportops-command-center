+++
id = "computer-no-network"
title = "Computer without network access"
aliases = ["no internet", "network unavailable", "offline computer"]
category = "Connectivity"
symptoms = ["The computer cannot access internal resources", "The connection appears disconnected"]
keywords = ["network", "Wi-Fi", "Ethernet", "DNS", "VPN"]
risk_notes = ["Do not change administrative network settings", "Do not disable security controls"]
escalation_criteria = ["Multiple users are affected", "A security incident is suspected"]
revision = "1.0.0"
+++
# Objective

Guide an observational diagnosis of a computer without network access.

## Safe evidence

- Identify whether the connection uses Wi-Fi, Ethernet, or VPN and which services are affected.
- Observe physical indicators, the operating-system status, and whether other authorized devices work.
- Record the time and generic messages without running administrative commands.

## Non-executable guidance

Check cables, airplane mode, and the selected network according to local procedures. Route DNS, IP address, or network-equipment tests to the authorized team.

## Stop and escalate

Escalate when the impact is widespread, security alerts are present, or remediation requires elevated privilege.
