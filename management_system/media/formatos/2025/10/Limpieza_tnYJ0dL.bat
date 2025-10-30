:: ----------
:: SISTEMA
:: ----------

:: Elimina archivos de %systemdrive%\Temp.
del /s/q/f %systemdrive%\Temp\*.*
del /s/q/f %systemdrive%\tmp\*.*
:: Elimina archivos de %windir%\Temp (ej. c:\winnt\Temp).
del /s/q/f %windir%\Temp\*.*
:: Elimina cache de iconos
del /s/q/f %windir%\ShellIconCache\*.*


:: ----------
:: PERFIL
:: ----------

:: Elimina archivos de %temp% del perfil ingresado (= "%userprofile%\Configuraci¢n local\Archivos temporales de Internet").
del /s/q/f %temp%\*.*
:: Elimina Archivos temporales de Internet.
del /s/q/f "%userprofile%\Configuraci¢n local\Archivos temporales de Internet\*.*"
del /s/q/f "%userprofile%\Microsoft\Windows\Archivos temporales de Internet\*.*"
:: Elimina Cookies de IE (del perfil ingresado).
del /s/q/f %userprofile%\Cookies\*.*


:: ----------
:: EXTENSIONES
:: ----------

%systemdrive%
cd\

:: Elimina logs en la raiz de C:\
del /q/f *.log
:: Elimina archivos tmp de C:\
del /s/q/f *.tmp


echo Eliminando archivos de %temp%.
del /s/a/q/f %temp%\*.*
echo.
echo Eliminando archivos de %windir%\Temp.
del /s/a/q/f %windir%\Temp\*.*
echo.

echo Eliminando Archivos temporales de Internet.
del /s/a/q/f "%userprofile%\Configuración local\Archivos temporales de Internet\*.*"
echo.
echo Eliminando Cookies.
del /s/a/q/f %userprofile%\Cookies\*.*
echo.

:: Windows Vista (español) - Archivos temporales de Internet
IF EXIST "%userprofile%\AppData\Local\Microsoft\Windows\Archivos temporales de Internet" (
	echo Eliminando Archivos temporales de Internet.
	del /s/a/q/f "%userprofile%\Microsoft\Windows\Archivos temporales de Internet\*.*"
	echo.
)

:: Windows Vista (inglés) - Archivos temporales de Internet
IF EXIST "%userprofile%\AppData\Local\Microsoft\Windows\Temporary Internet Files" (
	echo Eliminando Archivos temporales de Internet.
	del /s/a/q/f "%userprofile%\Microsoft\Windows\Temporary Internet Files\*.*"
	echo.
)

:: Windows Vista (español) - Carpeta de grabacion temporal
IF EXIST "%userprofile%\Microsoft\Windows\Burn\Carpeta de grabación temporal" (
	echo Eliminando Carpeta de grabacion temporal.
	del /s/a/q/f "%userprofile%\Microsoft\Windows\Burn\Carpeta de grabación temporal\*.*"
	echo.
)

:: Windows Vista (inglés) - Carpeta de grabacion temporal
IF EXIST "%userprofile%\Microsoft\Windows\Burn\Burn" (
	echo Eliminando Carpeta de grabacion temporal.
	del /s/a/q/f "%userprofile%\Microsoft\Windows\Burn\Burn\*.*"
	echo.
)

:: Windows XP (español) - Carpeta de grabacion temporal
IF EXIST "%userprofile%\Configuración local\Application Data\Microsoft\CD Burning" (
	echo Eliminando archivos de Carpeta de grabacion temporal.
	del /s/a/q/f "%userprofile%\Configuración local\Application Data\Microsoft\CD Burning\*.*"
	echo.
)

:: Windows XP (inglés) - Carpeta de grabacion temporal
IF EXIST "%userprofile%\Local Configuration\Application Data\Microsoft\CD Burning" (
	echo Eliminando archivos de Carpeta de grabacion temporal.
	del /s/a/q/f "%userprofile%\Local Configuration\Application Data\Microsoft\CD Burning\*.*"
	echo.
)

IF EXIST %systemdrive%\Temp (
	echo Eliminando archivos de %systemdrive%\Temp.
	del /s/a/q/f %systemdrive%\Temp\*.*
	echo.
)

echo Eliminando logs y tmp...
%homedrive%
cd\
echo Omitiendo *.log
rem del /s/a/q/f *.log
del /s/a/q/f *.tmp

cls
echo.
echo Limpieza realizada.
@pause