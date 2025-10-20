import os
import asyncio
from playwright.async_api import async_playwright
import requests
from urllib.parse import urljoin, urlparse
import base64
from bs4 import BeautifulSoup
import re

class WebsiteScraper:
    def __init__(self):
        self.downloaded_resources = {}
        
    def scrape_website(self, url):
        """Main method to scrape website"""
        return asyncio.run(self._async_scrape_website(url))
    
    async def _async_scrape_website(self, url):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                # Navigate to page
                await page.goto(url, wait_until='networkidle')
                
                # Get the HTML content
                html_content = await page.content()
                
                # Extract and download resources
                resources = await self._extract_resources(page, url, html_content)
                
                # Modify HTML to use local resources
                modified_html = self._modify_html_for_local_resources(html_content, resources, url)
                
                # Get all CSS and JavaScript code
                css_code = await self._extract_css_code(page)
                js_code = await self._extract_js_code(page)
                
                website_data = {
                    'html': modified_html,
                    'resources': resources,
                    'css_code': css_code,
                    'js_code': js_code,
                    'original_url': url
                }
                
                return website_data
                
            except Exception as e:
                print(f"Error scraping website: {e}")
                return None
            finally:
                await browser.close()
    
    async def _extract_resources(self, page, base_url, html_content):
        """Extract and download all resources (CSS, JS, images, fonts)"""
        resources = {}
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                resource_data = await self._download_resource(page, href, base_url)
                if resource_data:
                    resources[href] = resource_data
        
        # Extract JavaScript files
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                resource_data = await self._download_resource(page, src, base_url)
                if resource_data:
                    resources[src] = resource_data
        
        # Extract images
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                resource_data = await self._download_resource(page, src, base_url)
                if resource_data:
                    resources[src] = resource_data
        
        # Extract background images from inline styles
        for element in soup.find_all(style=True):
            style = element['style']
            urls = re.findall(r'url\([\'"]?(.*?)[\'"]?\)', style)
            for url in urls:
                resource_data = await self._download_resource(page, url, base_url)
                if resource_data:
                    resources[url] = resource_data
        
        return resources
    
    async def _download_resource(self, page, resource_url, base_url):
        """Download a single resource"""
        try:
            # Convert relative URL to absolute
            absolute_url = urljoin(base_url, resource_url)
            
            # Get resource content
            response = await page.goto(absolute_url)
            if response and response.status == 200:
                content = await response.body()
                
                # Determine content type and extension
                content_type = response.headers.get('content-type', '')
                extension = self._get_extension_from_url(resource_url, content_type)
                
                return {
                    'content': content,
                    'content_type': content_type,
                    'extension': extension,
                    'original_url': resource_url
                }
        except Exception as e:
            print(f"Error downloading resource {resource_url}: {e}")
        
        return None
    
    def _get_extension_from_url(self, url, content_type):
        """Get file extension from URL or content type"""
        parsed = urlparse(url)
        path = parsed.path
        
        if '.' in path:
            return path.split('.')[-1].lower()
        
        # Fallback to content type
        if 'css' in content_type:
            return 'css'
        elif 'javascript' in content_type:
            return 'js'
        elif 'image/jpeg' in content_type:
            return 'jpg'
        elif 'image/png' in content_type:
            return 'png'
        elif 'image/gif' in content_type:
            return 'gif'
        elif 'image/svg+xml' in content_type:
            return 'svg'
        
        return 'bin'
    
    def _modify_html_for_local_resources(self, html_content, resources, base_url):
        """Modify HTML to use local resource paths"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Update CSS links
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href and href in resources:
                new_filename = f"resources/{self._sanitize_filename(href)}.{resources[href]['extension']}"
                link['href'] = new_filename
        
        # Update script sources
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and src in resources:
                new_filename = f"resources/{self._sanitize_filename(src)}.{resources[src]['extension']}"
                script['src'] = new_filename
        
        # Update image sources
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src and src in resources:
                new_filename = f"resources/{self._sanitize_filename(src)}.{resources[src]['extension']}"
                img['src'] = new_filename
        
        # Update background images in inline styles
        for element in soup.find_all(style=True):
            style = element['style']
            new_style = style
            for url in re.findall(r'url\([\'"]?(.*?)[\'"]?\)', style):
                if url in resources:
                    new_filename = f"resources/{self._sanitize_filename(url)}.{resources[url]['extension']}"
                    new_style = new_style.replace(url, new_filename)
            element['style'] = new_style
        
        return str(soup)
    
    def _sanitize_filename(self, filename):
        """Sanitize filename for safe use"""
        return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    
    async def _extract_css_code(self, page):
        """Extract all CSS code from the page"""
        css_code = {}
        
        # Extract inline styles
        inline_styles = await page.evaluate("""
            () => {
                const styles = {};
                const elements = document.querySelectorAll('[style]');
                elements.forEach((el, index) => {
                    styles[`inline_${index}`] = el.getAttribute('style');
                });
                return styles;
            }
        """)
        
        css_code['inline_styles'] = inline_styles
        
        # Extract style tag content
        style_tags = await page.evaluate("""
            () => {
                const styles = {};
                const styleElements = document.querySelectorAll('style');
                styleElements.forEach((el, index) => {
                    styles[`style_tag_${index}`] = el.innerHTML;
                });
                return styles;
            }
        """)
        
        css_code['style_tags'] = style_tags
        
        return css_code
    
    async def _extract_js_code(self, page):
        """Extract all JavaScript code from the page"""
        js_code = {}
        
        # Extract inline scripts
        inline_scripts = await page.evaluate("""
            () => {
                const scripts = {};
                const scriptElements = document.querySelectorAll('script:not([src])');
                scriptElements.forEach((el, index) => {
                    if (el.innerHTML.trim()) {
                        scripts[`inline_script_${index}`] = el.innerHTML;
                    }
                });
                return scripts;
            }
        """)
        
        js_code['inline_scripts'] = inline_scripts
        
        return js_code
