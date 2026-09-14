; Inno Setup Script for Text Analysis Manager
; Enhanced Full Installation Program
; Download Inno Setup from: https://jrsoftware.org/isinfo.php

#define MyAppName "Text Analysis Manager"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Research Database Solutions"
#define MyAppURL "https://github.com/research-db-manager"
#define MyAppExeName "TextAnalysisManager.exe"
#define MyAppId "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}"

[Setup]
; Application information
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (c) 2024-2026 Research Database Solutions
AppReadmeFile={app}\README.txt
AppContact={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
DisableProgramGroupPage=no
DisableDirPage=no
DisableReadyPage=no
DisableFinishedPage=no

; Output settings
OutputDir=installer_output
OutputBaseFilename=TextAnalysisManager_Setup_{#MyAppVersion}
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardImageFile=
WizardSmallImageFile=

; Compression settings
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=2

; Installer appearance
WizardStyle=modern
WizardSizePercent=110,110
WizardImageStretch=no
WizardImageBackColor=clWhite

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Version info
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup Installer
VersionInfoCopyright=Copyright (c) 2024-2026 Research Database Solutions
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoProductTextVersion={#MyAppVersion}

; Minimum Windows version (Windows 7 SP1)
MinVersion=6.1sp1

; File associations
ChangesAssociations=no

; Uninstaller settings
UninstallDisplayName={#MyAppName}
UninstallDisplaySize=200
CreateUninstallRegKey=yes
UninstallFilesDir={app}

; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; License
LicenseFile=LICENSE.txt

; Info before/after
InfoBeforeFile=
InfoAfterFile=README.txt

; Setup log
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "Full installation"
Name: "compact"; Description: "Compact installation (minimal components)"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "main"; Description: "Main application files"; Types: full compact custom; Flags: fixed
Name: "main\core"; Description: "Core application files"; Types: full compact custom; Flags: fixed
Name: "main\documentation"; Description: "Documentation and help files"; Types: full custom
Name: "shortcuts"; Description: "Shortcuts and Start Menu entries"; Types: full compact custom; Flags: fixed
Name: "shortcuts\desktop"; Description: "Desktop shortcut"; Types: full custom
Name: "shortcuts\startmenu"; Description: "Start Menu shortcut"; Types: full compact custom; Flags: fixed

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Components: shortcuts\desktop; Flags: unchecked
Name: "startup"; Description: "Start {#MyAppName} when Windows starts"; GroupDescription: "Startup"; Flags: unchecked
Name: "associate"; Description: "Associate with research database files"; GroupDescription: "File associations"; Flags: unchecked

[Files]
; Main application files from PyInstaller dist folder
Source: "dist\TextAnalysisManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main\core

; License and documentation
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion; Components: main\documentation
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme; Components: main\documentation

[Dirs]
; Create data directories with user write permissions
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\backups"; Permissions: users-modify
Name: "{app}\config"; Permissions: users-modify
Name: "{userappdata}\TextAnalysisManager"; Permissions: users-modify
Name: "{userappdata}\TextAnalysisManager\data"; Permissions: users-modify
Name: "{userappdata}\TextAnalysisManager\backups"; Permissions: users-modify
Name: "{userappdata}\TextAnalysisManager\logs"; Permissions: users-modify
Name: "{userappdata}\TextAnalysisManager\saved_reports"; Permissions: users-modify

[Icons]
; Start Menu shortcuts
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Components: shortcuts\startmenu
Name: "{autoprograms}\{#MyAppName}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Components: shortcuts\startmenu

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: shortcuts\desktop

; Startup shortcut
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: startup

[Registry]
; Application registry entries (HKCU = per-user, no admin required)
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "DataPath"; ValueData: "{userappdata}\TextAnalysisManager"; Flags: uninsdeletekey

; Note: Uninstall registry key is created automatically by Inno Setup in HKCU when
; PrivilegesRequired=lowest. Custom HKLM entries were removed - they caused "Access denied"
; errors because HKLM requires admin rights.

[Run]
; Option to run application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent; Check: ShouldRunAfterInstall

[UninstallDelete]
; Clean up log files on uninstall
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\*.log"
Type: dirifempty; Name: "{app}\data"
Type: dirifempty; Name: "{app}\backups"
Type: dirifempty; Name: "{app}"

[Messages]
WelcomeLabel1=Welcome to the [name] Setup Wizard
WelcomeLabel2=This will install [name/ver] on your computer.%n%nText Analysis Manager is a comprehensive tool for organizing, analyzing, and reporting research data.%n%nIt is recommended that you close all other applications before continuing.
FinishedLabelNoIcons=Setup has finished installing [name] on your computer.
FinishedLabel=Setup has finished installing [name] on your computer.%n%n[name] has been installed to:%n%n[code:GetInstallPath]%n%nYour data will be stored in:%n%n[code:GetDataPath]

[Code]
const
  NewLine = #13#10;
  Tab = #9;

var
  UninstallDataPage: TOutputProgressWizardPage;

// Check if a previous version is installed
function InitializeSetup(): Boolean;
var
  PrevVersion: String;
  UninstallString: String;
  ErrorCode: Integer;
begin
  Result := True;
  
  // Check for previous installation
  if RegQueryStringValue(HKEY_LOCAL_MACHINE, 
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppId}_is1',
    'DisplayVersion', PrevVersion) then
  begin
    if MsgBox('A previous version (' + PrevVersion + ') of {#MyAppName} is already installed.' + NewLine + NewLine +
              'It is recommended that you uninstall the previous version before installing this one.' + NewLine + NewLine +
              'Do you want to continue with the installation?',
              mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDNO then
    begin
      Result := False;
      Exit;
    end;
    
    // Try to uninstall previous version
    if RegQueryStringValue(HKEY_LOCAL_MACHINE,
      'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppId}_is1',
      'UninstallString', UninstallString) then
    begin
      if MsgBox('Would you like to uninstall the previous version now?', 
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        // Extract the uninstaller path
        StringChangeEx(UninstallString, '"', '', True);
        if Exec(UninstallString, '/SILENT', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode) then
        begin
          // Wait a bit for the uninstaller to finish
          Sleep(2000);
        end;
      end;
    end;
  end;
  
  // Disk space check removed - GetSpaceOnDisk may not be available in all Inno Setup versions
  // Windows will handle disk space warnings automatically during installation
end;

// Initialize wizard pages
procedure InitializeWizard();
begin
  // Wizard initialization - can add custom pages here if needed
end;

// Handle step changes
procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    AppDataPath := ExpandConstant('{userappdata}\TextAnalysisManager');
    
    // Create user data directories
    if not DirExists(AppDataPath) then
    begin
      CreateDir(AppDataPath);
    end;
    
    CreateDir(AppDataPath + '\data');
    CreateDir(AppDataPath + '\backups');
    CreateDir(AppDataPath + '\logs');
    CreateDir(AppDataPath + '\saved_reports');
    
    // Set permissions
    try
      // Note: Setting permissions requires admin rights
      // The directories are created with default permissions
    except
      // Ignore permission errors if not admin
    end;
    
    // Write installation info
    SaveStringToFile(AppDataPath + '\install_info.txt',
      'Installation Date: ' + GetDateTimeString('yyyy/mm/dd hh:nn:ss', #0, #0) + NewLine +
      'Installation Path: ' + ExpandConstant('{app}') + NewLine +
      'Version: {#MyAppVersion}' + NewLine +
      'Installer Version: {#MyAppVersion}' + NewLine,
      False);
  end;
end;

// Handle uninstaller initialization
function InitializeUninstall(): Boolean;
var
  AppDataPath: String;
begin
  Result := True;
  
  // Check if application is running
  if CheckForMutexes('{#MyAppName}') then
  begin
    if MsgBox('{#MyAppName} appears to be running.' + NewLine + NewLine +
              'Please close {#MyAppName} and click Retry, or click Cancel to exit.',
              mbError, MB_RETRYCANCEL) = IDRETRY then
    begin
      Result := False;
      Exit;
    end
    else
    begin
      Result := False;
      Exit;
    end;
  end;
  
  // Create uninstall progress page
  UninstallDataPage := CreateOutputProgressPage('Uninstalling {#MyAppName}', 
    'Please wait while {#MyAppName} is being uninstalled.');
  
  AppDataPath := ExpandConstant('{userappdata}\TextAnalysisManager');
  
  // Check if data exists
  if DirExists(AppDataPath) then
  begin
    // Ask user about data preservation
    if MsgBox('Do you want to remove all user data and settings?' + NewLine + NewLine +
              'This includes:' + NewLine +
              Tab + 'Database files' + NewLine +
              Tab + 'Configuration settings' + NewLine +
              Tab + 'Backup files' + NewLine +
              Tab + 'Log files' + NewLine +
              Tab + 'Saved reports' + NewLine + NewLine +
              'Location: ' + AppDataPath + NewLine + NewLine +
              'Click Yes to remove all data, or No to keep it.',
              mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
    begin
      // Data will be removed in CurUninstallStepChanged
    end;
  end;
end;

// Handle uninstall step changes
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDataPath: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    UninstallDataPage.Show;
    UninstallDataPage.SetProgress(0, 100);
    UninstallDataPage.SetText('Removing application files...', '');
    Sleep(500);
    UninstallDataPage.SetProgress(50, 100);
  end;
  
  if CurUninstallStep = usPostUninstall then
  begin
    AppDataPath := ExpandConstant('{userappdata}\TextAnalysisManager');
    
    if DirExists(AppDataPath) then
    begin
      UninstallDataPage.SetText('Removing user data...', '');
      UninstallDataPage.SetProgress(75, 100);
      
      // Check if user wanted to remove data (from InitializeUninstall)
      // For now, we'll ask again to be safe
      if MsgBox('Remove all user data and settings from:' + NewLine + AppDataPath + '?',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        try
          DelTree(AppDataPath, True, True, True);
        except
          // If deletion fails, show message
          MsgBox('Some files could not be removed. You may need to delete them manually:' + NewLine + AppDataPath,
                 mbError, MB_OK);
        end;
      end;
    end;
    
    UninstallDataPage.SetProgress(100, 100);
    UninstallDataPage.Hide;
  end;
end;

// Helper function to check if application should run after install
function ShouldRunAfterInstall(): Boolean;
begin
  Result := not WizardSilent();
end;

// Helper function to get data path
function GetDataPath(Param: String): String;
begin
  Result := ExpandConstant('{userappdata}\TextAnalysisManager');
end;

// Helper function to get install path
function GetInstallPath(Param: String): String;
begin
  Result := ExpandConstant('{app}');
end;