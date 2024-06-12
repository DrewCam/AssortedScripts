#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

^1::
  ; Filters sign-in logs where the Identity matches the value copied to the clipboard.
  Send SigninLogs{Enter}| where Identity == "^v{Backspace}" + {Enter}
Return

^2::
  ; Projects detailed sign-in log information, including geographic IP info and device details.
  Send | project TimeGenerated, AppDisplayName, Identity, geo_info_from_ip_address(IPAddress), IPAddress, ResultDescription, ResultType, AuthenticationRequirement, DeviceDetail
  Send +{Enter}
Return

^3::
  ; Filters sign-in logs based on the IP address copied to the clipboard.
  Send SigninLogs{Enter}| where IPAddress == "^v" + {Enter}
Return

^4::
  ; Summarizes sign-in logs by device detail and IP address, counting occurrences.
  Send | summarize count() by tostring(DeviceDetail), IPAddress
  Send +{Enter}
Return

^5::
  ; Filters the logs to show entries from the last 90 days.
  Send | where TimeGenerated > ago(90d) + {Enter}
Return

^6::
  ; Starts querying sign-in logs, filters by IP address, and projects multi-factor authentication details.
  Send SigninLogs{Enter}
  Send | where IPAddress == "^v{Backspace}"{Enter}+{Enter}
  Send | project MfaDetail
Return  

^7::
  ; Filters sign-in logs by the copied IP address and projects detailed log information.
  Send SigninLogs{Enter}| where IPAddress == "^v" + {Enter}
  Send | project TimeGenerated, AppDisplayName, Identity, IPAddress, ResultDescription, ResultType, AuthenticationRequirement, DeviceDetail
  Send +{Enter}
Return

^R::
  ; A robust query that filters sign-in logs by IP address and projects detailed information, including geographic IP info.
  Send SigninLogs{Enter}| where IPAddress == "^v" + {Enter}
  Send | project TimeGenerated, AppDisplayName, Identity, geo_info_from_ip_address(IPAddress), IPAddress, ResultDescription, ResultType, AuthenticationRequirement, DeviceDetail
  Send +{Enter}
Return