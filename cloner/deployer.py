import os
import shutil
import uuid
import subprocess
import requests

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/render/project/src/.playwright"
subprocess.run(["git", "config", "--global", "user.email", "kainoa1kerr@gmail.com"])
subprocess.run(["git", "config", "--global", "user.name", "site-cloner"])

class WebsiteDeployer:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_username = os.getenv('GITHUB_USERNAME')
        if not self.github_token or not self.github_username:
            raise ValueError("GITHUB_TOKEN and GITHUB_USERNAME must be set")

    def create_github_repo(self, repo_name):
        """Create a new GitHub repo using the API"""
        url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }
        data = {"name": repo_name, "private": False}  # set True if you want private
        r = requests.post(url, headers=headers, json=data)
        if r.status_code == 201:
            print(f"GitHub repo '{repo_name}' created successfully")
            return True
        else:
            print("Failed to create repo:", r.status_code, r.text)
            return False

    def deploy_to_github_pages(self, website_data):
        repo_name = f'cloned-site-{uuid.uuid4().hex[:8]}'
        temp_dir = f'temp_repo_{uuid.uuid4().hex[:8]}'
        os.makedirs(temp_dir, exist_ok=True)

        # Save HTML
        with open(f'{temp_dir}/index.html', 'w', encoding='utf-8') as f:
            f.write(website_data['html'])

        # Copy resources if any
        if 'resources' in website_data:
            for path, local_path in website_data['resources'].items():
                shutil.copy(local_path, os.path.join(temp_dir, os.path.basename(local_path)))

        # create the GitHub repo first
        if not self.create_github_repo(repo_name):
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None

        try:
            # Initialize git
            subprocess.run(['git', 'init'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'checkout', '-b', 'main'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.email', f'{self.github_username}@users.noreply.github.com'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.name', self.github_username], cwd=temp_dir, check=True)
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)

            # Add remote and push
            remote_url = f'https://{self.github_username}:{self.github_token}@github.com/{self.github_username}/{repo_name}.git'
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url], cwd=temp_dir, check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=temp_dir, check=True)

            return f'https://{self.github_username}.github.io/{repo_name}/'
        except subprocess.CalledProcessError as e:
            print(f"GitHub deployment failed: {e}")
            return None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
