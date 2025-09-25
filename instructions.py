# portfolio-website/
# ├── app/
# │   ├── __init__.py          # (empty file - makes it a Python package)
# │   ├── main.py             # Main FastAPI application
# │   ├── database.py         # MongoDB connection
# │   └── models.py           # Data models
# ├── templates/              # HTML templates folder
# │   ├── base.html           # Base template
# │   ├── home.html           # Home page
# │   ├── about.html          # About page
# │   ├── projects.html       # Projects page
# │   └── contact.html        # Contact page
# ├── static/                 # Static files folder
# │   ├── css/
# │   │   └── style.css       # Your custom styles
# │   ├── js/
# │   │   └── main.js         # Your JavaScript
# │   └── images/             # Your images
# ├── requirements.txt        # Python dependencies
# └── .env                    # Environment variables (passwords, etc.)

# uvicorn app.main:app --reload
# venv\Scripts\activate

# FastAPI: Web framework (like Flask but more modern)
# Uvicorn: Server to run your FastAPI app
# Jinja2: Template engine for HTML
# PyMongo: MongoDB Python driver
# Python-multipart: For handling file uploads
# Python-dotenv: For managing environment variables

# pip freeze > requirements.txt