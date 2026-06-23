
from fastapi import APIRouter, Request, Depends, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import os
from pathlib import Path
from .fake_data import fake_db
from .tracking import track_deception_action

router = APIRouter(prefix="/deception", tags=["Deception Environment"])

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.get("/fake-admin", response_class=HTMLResponse)
async def fake_admin_dashboard(request: Request, response: Response):
    track_deception_action(request, "VIEW_ADMIN_DASHBOARD", "/deception/fake-admin")
    # If session is passed in URL query or header from redirect, we should set it in cookie
    sid = request.query_params.get("sid")
    if sid:
        response.set_cookie(key="deception_session_id", value=sid, httponly=True)
        
    return templates.TemplateResponse("fake_admin.html", {
        "request": request, 
        "stats": fake_db.get_sales_stats(),
        "title": "Corporate Administration Panel"
    })

@router.get("/fake-products", response_class=HTMLResponse)
async def fake_products(request: Request):
    track_deception_action(request, "VIEW_PRODUCTS", "/deception/fake-products")
    return templates.TemplateResponse("fake_products.html", {
        "request": request, 
        "products": fake_db.get_products()
    })

@router.get("/fake-customers", response_class=HTMLResponse)
async def fake_customers(request: Request):
    track_deception_action(request, "VIEW_CUSTOMERS", "/deception/fake-customers")
    return templates.TemplateResponse("fake_customers.html", {
        "request": request, 
        "customers": fake_db.get_customers()
    })

@router.get("/export/{resource}")
async def fake_export(resource: str, request: Request):
    track_deception_action(request, "EXPORT_DATA", f"/deception/export/{resource}", payload="Requested CSV dump")
    
    csv_content = f"id,name,value\n1,Test1,100\n2,Test2,200\n"
    if resource == "customers":
        csv_content = "id,name,email,spend\n" + "\n".join([f"{c['id']},{c['name']},{c['email']},{c['spend']}" for c in fake_db.get_customers()])
    elif resource == "products":
        csv_content = "id,name,price,stock\n" + "\n".join([f"{p['id']},{p['name']},{p['price']},{p['stock']}" for p in fake_db.get_products()])
        
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={resource}_backup.csv"})

@router.get("/wp-admin", response_class=HTMLResponse)
async def fake_wp_admin(request: Request):
    track_deception_action(request, "VIEW_WP_ADMIN", "/deception/wp-admin")
    return templates.TemplateResponse("fake_wp_admin.html", {
        "request": request,
        "title": "WordPress Admin Login"
    })

@router.post("/wp-admin", response_class=HTMLResponse)
async def fake_wp_admin_post(request: Request):
    form = await request.form()
    payload = f"user={form.get('log')}, pass={form.get('pwd')}"
    track_deception_action(request, "WP_AUTH_ATTEMPT", "/deception/wp-admin", payload=payload)
    return templates.TemplateResponse("fake_wp_admin.html", {
        "request": request,
        "title": "WordPress Admin Login",
        "error": "The username or password you entered is incorrect."
    })

@router.get("/phpmyadmin", response_class=HTMLResponse)
async def fake_phpmyadmin(request: Request):
    track_deception_action(request, "VIEW_PHPMYADMIN", "/deception/phpmyadmin")
    return templates.TemplateResponse("fake_phpmyadmin.html", {
        "request": request,
        "title": "phpMyAdmin"
    })

@router.post("/phpmyadmin", response_class=HTMLResponse)
async def fake_phpmyadmin_post(request: Request):
    form = await request.form()
    payload = f"user={form.get('pma_username')}"
    track_deception_action(request, "DB_AUTH_ATTEMPT", "/deception/phpmyadmin", payload=payload)
    return templates.TemplateResponse("fake_phpmyadmin.html", {
        "request": request,
        "title": "phpMyAdmin",
        "error": "Access denied for user"
    })

@router.get("/fake-leak")
async def fake_env_leak(request: Request):
    track_deception_action(request, "VIEW_ENV_LEAK", "/deception/fake-leak")
    # This includes honey tokens!
    env_content = """
DB_HOST=127.0.0.1
DB_USER=root
DB_PASS=S3cr3tP@ssw0rd!
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    """
    return Response(content=env_content.strip(), media_type="text/plain")

from fastapi import UploadFile, File
import hashlib
from ..database import SessionLocal
from ..models import FileUploadAttempt

@router.post("/fake-upload")
async def fake_upload(request: Request, file: UploadFile = File(...)):
    track_deception_action(request, "FILE_UPLOAD_ATTEMPT", "/deception/fake-upload", payload=f"File: {file.filename}")
    
    # Read and hash file, but discard contents safely
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    file_size = len(content)
    
    # Delete memory
    del content 
    
    session_id = request.query_params.get("sid") or request.cookies.get("deception_session_id") or "unknown_session"
    attacker_ip = request.client.host if request.client else "127.0.0.1"
    
    db = SessionLocal()
    try:
        upload_attempt = FileUploadAttempt(
            session_id=session_id,
            filename=file.filename,
            file_hash=file_hash,
            size=file_size,
            mime_type=file.content_type,
            attacker_ip=attacker_ip
        )
        db.add(upload_attempt)
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
        
    return JSONResponse(content={"status": "success", "message": "File uploaded successfully."})
