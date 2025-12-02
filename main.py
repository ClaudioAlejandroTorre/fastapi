from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.middleware("http")
async def bloquear_app(request: Request, call_next):
    return JSONResponse(
        content={
            "status": "DISCONTINUADA",
            "mensaje": "La Aplicación ha sido discontinuada",
            "usar_app": False
        },
        status_code=200
    )
