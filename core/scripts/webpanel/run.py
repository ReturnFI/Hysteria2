import uvicorn
from app import app
from uvicorn.middleware.wsgi import WSGIMiddleware

if __name__ == "__main__":
    uvicorn.run(
        WSGIMiddleware(app),
        host="0.0.0.0",
        port=8080,
        ssl_certfile="/etc/letsencrypt/live/example.com/fullchain.pem",
        ssl_keyfile="/etc/letsencrypt/live/example.com/privkey.pem"
    )
