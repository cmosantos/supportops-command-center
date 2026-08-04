+++
id = "onedrive-not-syncing"
title = "OneDrive is not synchronizing"
aliases = ["OneDrive stopped", "files are not syncing", "sync pending"]
category = "Microsoft 365"
symptoms = ["The synchronization icon remains pending", "Local files do not reach the cloud"]
keywords = ["OneDrive", "synchronization", "cloud", "quota"]
risk_notes = ["Do not delete local copies", "Do not reset the client without a validated backup"]
escalation_criteria = ["Possible data loss", "The library or account is unavailable"]
revision = "1.0.0"
+++
# Objective

Collect evidence for a OneDrive synchronization failure while preserving files.

## Safe evidence

- Observe the icon status, the approximate number of pending items, and the last successful synchronization.
- Check available local space, the reported quota, and whether the authorized web portal opens normally.
- Record generic error names without copying confidential file content.

## Non-executable guidance

Confirm connectivity and account status. Instruct the user to keep local files intact until the authorized team evaluates conflicts, quota, or the library connection.

## Stop and escalate

Stop before unlinking, resetting, or deleting any folder when there is a risk of data loss.
