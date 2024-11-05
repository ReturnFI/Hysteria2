import uvicorn
from app import app
from uvicorn.middleware.wsgi import WSGIMiddleware

if __name__ == "__main__":
    uvicorn.run(
        WSGIMiddleware(app),
        host="0.0.0.0",
        port=9090,
        ssl_certfile="/$Path/fullchain.pem",
        ssl_keyfile="/$Path/privkey.pem"
    )
