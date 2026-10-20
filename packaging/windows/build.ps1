$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $Root
python -m pip install '.[dev]' 'PySide6-Essentials==6.8.3' 'pyinstaller>=6,<7'
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
python packaging/build_app.py
if ($LASTEXITCODE -ne 0) { throw 'Windows app build failed' }
dotnet publish packaging/sensor-host/Wattpin.SensorHost.csproj -c Release -r win-x64 --self-contained true -o build-output/sensor-host
if ($LASTEXITCODE -ne 0) { throw 'Windows sensor helper build failed' }
$PythonDeps = python -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"
$Nuget = if ($env:NUGET_PACKAGES) { $env:NUGET_PACKAGES } else { "$env:USERPROFILE\.nuget\packages" }
python packaging/prepare_windows_payload.py --helper build-output/sensor-host --python-deps $PythonDeps --nuget $Nuget
if ($LASTEXITCODE -ne 0) { throw 'Payload preparation failed' }
New-Item -ItemType Directory -Force dist | Out-Null
$Compiler = if ($env:WATTPIN_NSIS) { $env:WATTPIN_NSIS } else { "${env:ProgramFiles(x86)}\NSIS\makensis.exe" }
& $Compiler "/DPAYLOAD=$Root\build-output\windows\Wattpin" "/DOUTPUT=$Root\dist\Wattpin-0.4.4-Windows-x64-Setup.exe" packaging/windows/wattpin.nsi
if ($LASTEXITCODE -ne 0) { throw 'Setup compilation failed' }
Write-Host 'Built dist\Wattpin-0.4.4-Windows-x64-Setup.exe'
