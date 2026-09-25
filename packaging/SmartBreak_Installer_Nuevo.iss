[Setup]
; Información General
AppName=SmartBreak
AppVersion=1.0.0
AppPublisher=LemonFabrica

; Directorio de Instalación (Requiere permisos de administrador por defecto)
DefaultDirName={autopf}\SmartBreak
DisableProgramGroupPage=yes

; Iconos e Interfaz
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\SmartBreak.exe

; Archivo de Salida (El Instalador final)
OutputDir=..\dist
OutputBaseFilename=SmartBreak_Instalador_v1.0

; Compresión Ultra (Reduce el peso del instalador significativamente)
Compression=lzma2/ultra64
SolidCompression=yes

; Arquitectura
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Iniciar SmartBreak al encender el equipo"; GroupDescription: "Arranque:"

[Files]
; Toma absolutamente todo el contenido de dist\SmartBreak y lo empaqueta
Source: "..\dist\SmartBreak\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\SmartBreak"; Filename: "{app}\SmartBreak.exe"
Name: "{autodesktop}\SmartBreak"; Filename: "{app}\SmartBreak.exe"; Tasks: desktopicon
; Acceso directo en la carpeta de inicio de Windows
Name: "{userstartup}\SmartBreak"; Filename: "{app}\SmartBreak.exe"; Tasks: startup

[Run]
Filename: "{app}\SmartBreak.exe"; Description: "Ejecutar SmartBreak ahora"; Flags: nowait postinstall skipifsilent
