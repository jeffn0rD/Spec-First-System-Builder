FastAPI Backend Project Setup - Windows 11
==========================================

Step-by-Step Implementation Guide
---------------------------------

* * *

Step 1: Create Project Directory and Virtual Environment
--------------------------------------------------------

    # Create project directory
    mkdir fastapi-backend
    cd fastapi-backend
    
    # Create virtual environment
    python -m venv venv
    
    # Activate virtual environment
	# requires execution policy change on windows; see farther below in startup/test section
	# note that you need to run the pip tool inside the venv (or install in both local shell/venv)
    .\venv\Scripts\activate
    
    # Verify activation (you should see (venv) in your prompt)

* * *

Step 2: Create Project Structure
--------------------------------

    # Create directory structure
    mkdir app
    mkdir app\api
    mkdir app\core
    mkdir app\models
    mkdir app\services
    mkdir tests
    
    # Create __init__.py files
    New-Item -ItemType File -Path "app\__init__.py"
    New-Item -ItemType File -Path "app\api\__init__.py"
    New-Item -ItemType File -Path "app\core\__init__.py"
    New-Item -ItemType File -Path "app\models\__init__.py"
    New-Item -ItemType File -Path "app\services\__init__.py"
    New-Item -ItemType File -Path "tests\__init__.py"

* * *

Step 3: Create Requirements File
--------------------------------

Create requirements.txt:

    New-Item -ItemType File -Path "requirements.txt"


Add the following content to requirements.txt:
# Version numbers had to be removed
# note that rust needs to be installed for pydantic 
#   Get rustup-init.exe from https://rust-lang.org/tools/install/
#	I left the file I used in the SFSB directory

    fastapi==0.109.0
    uvicorn[standard]==0.27.0
    pydantic==2.5.3
    pydantic-settings==2.1.0
    httpx==0.26.0
    networkx==3.2.1
    prefect==2.14.21
    jinja2==3.1.3
    sqlalchemy==2.0.25
    python-dotenv==1.0.0

* * *

Step 4: Install Dependencies
----------------------------

    # Install all dependencies
    pip install -r requirements.txt
    
    # Verify installation
    pip list

* * *

Step 5: Create Configuration File
---------------------------------

Create app\\core\\config.py:

    from pydantic_settings import BaseSettings
    from typing import Optional
    from functools import lru_cache
    
    
    class Settings(BaseSettings):
        """
        Application settings and configuration.
        Uses environment variables or .env file.
        """
        
        # Application Settings
        APP_NAME: str = "FastAPI Backend"
        APP_VERSION: str = "1.0.0"
        DEBUG: bool = True
        
        # API Settings
        API_V1_PREFIX: str = "/api/v1"
        
        # OpenRouter Configuration
        OPENROUTER_API_KEY: Optional[str] = None
        OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
        OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo"
        OPENROUTER_TIMEOUT: int = 30
        
        # Database Configuration
        DATABASE_URL: str = "sqlite:///./app.db"
        
        # Server Configuration
        HOST: str = "0.0.0.0"
        PORT: int = 8000
        
        class Config:
            env_file = ".env"
            case_sensitive = True
    
    
    @lru_cache()
    def get_settings() -> Settings:
        """
        Create cached settings instance.
        """
        return Settings()

* * *

Step 6: Create Environment File
-------------------------------

Create .env in the root directory:

    New-Item -ItemType File -Path ".env"

Add the following content to .env:

    # Application Settings
    APP_NAME=FastAPI Backend
    DEBUG=True
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY=your_api_key_here
    OPENROUTER_MODEL=openai/gpt-3.5-turbo
    
    # Database
    DATABASE_URL=sqlite:///./app.db
    
    # Server
    HOST=0.0.0.0
    PORT=8000
    

* * *

Step 7: Create Health Endpoint
------------------------------

Create app\\api\\health.py:

    from fastapi import APIRouter, Depends
    from pydantic import BaseModel
    from datetime import datetime
    from app.core.config import Settings, get_settings
    
    router = APIRouter()
    
    
    class HealthResponse(BaseModel):
        """Health check response model."""
        status: str
        timestamp: datetime
        app_name: str
        version: str
        openrouter_configured: bool
    
    
    @router.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check(settings: Settings = Depends(get_settings)):
        """
        Health check endpoint.
        Returns application status and configuration info.
        """
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            openrouter_configured=bool(settings.OPENROUTER_API_KEY)
        )
    
    
    @router.get("/health/detailed", tags=["Health"])
    async def detailed_health_check(settings: Settings = Depends(get_settings)):
        """
        Detailed health check with configuration details.
        """
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "application": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "debug": settings.DEBUG
            },
            "openrouter": {
                "configured": bool(settings.OPENROUTER_API_KEY),
                "base_url": settings.OPENROUTER_BASE_URL,
                "model": settings.OPENROUTER_MODEL,
                "timeout": settings.OPENROUTER_TIMEOUT
            },
            "database": {
                "url": settings.DATABASE_URL.split("///")[0] + "///" + "***"  # Hide sensitive info
            }
        }

* * *

Step 8: Create OpenRouter Service
---------------------------------

