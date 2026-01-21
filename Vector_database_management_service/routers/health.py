from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/health")
async def health(request: Request):
    ctx = request.app.state.ctx
    try:
        await ctx.connect()
        return {"status": "healthy", "connected": True}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
