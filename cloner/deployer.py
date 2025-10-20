import os
import base64
import uuid
from github import Github
from github import Auth
import tempfile
import shutil

class WebsiteDeployer:
    def __init__(self):
        # You'll need to set these environment variables
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_username = os.getenv('GITHUB_USERNAME')
    
    def deploy_to_github_pages(self, website_data):
        """Deploy the cloned website to GitHub Pages"""
        try:
            if not self.github_token or not self.github_username:
                return self._deploy_to_temp_location(website_data)
            
            # Create a unique repository name
            repo_name = f"cloned-site-{uuid.uuid4().hex[:8]}"
            
            # Initialize GitHub client
            auth = Auth.Token(self.github_token)
            g = Github(auth=auth)
            user = g.get_user()
            
            # Create new repository
            repo = user.create_repo(
                repo_name,
                description="Cloned website",
                private=False,
                auto_init=False
            )
            
            # Create necessary files
            self._create_github_files(repo, website_data)
            
            # Enable GitHub Pages
            repo.create_pages(branch="main", path="/")
            
            # Return the GitHub Pages URL
            return f"https://{self.github_username}.github.io/{repo_name}/"
            
        except Exception as e:
            print(f"Error deploying to GitHub: {e}")
            # Fallback to temporary deployment
            return self._deploy_to_temp_location(website_data)
    
    def _create_github_files(self, repo, website_data):
        """Create all necessary files in the GitHub repository"""
        
        # Create index.html
        repo.create_file("index.html", "Add cloned website", website_data['html'])
        
        # Create resources directory and files
        for resource_path, resource_data in website_data['resources'].items():
            file_path = f"resources/{self._sanitize_filename(resource_path)}.{resource_data['extension']}"
            content_base64 = base64.b64encode(resource_data['content']).decode()
            repo.create_file(file_path, f"Add resource {resource_path}", content_base64)
        
        # Create CSS files from extracted code
        for css_name, css_content in website_data['css_code'].items():
            if isinstance(css_content, dict):
                for sub_name, sub_content in css_content.items():
                    if sub_content:
                        file_path = f"css/{css_name}_{sub_name}.css"
                        repo.create_file(file_path, f"Add CSS {css_name}_{sub_name}", sub_content)
        
        # Create JS files from extracted code
        for js_name, js_content in website_data['js_code'].items():
            if isinstance(js_content, dict):
                for sub_name, sub_content in js_content.items():
                    if sub_content:
                        file_path = f"js/{js_name}_{sub_name}.js"
                        repo.create_file(file_path, f"Add JS {js_name}_{sub_name}", sub_content)
    
    def _deploy_to_temp_location(self, website_data):
        """Fallback deployment method (for demo purposes)"""
        # In a real implementation, you might deploy to:
        # - Netlify
        # - Vercel
        # - Render.com
        # - Or any other hosting service
        
        # For now, we'll just return a message
        # In production, implement actual deployment to your preferred platform
        return "https://example.com/deployment-not-configured"
    
    def _sanitize_filename(self, filename):
        """Sanitize filename for safe use"""
        import re
        return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
