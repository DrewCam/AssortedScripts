#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

^1:: ; All Current Vulnerabilities.
  Send Risk Modified is not equal to Accepted AND State is equal to Active, Resurfaced, New AND Severity is equal to Critical, High
Return

^2:: ; All New Vulnerabilities.
  Send First Seen between 00/01/2024 to 00/31/2024 AND Risk Modified is not equal to Accepted AND State is equal to Active, Resurfaced, New AND Severity is equal to High, Critical
Return

^3:: ; All New Vulnerabilities on Managed Devices.
  Send First Seen between 00/01/2024 to 00/31/2024 AND Risk Modified is not equal to Accepted AND State is equal to Active, Resurfaced, New AND Severity is equal to High, Critical AND Asset Tags is equal to Managed Devices: Network, Managed Devices: Endpoint, Managed Devices: Servers
Return

^4:: ; All New Vulnerabilities on Unmanaged Devices.
  Send First Seen between 00/01/2024 to 00/31/2024 AND Risk Modified is not equal to Accepted AND State is equal to Active, Resurfaced, New AND Severity is equal to High, Critical AND Asset Tags is not equal to Managed Devices: Network, Managed Devices: Endpoint, Managed Devices: Servers
Return

^5:: ; All Fixed Vulnerabilities on Managed Devices.
  Send Asset Tags is equal to Managed Devices: Network, Managed Devices: Servers, Managed Devices: Endpoint AND Last Seen between 00/01/2024 to 00/31/2024 AND Risk Modified is not equal to Accepted AND Severity is equal to High, Critical AND State is equal to Fixed 
Return

^6:: ; All newly discovered licensed assets.
  Send First Seen between 00/01/2024 to 00/31/2024 AND Licensed is equal to Yes
Return

^7:: ; All newly discovered unlicensed assets.
  Send First Seen between 00/01/2024 to 00/31/2024 AND Licensed is equal to No
Return