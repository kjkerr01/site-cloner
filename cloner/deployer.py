import os
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/render/project/src/.playwright"
import shutil
import uuid
import subprocess

class WebsiteDeployer:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_username = os.getenv('GITHUB_USERNAME')

    def deploy_to_github_pages(self, website_data):
        repo_name = f'cloned-site-{uuid.uuid4().hex[:8]}'
        temp_dir = f'temp_repo_{uuid.uuid4().hex[:8]}'
        os.makedirs(temp_dir, exist_ok=True)

        # Save HTML
        with open(f'{temp_dir}/index.html', 'w', encoding='utf-8') as f:
            f.write(website_data['html'])

        # Copy resources
        if 'resources' in website_data:
            for path, local_path in website_data['resources'].items():
                shutil.copy(local_path, f'{temp_dir}/{os.path.basename(local_path)}')

        try:
            # Init git repo
            subprocess.run(['git', 'init'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'checkout', '-b', 'main'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            git config --global user.email "kainoa1kerr@gmail.com"
            git config --global user.name "kjkerr01"
            subprocess.run(["git", "config", "user.email", os.getenv("GITHUB_EMAIL", "noreply@example.com")])
            subprocess.run(["git", "config", "user.name", os.getenv("GITHUB_USERNAME", "site-cloner")])
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)

            # Push to GitHub
            remote_url = f'https://{self.github_username}:{self.github_token}@github.com/{self.github_username}/{repo_name}.git'
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url], cwd=temp_dir, check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=temp_dir, check=True)

            return f'https://{self.github_username}.github.io/{repo_name}/'
        except Exception as e:
            print(f"GitHub deployment failed: {e}")
            return None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
