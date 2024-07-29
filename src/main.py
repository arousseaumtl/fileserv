from mangum import Mangum
import uvicorn

from app import app

handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
