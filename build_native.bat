@echo off
echo =====================================================================
echo           AXIOM CORE v3.0 NATIVE C++ ENGINE BUILD SYSTEM             
echo =====================================================================
echo.

if not exist build mkdir build

echo [*] Checking for C++ compiler...

where g++ >nul 2>nul
if %ERRORLEVEL% equ 0 goto use_gcc

where clang++ >nul 2>nul
if %ERRORLEVEL% equ 0 goto use_clang

where cl.exe >nul 2>nul
if %ERRORLEVEL% equ 0 goto use_msvc

echo [!] WARNING: No C++ compiler (g++, clang++, or cl.exe) found in PATH.
echo [!] Please install MinGW-w64, Clang, or Visual Studio C++ Build Tools.
exit /b 1

:use_gcc
echo [+] GCC/G++ detected.
echo [*] Compiling Superium Native Benchmark Binary with -O3 -std=c++17...
g++ -O3 -std=c++17 -I products/axiom-core/include products/axiom-core/tests/test_superium_native.cpp -o build/axiom_superium_native_test.exe
if %ERRORLEVEL% neq 0 (
    echo [!] Compilation failed!
    exit /b 1
)
goto run_binary

:use_clang
echo [+] Clang++ detected.
echo [*] Compiling Superium Native Benchmark Binary with -O3 -std=c++17...
clang++ -O3 -std=c++17 -I products/axiom-core/include products/axiom-core/tests/test_superium_native.cpp -o build/axiom_superium_native_test.exe
if %ERRORLEVEL% neq 0 (
    echo [!] Compilation failed!
    exit /b 1
)
goto run_binary

:use_msvc
echo [+] MSVC cl.exe detected.
echo [*] Compiling Superium Native Benchmark Binary with /O2 /std:c++17...
cl.exe /O2 /std:c++17 /EHsc /I products\axiom-core\include products\axiom-core\tests\test_superium_native.cpp /Fe:build\axiom_superium_native_test.exe
if %ERRORLEVEL% neq 0 (
    echo [!] Compilation failed!
    exit /b 1
)
goto run_binary

:run_binary
echo [+] Compilation successful: build\axiom_superium_native_test.exe
echo.
echo [*] Executing Native Verification Suite...
echo.
.\build\axiom_superium_native_test.exe
if %ERRORLEVEL% equ 0 (
    echo.
    echo =====================================================================
    echo [+] BUILD AND NATIVE VERIFICATION COMPLETED WITH 100%% HEALTH!
    echo =====================================================================
    exit /b 0
) else (
    echo [!] Native tests failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
