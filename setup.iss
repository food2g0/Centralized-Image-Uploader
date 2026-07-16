#define MyAppPublisher "IT Department"

[Setup]
AppName=RMS
AppVersion=1.1.6
AppId={{16840CC5-6EFE-469E-AE8F-5F247F75899B}}
DefaultDirName=C:\Record Management System
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=admin
CreateUninstallRegKey=yes
ArchitecturesInstallIn64BitMode=x64os
OutputDir=output
AppPublisher=IT DEPARTMENT
OutputBaseFilename=installer
SetupIconFile="E:\Centralized Image Uploader\Logo.ico"

[Files]
Source: "E:\Centralized Image Uploader\dist\main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "E:\Centralized Image Uploader\dist\serviceAccountKey.json"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
; Delete shortcuts
Type: files; Name: "{commondesktop}\RMS.lnk"
Type: files; Name: "{userdesktop}\RMS.lnk"
Type: files; Name: "{commonstartmenu}\RMS\RMS.lnk"
Type: files; Name: "{commonstartmenu}\RMS\Uninstall RMS.lnk"
Type: dirifempty; Name: "{commonstartmenu}\RMS"
Type: files; Name: "{commondesktop}\Old RMS.lnk"
Type: files; Name: "{userdesktop}\Old RMS.lnk"

; Delete your main application files specifically
Type: files; Name: "{app}\main.exe"
Type: files; Name: "{app}\serviceAccountKey.json"
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{commondesktop}\RMS"; Filename: "{app}\main.exe"; IconFilename: "{app}\Logo.ico"; WorkingDir: "{app}"
Name: "{commonstartmenu}\RMS\RMS"; Filename: "{app}\main.exe"; IconFilename: "{app}\Logo.ico"; WorkingDir: "{app}"
Name: "{commonstartmenu}\RMS\Uninstall RMS"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\main.exe"; Description: "Launch RMS"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"
Filename: "cmd.exe"; Parameters: "/c echo 1.1.6 > ""{app}\version.txt"""; Flags: runhidden
