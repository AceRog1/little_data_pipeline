@echo off
setlocal enabledelayedexpansion

REM ===== Configuración =====
set OUT_DIR=artifacts
set PYTHON=python

REM ===== Nombres de runs =====
set RUNS=run1_baseline run2_deep_lookback run3_dropout_high run4_short_lookback run5_slow_lr

echo 🧹 Eliminando carpetas antiguas de artifacts...

for %%R in (%RUNS%) do (
    if exist "%OUT_DIR%\%%R" (
        echo 🗑️  Eliminando: %OUT_DIR%\%%R
        rmdir /S /Q "%OUT_DIR%\%%R"
    )
)

echo 🚀 Ejecutando nuevas configuraciones...

REM --- Run 1
%PYTHON% src/models/train_lstm.py --run_name run1_baseline --epochs 50 --hidden_size 32 --dropout 0.3

REM --- Run 2
%PYTHON% src/models/train_lstm.py --run_name run2_deep_lookback --lookback 12 --hidden_size 64 --dropout 0.3 --epochs 100

REM --- Run 3
%PYTHON% src/models/train_lstm.py --run_name run3_dropout_high --dropout 0.5 --epochs 100 --batch_size 64

REM --- Run 4
%PYTHON% src/models/train_lstm.py --run_name run4_short_lookback --lookback 3 --hidden_size 32 --batch_size 128 --epochs 150

REM --- Run 5
%PYTHON% src/models/train_lstm.py --run_name run5_slow_lr --lr 1e-4 --epochs 200 --hidden_size 64 --dropout 0.2

echo ✅ ¡Todas las ejecuciones han terminado!

pause
