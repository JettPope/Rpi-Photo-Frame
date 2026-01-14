import os
import platform
import shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from PIL import Image
from io import BytesIO
import pillow_heif
import datetime
import json

pillow_heif.register_heif_opener()

# Use same image directory as the photo frame
if platform.system() == "Windows":  # for development only
    IMAGE_DIR = r"C:\PC\Documents\Rpi Photo Frame\Pictures"
else:
    IMAGE_DIR = "Pics"

SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".heic"]

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = IMAGE_DIR
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit for multiple files
app.secret_key = 'change-this-secret-key-for-production'  # IMPORTANT: Change this!

# Load user credentials from external file (not in version control)
USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'users.json')

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Warning: Could not load users from {USERS_FILE}")
    return {}

def save_users(users):
    """Save users to JSON file"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# Load users at startup
USERS = load_users()

def login_required(f):
    def decorated_function(*args, **kwargs):
        if not USERS:
            return redirect(url_for('setup'))
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in [ext[1:] for ext in SUPPORTED_EXTENSIONS]

def secure_path(path):
    """Secure a path by securing each component"""
    parts = path.replace('\\', '/').split('/')
    secured_parts = []
    for part in parts:
        if part:  # skip empty parts
            secured_parts.append(secure_filename(part))
    return '/'.join(secured_parts)

def collect_images(directory, base_path=""):
    """Recursively collect all image files with their dates"""
    images = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if allowed_file(file):
                rel_path = os.path.relpath(os.path.join(root, file), directory)
                full_path = os.path.join(directory, rel_path)
                try:
                    mtime = os.path.getmtime(full_path)
                    date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                except OSError:
                    date_str = 'Unknown'
                images.append({'path': rel_path, 'date': date_str})
    return images

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if USERS:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('setup'))
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('setup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters')
            return redirect(url_for('setup'))
        
        # Create the first admin user
        global USERS
        USERS[username] = generate_password_hash(password)
        save_users(USERS)
        
        session['username'] = username
        flash('Admin user created successfully!')
        return redirect(url_for('index'))
    
    return render_template('setup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not USERS:
        return redirect(url_for('setup'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and check_password_hash(USERS[username], password):
            session['username'] = username
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/manage-users')
@login_required
def manage_users():
    return render_template('manage_users.html', users=list(USERS.keys()), current_user=session.get('username'))

@app.route('/add-user', methods=['POST'])
@login_required
def add_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        flash('Username and password are required')
        return redirect(url_for('manage_users'))
    
    if username in USERS:
        flash('User already exists')
        return redirect(url_for('manage_users'))
    
    USERS[username] = generate_password_hash(password)
    save_users(USERS)
    flash(f'User {username} added successfully')
    return redirect(url_for('manage_users'))

@app.route('/delete-user/<username>')
@login_required
def delete_user(username):
    current_user = session.get('username')
    if username == current_user:
        flash('Cannot delete your own account')
        return redirect(url_for('manage_users'))
    
    if username in USERS:
        del USERS[username]
        save_users(USERS)
        flash(f'User {username} deleted')
    return redirect(url_for('manage_users'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    username = session.get('username')
    
    if not check_password_hash(USERS[username], current_password):
        flash('Current password is incorrect')
        return redirect(url_for('manage_users'))
    
    if new_password != confirm_password:
        flash('New passwords do not match')
        return redirect(url_for('manage_users'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters')
        return redirect(url_for('manage_users'))
    
    USERS[username] = generate_password_hash(new_password)
    save_users(USERS)
    flash('Password changed successfully')
    return redirect(url_for('manage_users'))

@app.route('/')
@app.route('/<path:current_path>')
@login_required
def index(current_path=''):
    view = request.args.get('view', 'folders')
    sort_by = request.args.get('sort', 'name')
    
    if view == 'gallery':
        images = collect_images(IMAGE_DIR)
        if sort_by == 'name':
            images.sort(key=lambda x: x['path'].lower())
        elif sort_by == 'date':
            images.sort(key=lambda x: os.path.getmtime(os.path.join(IMAGE_DIR, x['path'])), reverse=True)
        return render_template('gallery.html', images=images, sort_by=sort_by)
    
    # Folder view
    full_path = os.path.join(IMAGE_DIR, current_path)
    if not os.path.exists(full_path):
        return "Not found", 404
    
    items = []
    try:
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            rel_path = os.path.join(current_path, item) if current_path else item
            try:
                mtime = os.path.getmtime(item_path)
                date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            except OSError:
                date_str = 'Unknown'
            if os.path.isdir(item_path):
                items.append({'name': item, 'type': 'folder', 'path': rel_path, 'date': date_str})
            elif allowed_file(item):
                items.append({'name': item, 'type': 'file', 'path': rel_path, 'date': date_str})
    except PermissionError:
        return "Permission denied", 403
    
    # Sort items
    if sort_by == 'name':
        items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
    elif sort_by == 'date':
        def get_sort_key(item):
            item_full_path = os.path.join(IMAGE_DIR, item['path'])
            try:
                mtime = os.path.getmtime(item_full_path)
            except OSError:
                mtime = 0
            return (item['type'] == 'file', -mtime)  # folders first, then by date descending
        items.sort(key=get_sort_key)
    
    return render_template('index.html', items=items, current_path=current_path, sort_by=sort_by)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        files = request.files.getlist('files')
        uploaded_count = 0
        for file in files:
            if file.filename:
                rel_path = secure_path(file.filename)
                if rel_path:  # skip if empty after securing
                    full_path = os.path.join(IMAGE_DIR, rel_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    file.save(full_path)
                    uploaded_count += 1
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/delete/<path:filepath>')
@login_required
def delete(filepath):
    full_path = os.path.join(IMAGE_DIR, filepath)
    if os.path.exists(full_path):
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
    # Redirect to the parent directory
    parent_path = os.path.dirname(filepath)
    return redirect(url_for('index', current_path=parent_path) if parent_path != '.' else url_for('index'))

@app.route('/image/<path:filepath>')
def image(filepath):
    directory = os.path.dirname(os.path.join(IMAGE_DIR, filepath))
    filename = os.path.basename(filepath)
    if allowed_file(filename) and os.path.exists(os.path.join(directory, filename)):
        return send_from_directory(directory, filename)
    return "Not allowed", 403

@app.route('/thumb/<path:filepath>')
def thumb(filepath):
    full_path = os.path.join(IMAGE_DIR, filepath)
    if not os.path.exists(full_path) or not allowed_file(os.path.basename(filepath)):
        return "Not found", 404
    try:
        with Image.open(full_path) as im:
            im.thumbnail((200, 200))
            im = im.convert('RGB')  # Ensure RGB mode for JPEG compatibility
            img_io = BytesIO()
            im.save(img_io, 'JPEG', quality=85)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)