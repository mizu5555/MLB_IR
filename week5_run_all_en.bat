@echo off
REM Week 5: Complete Data Collection and Integration
REM No Chinese characters to avoid encoding issues

echo ========================================
echo Week 5: Data Collection and Integration
echo ========================================
echo.

echo [Step 1/4] Build playerID mapping table
echo ----------------------------------------
python week5_player_mapping.py
if %errorlevel% neq 0 (
    echo ERROR: Mapping table creation failed
    pause
    exit /b 1
)
echo.

echo [Step 2/4] Collect awards, salary, statcast data
echo ----------------------------------------
python week5_data_collection.py
if %errorlevel% neq 0 (
    echo ERROR: Data collection failed
    pause
    exit /b 1
)
echo.

echo [Step 3/4] Integrate data into existing documents
echo ----------------------------------------
python week5_integrate_data.py
if %errorlevel% neq 0 (
    echo ERROR: Data integration failed
    pause
    exit /b 1
)
echo.

echo [Step 4/4] Rebuild vector database (optional)
echo ----------------------------------------
echo Do you need to rebuild the vector database?
echo If you only added fields (no text changes), you can skip this step
echo.
set /p rebuild="Rebuild vector database? (y/n): "

if /i "%rebuild%"=="y" (
    echo Rebuilding vector database...
    python week4_build_vector_db.py
    if %errorlevel% neq 0 (
        echo WARNING: Vector DB rebuild failed, but data is integrated
    )
)

echo.
echo ========================================
echo Week 5 Complete!
echo ========================================
echo.
echo Generated files:
echo   - mlb_data/week5_player_mapping.json (playerID mapping)
echo   - mlb_data/week5_awards.json (awards data)
echo   - mlb_data/week5_salaries.json (salary data)
echo   - mlb_data/week5_statcast_structure.json (statcast structure)
echo   - mlb_data/week5_mlb_documents_enhanced.json (integrated documents)
echo.
echo Next steps:
echo   - Run week5_test.py to test the new features
echo   - Or start week5_streamlit_demo.py to see the UI
echo.
pause
