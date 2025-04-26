import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers import files, auth, tracer



app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(files.router)

app.include_router(auth.router)

app.include_router(tracer.router)



if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)