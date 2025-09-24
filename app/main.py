from fastapi import FastAPI, Request, HTTPException, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from contextlib import asynccontextmanager
import secrets
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.database import db, get_projects_collection, get_contacts_collection
from app.models import Project, ProjectCreate, ContactCreate
from bson import ObjectId
from typing import List
from datetime import datetime

# Security for admin area
security = HTTPBasic()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password123")

# Email configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USERNAME)
EMAIL_TO = os.getenv("EMAIL_TO", EMAIL_USERNAME)

async def send_email(subject: str, body: str, to_email: str = None):
    """Send email notification"""
    print(f"🔧 Email config check:")
    print(f"   EMAIL_HOST: {EMAIL_HOST}")
    print(f"   EMAIL_PORT: {EMAIL_PORT}")
    print(f"   EMAIL_USERNAME: {EMAIL_USERNAME[:5]}...@gmail.com" if EMAIL_USERNAME else "Not set")
    print(f"   EMAIL_PASSWORD: {'Set' if EMAIL_PASSWORD else 'Not set'}")
    print(f"   EMAIL_FROM: {EMAIL_FROM}")
    print(f"   EMAIL_TO: {EMAIL_TO}")
    
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        print("⚠️ Email not configured, skipping email send")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL_FROM
        message["To"] = to_email or EMAIL_TO
        
        # Add body
        text_part = MIMEText(body, "plain")
        message.attach(text_part)
        
        print(f"📧 Attempting to send email to: {to_email or EMAIL_TO}")
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=EMAIL_HOST,
            port=EMAIL_PORT,
            start_tls=True,
            username=EMAIL_USERNAME,
            password=EMAIL_PASSWORD,
        )
        print(f"✅ Email sent successfully to {to_email or EMAIL_TO}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Fallback data when database is unavailable
FALLBACK_PROJECTS = [
    {
        "_id": "1",
        "name": "Social Media Platform",
        "description": "A social networking application with user profiles and posts",
        "tech_stack": ["Python", "Flask", "SQLite"],
        "status": "Completed",
        "featured": True
    },
    {
        "_id": "2",
        "name": "Learning Platform", 
        "description": "Educational platform with courses and progress tracking",
        "tech_stack": ["Python", "Django", "PostgreSQL"],
        "status": "Completed",
        "featured": True
    },
    {
        "_id": "3",
        "name": "Music Streaming Platform",
        "description": "Music player with playlists and user preferences", 
        "tech_stack": ["Python", "FastAPI", "MongoDB"],
        "status": "Completed",
        "featured": False
    },
    {
        "_id": "4",
        "name": "Emoji Classifier",
        "description": "Machine learning model to classify and analyze emojis",
        "tech_stack": ["Python", "TensorFlow", "Pandas"],
        "status": "In Progress",
        "featured": True
    }
]

# Lifespan event handler for database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to database
    connected = db.connect()
    
    if connected:
        # Initialize with sample data if no projects exist
        projects_collection = get_projects_collection()
        if projects_collection.count_documents({}) == 0:
            sample_projects = [
                {
                    "name": "Social Media Platform",
                    "description": "A social networking application with user profiles and posts",
                    "tech_stack": ["Python", "Flask", "SQLite"],
                    "status": "Completed",
                    "featured": True
                },
                {
                    "name": "Learning Platform", 
                    "description": "Educational platform with courses and progress tracking",
                    "tech_stack": ["Python", "Django", "PostgreSQL"],
                    "status": "Completed",
                    "featured": True
                },
                {
                    "name": "Music Streaming Platform",
                    "description": "Music player with playlists and user preferences", 
                    "tech_stack": ["Python", "FastAPI", "MongoDB"],
                    "status": "Completed",
                    "featured": False
                },
                {
                    "name": "Emoji Classifier",
                    "description": "Machine learning model to classify and analyze emojis",
                    "tech_stack": ["Python", "TensorFlow", "Pandas"],
                    "status": "In Progress",
                    "featured": True
                }
            ]
            projects_collection.insert_many(sample_projects)
            print("✅ Sample projects added to database")
    else:
        print("⚠️ Starting without database connection")
    
    yield
    
    # Shutdown: Close database connection
    db.close()

# Create FastAPI app with lifespan handler
app = FastAPI(
    title="Portfolio Website", 
    description="My Personal Portfolio",
    lifespan=lifespan
)

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        # Try to get featured projects from database
        projects_collection = get_projects_collection()
        featured_projects = list(projects_collection.find({"featured": True}).limit(2))
        
        # Convert ObjectId to string for template rendering
        for project in featured_projects:
            project["_id"] = str(project["_id"])
            
    except Exception as e:
        print(f"Database error, using fallback data: {e}")
        # Use fallback data if database is unavailable
        featured_projects = [p for p in FALLBACK_PROJECTS if p.get("featured")][:2]
    
    return templates.TemplateResponse("home.html", {
        "request": request, 
        "page_title": "Home",
        "featured_projects": featured_projects
    })

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "page_title": "About"})

@app.get("/projects", response_class=HTMLResponse)
async def projects(request: Request):
    try:
        # Get all projects from database
        projects_collection = get_projects_collection()
        all_projects = list(projects_collection.find({}))
        
        # Convert ObjectId to string for template rendering
        for project in all_projects:
            project["_id"] = str(project["_id"])
            
    except Exception as e:
        print(f"Database error, using fallback data: {e}")
        # Use fallback data if database is unavailable
        all_projects = FALLBACK_PROJECTS
    
    return templates.TemplateResponse("projects.html", {
        "request": request, 
        "page_title": "Projects",
        "projects": all_projects
    })

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, "page_title": "Contact"})

