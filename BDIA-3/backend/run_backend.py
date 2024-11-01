import uvicorn
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        workers=1
    )