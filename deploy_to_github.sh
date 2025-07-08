#!/bin/bash
# Script to deploy the BVD AccountAnalysis project to GitHub

echo "Starting deployment of BVD AccountAnalysis to GitHub..."

# Step 1: Initialize Git repository (if not already done)
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    echo "Git repository initialized."
else
    echo "Git repository already exists."
fi

# Step 2: Make sure .gitignore is properly set up
if [ ! -f ".gitignore" ]; then
    echo "Creating .gitignore file..."
    cat > .gitignore << EOL
# Ignore specific folders
Versions/
Data/

# Python-specific ignores
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# IDE-specific files
.idea/
.vscode/
*.swp
*.swo

# Environment files
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# OS-specific files
.DS_Store
Thumbs.db
EOL
    echo ".gitignore file created."
else
    echo ".gitignore file already exists."
fi

# Step 3: Add all files to Git
echo "Adding files to Git..."
git add .

# Step 4: Set up GitHub remote
echo "Checking if remote already exists..."
if git remote | grep -q "origin"; then
    echo "Remote 'origin' already exists. Would you like to update it? (y/n)"
    read update_remote
    if [ "$update_remote" == "y" ]; then
        git remote set-url origin https://github.com/shaymcgreal/datatransformer.git
        echo "Remote 'origin' updated."
    fi
else
    git remote add origin https://github.com/shaymcgreal/datatransformer.git
    echo "Remote 'origin' added."
fi

# Step 5: Commit changes
echo "Committing changes..."
echo "Enter commit message (e.g., 'Initial commit' or 'Update with new features'):"
read commit_message
git commit -m "$commit_message"

# Step 6: Push to GitHub
echo "Pushing to GitHub..."
echo "Which branch would you like to push to? (default: main)"
read branch
branch=${branch:-main}

git push -u origin $branch

echo "Deployment complete! Your code is now on GitHub at https://github.com/shaymcgreal/datatransformer"
echo "You can create a release by visiting your repository and clicking on 'Releases' > 'Create a new release'"
