; AutoHotkey v2 Script
; SHIFT+ENTER line continuation for JetBrains Rider and VS Code
; Replicates macOS Karabiner functionality on Windows

; JetBrains Rider - SHIFT+ENTER sends backslash + Enter
#HotIf WinActive("ahk_exe rider64.exe")
+Enter::Send("{\}{Enter}")
#HotIf

; Visual Studio Code - SHIFT+ENTER sends backslash + Enter  
#HotIf WinActive("ahk_exe Code.exe")
+Enter::Send("{\}{Enter}")
#HotIf

; WSL2 terminals - SHIFT+ENTER sends backslash + Enter
#HotIf WinActive("ahk_exe wsl.exe") || WinActive("ahk_exe WindowsTerminal.exe") || WinActive("ahk_exe conhost.exe")
+Enter::Send("{\}{Enter}")
#HotIf