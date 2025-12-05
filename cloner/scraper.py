import os
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/render/project/src/.playwright"
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re
import requests
import uuid
import shutil
import zipfile
from flask import Flask, request, send_file

app = Flask(__name__)

# -------------------------
# SCRAPER
# -------------------------

class WebsiteScraper:
    def __init__(self):
        self.downloaded_resources = {}

    def scrape_website(self, url):
        return asyncio.run(self._async_scrape_website(url))

    async def _async_scrape_website(self, url):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle')

            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            resources = {}
            os.makedirs('temp_resources', exist_ok=True)

            # CSS
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href:
                    content = self._download_file(url, href)
                    if content:
                        filename = self._sanitize_filename(href)
                        path = f'temp_resources/{filename}'
                        with open(path, 'wb') as f:
                            f.write(content)
                        resources[href] = path
                        link['href'] = filename

            # JS
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src:
                    content = self._download_file(url, src)
                    if content:
                        filename = self._sanitize_filename(src)
                        path = f'temp_resources/{filename}'
                        with open(path, 'wb') as f:
                            f.write(content)
                        resources[src] = path
                        script['src'] = filename

            # Images
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                if src:
                    content = self._download_file(url, src)
                    if content:
                        filename = self._sanitize_filename(src)
                        path = f'temp_resources/{filename}'
                        with open(path, 'wb') as f:
                            f.write(content)
                        resources[src] = path
                        img['src'] = filename

            await browser.close()
            modified_html = str(soup)
            return {'html': modified_html, 'resources': resources}

    def _download_file(self, base_url, file_url):
        try:
            abs_url = urljoin(base_url, file_url)
            r = requests.get(abs_url, timeout=10)
            if r.status_code == 200:
                return r.content
        except Exception as e:
            print(f"Failed to download {file_url}: {e}")
        return None

    def _sanitize_filename(self, filename):
        return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)


scraper = WebsiteScraper()

# -------------------------
# ZIP DOWNLOAD ENDPOINT
# -------------------------

@app.route("/clone", methods=["POST"])
def clone():
    data = request.json
    url = data["url"]

    website_data = scraper.scrape_website(url)

    # folder for this download
    folder = f"site_{uuid.uuid4().hex}"
    os.makedirs(folder, exist_ok=True)

    # write HTML
    with open(f"{folder}/index.html", "w", encoding="utf-8") as f:
        f.write(website_data["html"])

    # copy resources into that folder
    for _, src_path in website_data["resources"].items():
        shutil.copy(src_path, os.path.join(folder, os.path.basename(src_path)))

    # zip it
    zip_path = f"{folder}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, folder)
                z.write(full_path, arcname)

    # delete folder
    shutil.rmtree(folder, ignore_errors=True)

    return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
