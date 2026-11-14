#ifndef AppVersion
  #define AppVersion "0.4.1"
#endif
#ifndef BundleDir
  #define BundleDir "..\dist-native\VoxLoom"
#endif
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
OutputDir=..\release-native
OutputBaseFilename=VoxLoom-Studio-{#AppVersion}-windows-x64
SetupIconFile=..\assets\voxloom.ico
UninstallDisplayIcon={app}\VoxLoom.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
LanguageDetectionMethod=none

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\VoxLoom Studio"; Filename: "{app}\VoxLoom.exe"
Name: "{autodesktop}\VoxLoom Studio"; Filename: "{app}\VoxLoom.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VoxLoom.exe"; Description: "{cm:LaunchProgram,VoxLoom Studio}"; Flags: nowait postinstall skipifsilent
