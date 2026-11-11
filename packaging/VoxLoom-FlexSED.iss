#define AppVersion "0.2.2"
[Setup]
AppId={{E7154787-0A29-47F9-AC3F-031CA0F2C83A}
AppName=VoxLoom Studio
AppVersion={#AppVersion}
AppPublisher=MatSoftAI
DefaultDirName={localappdata}\Programs\VoxLoom Studio
DefaultGroupName=VoxLoom Studio
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=VoxLoom-Studio-Setup-0.2.2-Offline-win-x64
SetupIconFile=..\assets\voxloom.ico
UninstallDisplayIcon={app}\VoxLoom.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; Flags: unchecked

[Files]
Source: "..\dist-flexsed\VoxLoom\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\VoxLoom Studio"; Filename: "{app}\VoxLoom.exe"
Name: "{autodesktop}\VoxLoom Studio"; Filename: "{app}\VoxLoom.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VoxLoom.exe"; Description: "Открыть VoxLoom Studio"; Flags: nowait postinstall skipifsilent
