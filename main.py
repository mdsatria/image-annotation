import io
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from PIL import Image, ImageOps

app = FastAPI(title="Image Annotation")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    data = await file.read()
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)  # auto-rotate from EXIF
        img = img.convert("RGB")
    except Exception as e:
        raise HTTPException(400, f"Cannot open image: {e}")

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {
        "w": img.width,
        "h": img.height,
        "src": f"data:image/jpeg;base64,{b64}",
        "name": file.filename or "image",
    }


@app.post("/export")
async def export_mask(request: Request):
    body = await request.json()
    mask_data_url = body.get("mask", "")
    if "," not in mask_data_url:
        raise HTTPException(400, "Invalid mask data")

    raw = base64.b64decode(mask_data_url.split(",", 1)[1])
    mask = Image.open(io.BytesIO(raw)).convert("L")
    # Hard threshold → pure binary
    mask = mask.point(lambda p: 255 if p > 127 else 0)

    buf = io.BytesIO()
    mask.save(buf, "JPEG", quality=95)
    filename = body.get("filename", "mask") + "_mask.jpg"
    return Response(
        buf.getvalue(),
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
