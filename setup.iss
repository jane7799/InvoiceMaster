; =====================================================================
; Inno Setup 配置文件 - 智能发票管理助手
; 支持 LZMA2 超高压缩、桌面快捷方式、开始菜单图标与完整卸载
; =====================================================================

#define MyAppName "智能发票管理助手"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "会钓鱼的猫"
#define MyAppExeName "智能发票打印助手.exe"
#ifndef OutputFileName
  #define OutputFileName "智能发票管理助手_安装包"
#endif

[Setup]
; 基础信息设置
AppId={{D37E8A1F-433E-493A-9457-3844BDD9942C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; 输出设置
OutputDir=dist_installer
OutputBaseFilename={#OutputFileName}

; 权限设置（免管理员提示安装到当前用户，若需要系统全局可改为 admin）
PrivilegesRequiredOverridesAllowed=commandline dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.CreateDesktopIcon=创建桌面快捷方式(&D)
english.AdditionalIcons=附加图标:
english.LaunchProgram=启动 {#MyAppName}
english.UninstallProgram=卸载 {#MyAppName}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; 包含 PyInstaller 出来的整个文件夹内容
Source: "dist\智能发票打印助手\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 创建开始菜单与桌面快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后提示启动
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
