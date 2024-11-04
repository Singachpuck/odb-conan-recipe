@echo off
chcp 65001 > nul
setlocal
echo @echo off > "%~dp0/deactivate_msbuild_env.bat"
echo echo Restoring environment >> "%~dp0/deactivate_msbuild_env.bat"
for %%v in (PATH) do (
    set foundenvvar=
    for /f "delims== tokens=1,2" %%a in ('set') do (
        if /I "%%a" == "%%v" (
            echo set "%%a=%%b">> "%~dp0/deactivate_msbuild_env.bat"
            set foundenvvar=1
        )
    )
    if not defined foundenvvar (
        echo set %%v=>> "%~dp0/deactivate_msbuild_env.bat"
    )
)
endlocal


set "PATH=%PATH%;C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin"