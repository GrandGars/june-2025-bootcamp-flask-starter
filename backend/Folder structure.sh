# Create all directories
mkdir -p app docs tests instance/static instance/templates

# Create all files
touch requirements.txt run.py .env .gitignore README.md
touch app/__init__.py app/routes.py app/models.py app/config.py
touch instance/__init__.py instance/config.py