@app.post("/contact")
async def submit_contact(
    request: Request,
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    newsletter: bool = Form(False)
):
    print("🔥 CONTACT FORM SUBMITTED!")
    print(f"   Name: {firstName} {lastName}")
    print(f"   Email: {email}")
    print(f"   Subject: {subject}")
    print(f"   Message: {message[:50]}...")
    
    try:
        # Create contact message
        contact_data = ContactCreate(
            first_name=firstName,
            last_name=lastName,
            email=email,
            subject=subject,
            message=message,
            newsletter_signup=newsletter
        )
        
        # Try to save to database
        print("💾 Attempting to save to database...")
        contacts_collection = get_contacts_collection()
        result = contacts_collection.insert_one(contact_data.dict())
        print(f"💾 Database save result: {result.inserted_id}")
        
        # Send email notification
        print("📧 Attempting to send email...")
        email_subject = f"New Portfolio Contact: {subject}"
        email_body = f"""
New message from your portfolio website:

Name: {firstName} {lastName}
Email: {email}
Subject: {subject}

Message:
{message}

Newsletter Signup: {'Yes' if newsletter else 'No'}

---
This message was sent from your portfolio contact form.
        """
        
        # Send email (don't fail if email fails)
        email_sent = await send_email(email_subject, email_body.strip())
        print(f"📧 Email send result: {email_sent}")
        
        if result.inserted_id:
            if email_sent:
                success_msg = "Thank you! Your message has been sent successfully. I'll get back to you soon!"
            else:
                success_msg = "Thank you! Your message has been saved. I'll get back to you soon! (Email notification failed)"
        else:
            success_msg = "Thank you for your message! (Database currently unavailable, but your message was received)"
            
    except Exception as e:
        print(f"❌ Contact form error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        success_msg = "Thank you for your message! There was a technical issue, but I'll still try to get back to you."
    
    return templates.TemplateResponse("contact.html", {
        "request": request,
        "page_title": "Contact",
        "success": success_msg
    })

# Test route to check if auth is working
@app.get("/test-auth")
async def test_auth(admin_user: str = Depends(verify_admin)):
    return {"message": f"Hello {admin_user}, auth is working!"}

# Admin routes for project management (PASSWORD PROTECTED)
@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request, admin_user: str = Depends(verify_admin)):
    try:
        projects_collection = get_projects_collection()
        contacts_collection = get_contacts_collection()
        
        all_projects = list(projects_collection.find({}))
        recent_contacts = list(contacts_collection.find({}).sort("created_at", -1).limit(5))
        
        # Convert ObjectId to string
        for project in all_projects:
            project["_id"] = str(project["_id"])
        for contact in recent_contacts:
            contact["_id"] = str(contact["_id"])
            
    except Exception as e:
        print(f"Admin panel database error: {e}")
        all_projects = FALLBACK_PROJECTS
        recent_contacts = []
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "page_title": "Admin",
        "projects": all_projects,
        "contacts": recent_contacts
    })

@app.post("/admin/projects")
async def add_project(
    request: Request,
    admin_user: str = Depends(verify_admin),
    name: str = Form(...),
    description: str = Form(...),
    tech_stack: str = Form(...),
    status: str = Form(...),
    github_url: str = Form(""),
    demo_url: str = Form(""),
    featured: bool = Form(False)
):
    try:
        # Parse tech stack from comma-separated string
        tech_list = [tech.strip() for tech in tech_stack.split(",") if tech.strip()]
        
        # Create project
        project_data = ProjectCreate(
            name=name,
            description=description,
            tech_stack=tech_list,
            status=status,
            github_url=github_url if github_url else None,
            demo_url=demo_url if demo_url else None,
            featured=featured
        )
        
        # Save to database
        projects_collection = get_projects_collection()
        result = projects_collection.insert_one(project_data.dict())
        
        if result.inserted_id:
            return RedirectResponse(url="/admin", status_code=303)
    except Exception as e:
        print(f"Error adding project: {e}")
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/projects/{project_id}/edit")
async def edit_project(
    project_id: str,
    request: Request,
    admin_user: str = Depends(verify_admin),
    name: str = Form(...),
    description: str = Form(...),
    tech_stack: str = Form(...),
    status: str = Form(...),
    github_url: str = Form(""),
    demo_url: str = Form(""),
    featured: bool = Form(False)
):
    try:
        # Parse tech stack from comma-separated string
        tech_list = [tech.strip() for tech in tech_stack.split(",") if tech.strip()]
        
        # Create update data
        update_data = {
            "name": name,
            "description": description,
            "tech_stack": tech_list,
            "status": status,
            "github_url": github_url if github_url else None,
            "demo_url": demo_url if demo_url else None,
            "featured": featured,
            "updated_at": datetime.utcnow()
        }
        
        # Update in database
        projects_collection = get_projects_collection()
        result = projects_collection.update_one(
            {"_id": ObjectId(project_id)}, 
            {"$set": update_data}
        )
        
        if result.modified_count:
            return RedirectResponse(url="/admin", status_code=303)
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        print(f"Error updating project: {e}")
    
    return RedirectResponse(url="/admin", status_code=303)

@app.delete("/admin/projects/{project_id}")
async def delete_project(project_id: str, admin_user: str = Depends(verify_admin)):
    try:
        projects_collection = get_projects_collection()
        result = projects_collection.delete_one({"_id": ObjectId(project_id)})
        
        if result.deleted_count:
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn app.main:app --reload