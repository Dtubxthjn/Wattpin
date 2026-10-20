Unicode True
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"
!include "x64.nsh"
!include "WinVer.nsh"
!ifndef PAYLOAD
!define PAYLOAD "..\..\build-output\windows\Wattpin"
!endif
!ifndef OUTPUT
!define OUTPUT "..\..\dist\Wattpin-0.4.3-Windows-x64-Setup.exe"
!endif
Name "Wattpin"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\Wattpin"
InstallDirRegKey HKCU "Software\Wattpin" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
Icon "..\..\powerglass\assets\wattpin.ico"
UninstallIcon "..\..\powerglass\assets\wattpin.ico"
VIProductVersion "0.4.3.0"
VIAddVersionKey "ProductName" "Wattpin"
VIAddVersionKey "FileDescription" "Wattpin Setup"
VIAddVersionKey "FileVersion" "0.4.3"
VIAddVersionKey "LegalCopyright" "2026 Wattpin contributors"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\Wattpin.exe"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
UninstPage custom un.DataPage un.DataLeave
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH
!insertmacro MUI_LANGUAGE "English"
Var Purge
Var PurgeCheck

Function .onInit
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_ICONSTOP "Wattpin requires Windows 10 or newer."
    Abort
  ${EndIf}
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Wattpin requires 64-bit Windows 10 or newer."
    Abort
  ${EndIf}
FunctionEnd

Function .onVerifyInstDir
  IfFileExists "$INSTDIR\*.*" 0 valid
  IfFileExists "$INSTDIR\.wattpin-managed" valid 0
  SetErrors
valid:
FunctionEnd

Section "Wattpin (required)" Main
  SectionIn RO
  IfFileExists "$INSTDIR\Wattpin.exe" 0 stopped
  ExecWait '"$INSTDIR\Wattpin.exe" --quit' $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "Close Wattpin before upgrading."
    Abort
  ${EndIf}
stopped:
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD}\*.*"
  FileOpen $0 "$INSTDIR\.wattpin-managed" w
  FileWrite $0 "Wattpin 0.4.3"
  FileClose $0
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Wattpin"
  Delete "$DESKTOP\Wattpin.lnk"
  CreateDirectory "$SMPROGRAMS\Wattpin"
  CreateShortcut "$SMPROGRAMS\Wattpin\Wattpin.lnk" "$INSTDIR\Wattpin.exe"
  CreateShortcut "$SMPROGRAMS\Wattpin\Uninstall Wattpin.lnk" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Wattpin" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wattpin" "DisplayName" "Wattpin"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wattpin" "DisplayVersion" "0.4.3"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wattpin" "DisplayIcon" "$INSTDIR\Wattpin.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wattpin" "Publisher" "Wattpin contributors"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wattpin" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wattpin" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wattpin" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wattpin" "NoRepair" 1
SectionEnd

Section "Start Wattpin when I sign in" Login
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Wattpin" '$\"$INSTDIR\Wattpin.exe$\"'
SectionEnd
Section /o "Desktop shortcut" Desktop
  CreateShortcut "$DESKTOP\Wattpin.lnk" "$INSTDIR\Wattpin.exe"
SectionEnd

Function un.DataPage
  nsDialogs::Create 1018
  Pop $0
  ${NSD_CreateLabel} 0 0 100% 32u "The app will be removed. Your power history and preferences are kept unless you select the option below."
  Pop $0
  ${NSD_CreateCheckbox} 0 45u 100% 20u "Also delete my power history and preferences"
  Pop $PurgeCheck
  nsDialogs::Show
FunctionEnd
Function un.DataLeave
  ${NSD_GetState} $PurgeCheck $Purge
FunctionEnd

Section "Uninstall"
  IfFileExists "$INSTDIR\Wattpin.exe" 0 unStopped
  ExecWait '"$INSTDIR\Wattpin.exe" --quit' $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "Close Wattpin before uninstalling."
    Abort
  ${EndIf}
unStopped:
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Wattpin"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wattpin"
  DeleteRegKey HKCU "Software\Wattpin"
  Delete "$DESKTOP\Wattpin.lnk"
  Delete "$SMPROGRAMS\Wattpin\Wattpin.lnk"
  Delete "$SMPROGRAMS\Wattpin\Uninstall Wattpin.lnk"
  RMDir "$SMPROGRAMS\Wattpin"
  IfFileExists "$INSTDIR\.wattpin-managed" 0 unFinished
  Delete "$INSTDIR\Wattpin.exe"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\THIRD_PARTY_NOTICES.md"
  Delete "$INSTDIR\README.md"
  RMDir /r "$INSTDIR\_internal"
  RMDir /r "$INSTDIR\sensors"
  RMDir /r "$INSTDIR\licenses"
  Delete "$INSTDIR\.wattpin-managed"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  ${If} $Purge == ${BST_CHECKED}
    RMDir /r "$LOCALAPPDATA\Wattpin"
  ${EndIf}
unFinished:
SectionEnd
