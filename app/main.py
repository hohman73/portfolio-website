from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager

from app.database import db, get_projects_collection, get_contacts_collection
from app.models import Project, ProjectCreate, ContactCreate
from bson import ObjectId
from typing import List

# Lifespan event handler for database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to database
    db.connect()
    
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
    # Get featured projects from database
    projects_collection = get_projects_collection()
    featured_projects = list(projects_collection.find({"featured": True}).limit(2))
    
    # Convert ObjectId to string for template rendering
    for project in featured_projects:
        project["_id"] = str(project["_id"])
    
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
    # Get all projects from database
    projects_collection = get_projects_collection()
    all_projects = list(projects_collection.find({}))
    
    # Convert ObjectId to string for template rendering
    for project in all_projects:
        project["_id"] = str(project["_id"])
    
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
        
        # Save to database
        contacts_collection = get_contacts_collection()
        result = contacts_collection.insert_one(contact_data.dict())
        
        if result.inserted_id:
            return templates.TemplateResponse("contact.html", {
                "request": request,
                "page_title": "Contact",
                "success": "Thank you! Your message has been sent successfully. I'll get back to you soon!"
            })
    except Exception as e:
        return templates.TemplateResponse("contact.html", {
            "request": request,
            "page_title": "Contact", 
            "error": "Sorry, there was an error sending your message. Please try again."
        })

# Admin routes for project management
@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    projects_collection = get_projects_collection()
    contacts_collection = get_contacts_collection()
    
    all_projects = list(projects_collection.find({}))
    recent_contacts = list(contacts_collection.find({}).sort("created_at", -1).limit(5))
    
    # Convert ObjectId to string
    for project in all_projects:
        project["_id"] = str(project["_id"])
    for contact in recent_contacts:
        contact["_id"] = str(contact["_id"])
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "page_title": "Admin",
        "projects": all_projects,
        "contacts": recent_contacts
    })

@app.post("/admin/projects")
async def add_project(
    request: Request,
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

@app.delete("/admin/projects/{project_id}")
async def delete_project(project_id: str):
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