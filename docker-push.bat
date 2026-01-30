@echo off
REM Build and push Docker images to Docker Hub
REM Usage: docker-push.bat <dockerhub_username>

SET DOCKERHUB_USERNAME=%1
IF "%DOCKERHUB_USERNAME%"=="" SET DOCKERHUB_USERNAME=fincommerce

SET VERSION=latest

echo ===========================================
echo   Building and Pushing Docker Images
echo   Username: %DOCKERHUB_USERNAME%
echo   Version: %VERSION%
echo ===========================================
echo.

REM Build backend
echo [1/4] Building backend image...
docker build -t %DOCKERHUB_USERNAME%/fincommerce-backend:%VERSION% ./backend
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Backend build failed!
    exit /b 1
)

REM Build frontend  
echo [2/4] Building frontend image...
docker build -t %DOCKERHUB_USERNAME%/fincommerce-frontend:%VERSION% ./Web_app
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Frontend build failed!
    exit /b 1
)

REM Login reminder
echo.
echo [3/4] Ready to push to Docker Hub
echo Make sure you're logged in: docker login
echo.
pause

REM Push to Docker Hub
echo [4/4] Pushing images to Docker Hub...
docker push %DOCKERHUB_USERNAME%/fincommerce-backend:%VERSION%
docker push %DOCKERHUB_USERNAME%/fincommerce-frontend:%VERSION%

echo.
echo ===========================================
echo   SUCCESS! Images pushed to Docker Hub
echo ===========================================
echo.
echo Images available at:
echo   - %DOCKERHUB_USERNAME%/fincommerce-backend:%VERSION%
echo   - %DOCKERHUB_USERNAME%/fincommerce-frontend:%VERSION%
echo.
echo Your friend can run:
echo   1. Create a folder and add docker-compose.yml
echo   2. Create .env with GEMINI_API_KEY=their_key
echo   3. Run: docker-compose up -d
echo   4. Open: http://localhost:3000
echo.
pause
