from flask import Flask, render_template, request, jsonify
import os
import uuid
import threading
from cloner.scraper import WebsiteScraper
from cloner.deployer import WebsiteDeployer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Store cloning tasks
tasks = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clone', methods=['POST'])
def clone_website():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'processing', 'url': url, 'cloned_url': None}
    
    # Start cloning process in background thread
    thread = threading.Thread(target=process_cloning, args=(task_id, url))
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def get_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(task)

def process_cloning(task_id, url):
    try:
        # Step 1: Scrape the website
        scraper = WebsiteScraper()
        task_data = tasks[task_id]
        
        task_data['status'] = 'scraping_website'
        website_data = scraper.scrape_website(url)
        
        if not website_data:
            task_data['status'] = 'error'
            task_data['message'] = 'Failed to scrape website'
            return
        
        # Step 2: Deploy the cloned website
        task_data['status'] = 'deploying'
        deployer = WebsiteDeployer()
        
        cloned_url = deployer.deploy_to_github_pages(website_data)
        
        if cloned_url:
            task_data['status'] = 'completed'
            task_data['cloned_url'] = cloned_url
        else:
            task_data['status'] = 'error'
            task_data['message'] = 'Failed to deploy website'
            
    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['message'] = str(e)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