Create app\\services\\openrouter.py:

    import httpx
    from typing import Optional, Dict, Any
    from app.core.config import Settings, get_settings
    
    
    class OpenRouterService:
        """
        Service for interacting with OpenRouter API.
        """
        
        def __init__(self, settings: Settings):
            self.settings = settings
            self.base_url = settings.OPENROUTER_BASE_URL
            self.api_key = settings.OPENROUTER_API_KEY
            self.model = settings.OPENROUTER_MODEL
            self.timeout = settings.OPENROUTER_TIMEOUT
        
        async def chat_completion(
            self,
            messages: list[Dict[str, str]],
            model: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Send a chat completion request to OpenRouter.
            
            Args:
                messages: List of message dictionaries with 'role' and 'content'
                model: Model to use (defaults to configured model)
                temperature: Sampling temperature
                max_tokens: Maximum tokens to generate
                
            Returns:
                API response dictionary
            """
            if not self.api_key:
                raise ValueError("OpenRouter API key not configured")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # Optional
                "X-Title": self.settings.APP_NAME  # Optional
            }
            
            payload = {
                "model": model or self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        
        async def test_connection(self) -> bool:
            """
            Test the OpenRouter API connection.
            
            Returns:
                True if connection successful, False otherwise
            """
            try:
                result = await self.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                return bool(result)
            except Exception:
                return False
    
    
    def get_openrouter_service() -> OpenRouterService:
        """
        Dependency injection for OpenRouter service.
        """
        settings = get_settings()
        return OpenRouterService(settings)

* * *

Step 9: Create Main Application
-------------------------------

Create app\\main.py:

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.core.config import get_settings
    from app.api import health
    
    # Get settings
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix=settings.API_V1_PREFIX)
    
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs"
        }
    
    
    @app.on_event("startup")
    async def startup_event():
        """Run on application startup."""
        print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        print(f"OpenRouter configured: {bool(settings.OPENROUTER_API_KEY)}")
    
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Run on application shutdown."""
        print(f"Shutting down {settings.APP_NAME}")

* * *

Step 10: Create Run Script
--------------------------

Create run.py in the root directory:

    import uvicorn
    from app.core.config import get_settings
    
    if __name__ == "__main__":
        settings = get_settings()
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
			# this was needed to run in venv
			reload_excludes=["venv"] 
        )

* * *

Step 11: Create Test File
-------------------------

Create tests\\test\_health.py:

    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    
    def test_root():
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    
    def test_health_check():
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    
    def test_detailed_health_check():
        """Test detailed health check endpoint."""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "application" in data
        assert "openrouter" in data

* * *

Step 12: Create .gitignore
--------------------------

Create .gitignore:

    # Python
    __pycache__/
    *.py[cod]
    *$py.class
    *.so
    .Python
    venv/
    env/
    ENV/
    
    # Environment variables
    .env
    .env.local
    
    # Database
    *.db
    *.sqlite
    
    # IDE
    .vscode/
    .idea/
    *.swp
    *.swo
    
    # OS
    .DS_Store
    Thumbs.db
    
    # Logs
    *.log
    
    # Testing
    .pytest_cache/
    .coverage
    htmlcov/
    

* * *

Step 13: Testing the Application
--------------------------------

### Start the server:

    # Make sure virtual environment is activated
    .\venv\Scripts\activate
    # note this required setting script permissions on windows; this allows script execution for files created locally 
	# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
	
    # Run the application
    python run.py

### Test endpoints using PowerShell:

    # Test root endpoint
    Invoke-WebRequest -Uri "http://localhost:8000/" | Select-Object -ExpandProperty Content
    
    # Test health endpoint
    Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" | Select-Object -ExpandProperty Content
    
    # Test detailed health endpoint
    Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health/detailed" | Select-Object -ExpandProperty Content

### Or use curl (if installed):

    curl http://localhost:8000/
    curl http://localhost:8000/api/v1/health
    curl http://localhost:8000/api/v1/health/detailed

### Access Interactive API Documentation:

Open your browser and navigate to:

*   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Run tests:

    # Install pytest
    pip install pytest pytest-asyncio
    
    # Run tests
    pytest tests/ -v

* * *

Project Structure Summary
-------------------------

    fastapi-backend/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                 # Main FastAPI application
    │   ├── api/
    │   │   ├── __init__.py
    │   │   └── health.py           # Health check endpoints
    │   ├── core/
    │   │   ├── __init__.py
    │   │   └── config.py           # Configuration management
    │   ├── models/
    │   │   └── __init__.py
    │   └── services/
    │       ├── __init__.py
    │       └── openrouter.py       # OpenRouter API service
    ├── tests/
    │   ├── __init__.py
    │   └── test_health.py          # Health endpoint tests
    ├── venv/                       # Virtual environment
    ├── .env                        # Environment variables
    ├── .gitignore                  # Git ignore file
    ├── requirements.txt            # Python dependencies
    └── run.py                      # Application runner

* * *

Summary
-------

### What We've Implemented:

1.  ✅ **FastAPI Backend Project** with proper structure
2.  ✅ **All Required Dependencies** installed and configured
3.  ✅ **Configuration Management** using Pydantic Settings
4.  ✅ **Health Endpoints** (basic and detailed)
5.  ✅ **OpenRouter Integration** with placeholder service
6.  ✅ **Environment-based Configuration** for API keys and models
7.  ✅ **CORS Middleware** for cross-origin requests
8.  ✅ **Interactive API Documentation** (Swagger/ReDoc)
9.  ✅ **Testing Setup** with pytest
10.  ✅ **Proper Project Structure** for scalability

### Key Features:

*   **Modular Design**: Separated concerns (API, services, config)
*   **Type Safety**: Using Pydantic for validation
*   **Async Support**: All endpoints are async-ready
*   **Environment Variables**: Secure configuration management
*   **Auto-reload**: Development mode with hot reload
*   **API Documentation**: Auto-generated interactive docs
*   **Testing Ready**: Includes test structure and examples

### Next Steps:

1.  Add your actual OpenRouter API key to .env
2.  Implement additional API endpoints as needed
3.  Add database models using SQLAlchemy
4.  Implement Prefect workflows
5.  Add NetworkX graph operations
6.  Implement authentication/authorization
7.  Add more comprehensive tests

The application is now ready for development and testing! 🚀