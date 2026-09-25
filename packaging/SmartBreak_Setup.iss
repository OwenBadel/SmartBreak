; ==============================================================================
; Script de Inno Setup para compilar el Instalador Oficial de SmartBreak
; Genera Setup.exe con accesos directos y opción de autoarranque con Windows
; ==============================================================================

#define MyAppName "SmartBreak"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Lemon Software Factory"
#define MyAppURL "https://github.com/OwenBadel/Fabrica_Software"
#define MyAppExeName "SmartBreak.exe"

[Setup]
; Identificador de la aplicación
AppId={{9B7F1C42-E931-4A5D-82F3-C8A4D17B60E2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Directorio y nombre del archivo instalador generado
OutputDir=..\installer_output
OutputBaseFilename=SmartBreak_Setup_v1.0.0
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Iniciar SmartBreak automáticamente al encender Windows"; GroupDescription: "Opciones de Inicio:"

[Files]
Source: "..\dist\SmartBreak\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\icon.ico"

; ------------------------------------------------------------------------------
; Autoarranque con Windows (Registro de Usuario Actual)
; ------------------------------------------------------------------------------
[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SmartBreak"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
