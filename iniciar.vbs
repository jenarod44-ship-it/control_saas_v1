Set objShell = CreateObject("Wscript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

objShell.Run "cmd /c cd /d """ & strPath & """ && iniciar.bat", 0

Set objShell = Nothing
Set objFSO = Nothing
