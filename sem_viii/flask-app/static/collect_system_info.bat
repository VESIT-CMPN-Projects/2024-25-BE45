@echo off
setlocal EnableDelayedExpansion

set "OUTPUT_FILE=%~dp0output.txt"
echo ====================================================== > "%OUTPUT_FILE%"
echo Retrieving CPU Information... >> "%OUTPUT_FILE%"
echo ====================================================== >> "%OUTPUT_FILE%"

for /f "delims=" %%i in ('powershell -command ^
    "Get-CimInstance Win32_Processor | ForEach-Object { '{0} - Socket: {1} - Manufacturer: {2} - ProcessorId: {3} - MaxClockSpeed: {4} MHz - Caption: {5} - Family: {6} - Type: {7} - Data Width: {8}-bit' -f $_.Name, $_.SocketDesignation, $_.Manufacturer, $_.ProcessorId, $_.MaxClockSpeed, $_.Caption, $_.Family, $_.ProcessorType, $_.DataWidth }"') do (
    echo %%i >> "%OUTPUT_FILE%"
)

echo CPU Information Retrieved. >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo ====================================================== >> "%OUTPUT_FILE%"
echo Retrieving System Information... >> "%OUTPUT_FILE%"
echo ====================================================== >> "%OUTPUT_FILE%"

powershell -Command "Get-CimInstance Win32_BIOS | Format-List Manufacturer, Name, Version, SerialNumber, ReleaseDate" >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_ComputerSystem | Format-List Manufacturer, Model, SystemType" >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_BaseBoard | Format-List Manufacturer, Product, Version, SerialNumber" >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_PhysicalMemory | Format-List Manufacturer, PartNumber, SerialNumber, Speed, Capacity, DeviceLocator, BankLabel" >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_PhysicalMemoryArray | Format-List MaxCapacity, MemoryDevices" >> "%OUTPUT_FILE%"

echo GPU Information: >> "%OUTPUT_FILE%"
for /f "delims=" %%i in ('powershell -command "(Get-CimInstance Win32_VideoController).Caption"') do (
    set "gpu_info=%%i"
    echo GPU detected: !gpu_info! >> "%OUTPUT_FILE%"
)

if not defined gpu_info (
    echo No GPU detected. >> "%OUTPUT_FILE%"
)

echo !gpu_info! | findstr /i "NVIDIA" >nul && set "gpu_type=NVIDIA"
echo !gpu_info! | findstr /i "AMD" >nul && set "gpu_type=AMD"

echo GPU Type: !gpu_type! >> "%OUTPUT_FILE%"

IF "!gpu_type!"=="NVIDIA" (
    echo Running NVIDIA Query... >> "%OUTPUT_FILE%"
    nvidia-smi --query-gpu=temperature.gpu,fan.speed,power.draw,clocks.current.graphics --format=csv >> "%OUTPUT_FILE%"
    nvidia-smi -q -d POWER >> "%OUTPUT_FILE%"
) ELSE IF "!gpu_type!"=="AMD" (
    echo Running AMD Query... >> "%OUTPUT_FILE%"
    radeon-profile --query-temp --query-fan --query-power 2 >> "%OUTPUT_FILE%"
) ELSE (
    echo Unsupported GPU type or unable to determine GPU type. >> "%OUTPUT_FILE%"
)

:: Log system metrics to output.txt
echo ====================================================== >> "%OUTPUT_FILE%"
echo Basic System Performance Metrics >> "%OUTPUT_FILE%"
echo ====================================================== >> "%OUTPUT_FILE%"

for /f "tokens=1-3 delims=/- " %%a in ('date /t') do set today=%%c-%%a-%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set time=%%a:%%b
set datetime=%today% %time%

for /f %%a in ('powershell -command "[math]::Round((Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue,2)"') do set "cpuUsage=%%a"
for /f %%a in ('powershell -command "[math]::Round((Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue,2)"') do set "availMemory=%%a"
for /f %%a in ('powershell -command "(New-TimeSpan -Start (Get-CimInstance Win32_OperatingSystem).LastBootUpTime -End (Get-Date)).TotalSeconds"') do set "uptimeSecs=%%a"
for /f %%a in ('powershell -command "[math]::Round(((Get-CimInstance -Namespace 'root\WMI' -Class MSAcpi_ThermalZoneTemperature).CurrentTemperature / 10) - 273.15,2)"') do set "cpuTemp=%%a"

echo Date/Time: %datetime% >> "%OUTPUT_FILE%"
echo CPU Usage: %cpuUsage%%% >> "%OUTPUT_FILE%"
echo Available Memory: %availMemory% MB >> "%OUTPUT_FILE%"
echo System Uptime (seconds): %uptimeSecs% >> "%OUTPUT_FILE%"
echo CPU Temperature: %cpuTemp% C >> "%OUTPUT_FILE%"

echo ====================================================== >> "%OUTPUT_FILE%"
echo System Hardware Information Report >> "%OUTPUT_FILE%"
echo ====================================================== >> "%OUTPUT_FILE%"

echo CPU: >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, Manufacturer | Format-Table -AutoSize" >> "%OUTPUT_FILE%"

echo Memory: >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity, Speed, Manufacturer, PartNumber | Format-Table -AutoSize" >> "%OUTPUT_FILE%"

echo Disk Drives: >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_DiskDrive | Select-Object Caption, Size, Status | Format-Table -AutoSize" >> "%OUTPUT_FILE%"

echo BIOS: >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_BIOS | Select-Object Manufacturer, Name, Version, SerialNumber | Format-Table -AutoSize" >> "%OUTPUT_FILE%"

echo OS: >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture, TotalVisibleMemorySize, FreePhysicalMemory | Format-Table -AutoSize" >> "%OUTPUT_FILE%"

echo GPU: >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_VideoController | Select-Object Caption, CurrentRefreshRate, CurrentHorizontalResolution, CurrentVerticalResolution | Format-Table -AutoSize" >> "%OUTPUT_FILE%"

echo Memory Info: >> "%OUTPUT_FILE%"
powershell -Command "Get-CimInstance Win32_PhysicalMemory | Select-Object BankLabel, Capacity, DeviceLocator, Manufacturer, MemoryType, Speed, PartNumber, SerialNumber, Tag | Format-Table -AutoSize" >> "%OUTPUT_FILE%"

echo System Memory Status: >> "%OUTPUT_FILE%"
systeminfo | findstr /C:"Total Physical Memory" /C:"Available Physical Memory" >> "%OUTPUT_FILE%"

echo Virtual Memory Details: >> "%OUTPUT_FILE%"
systeminfo | findstr /C:"Virtual Memory" /C:"Paging File" >> "%OUTPUT_FILE%"

echo ====================================================== >> "%OUTPUT_FILE%"
echo Script completed. >> "%OUTPUT_FILE%"
echo ====================================================== >> "%OUTPUT_FILE%"

pause
