# Upload to Cloudinary with AppEngine!
## Documentation Created with Google Gemini 2.5 Pro 03-25
### Let's build this Python application for Google App Engine Standard Environment (Python 3). It will use Flask as the web framework, Cloudinary for image/video handling, Google Sign-In for authentication, and Google Cloud Datastore to keep track of uploaded files per user.

**Key Components:**

1.  **App Engine Setup (`app.yaml`)**: Configures the GAE environment.
2.  **Dependencies (`requirements.txt`)**: Lists necessary Python packages.
3.  **Main Application (`main.py`)**: Contains the Flask routes, logic for authentication, Cloudinary uploads/transformations, and Datastore interaction.
4.  **HTML Templates (`templates/`)**: Frontend views (Login page, File Manager page).
5.  **Static Files (`static/`)**: CSS and JavaScript (including Google Sign-In logic).

---

**Prerequisites:**

1.  **Google Cloud Project:** Create or select a Google Cloud project.
2.  **Enable APIs:**
    *   Google App Engine Admin API
    *   Cloud Datastore API
    *   (Optional but recommended) Secret Manager API (to store secrets securely)
3.  **Create OAuth 2.0 Client ID:**
    *   Go to "APIs & Services" > "Credentials" in your Cloud Console.
    *   Click "Create Credentials" > "OAuth client ID".
    *   Select "Web application".
    *   Give it a name (e.g., "App Engine Cloudinary Uploader Auth").
    *   **Important:** Add Authorized JavaScript origins:
        *   `http://localhost:8080` (for local testing)
        *   `https://YOUR_PROJECT_ID.appspot.com` (replace `YOUR_PROJECT_ID` with your actual project ID after deployment)
        *   `https://YOUR_CUSTOM_DOMAIN` (if you use one)
    *   Note down the **Client ID**. You'll need it.
4.  **Cloudinary Account:** Sign up for a Cloudinary account (free tier is available). Note down your **Cloud Name**, **API Key**, and **API Secret**.
5.  **Google Cloud SDK:** Install and initialize the `gcloud` command-line tool. ([https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install))
6.  **Python 3:** Ensure you have Python 3.7+ installed locally.

---

**Step 1: Project Structure**

Create the following directory structure:

```
gae-cloudinary-manager/
├── app.yaml
├── requirements.txt
├── main.py
├── templates/
│   ├── base.html
│   ├── login.html
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

---

**Step 2: `requirements.txt`**

List the Python dependencies:

```txt
# gae-cloudinary-manager/requirements.txt

Flask>=2.0
cloudinary>=1.26  # Or latest version
google-cloud-datastore>=2.5 # Or latest version
google-auth>=2.3 # Or latest version
requests>=2.25 # google-auth dependency
gunicorn>=20.1 # For App Engine deployment
python-dotenv>=0.19 # For local development env vars (optional but good practice)
```

---

**Step 3: `app.yaml`**

Configure your App Engine application:

```yaml
# gae-cloudinary-manager/app.yaml

runtime: python39 # Or python310, python311 etc. choose a supported version
entrypoint: gunicorn -b :$PORT main:app

instance_class: F1 # Basic instance class, adjust if needed

env_variables:
  # --- Cloudinary Configuration ---
  # **BEST PRACTICE:** Use Secret Manager instead of putting secrets here directly.
  # See: https://cloud.google.com/appengine/docs/standard/python3/configuring-variables#setting_environment_variables
  # Example using Secret Manager (replace 1 with latest version):
  # CLOUDINARY_CLOUD_NAME: "projects/YOUR_PROJECT_ID/secrets/cloudinary-cloud-name/versions/1"
  # CLOUDINARY_API_KEY: "projects/YOUR_PROJECT_ID/secrets/cloudinary-api-key/versions/1"
  # CLOUDINARY_API_SECRET: "projects/YOUR_PROJECT_ID/secrets/cloudinary-api-secret/versions/1"

  # --- Google Sign-In Configuration ---
  # GOOGLE_CLIENT_ID: "projects/YOUR_PROJECT_ID/secrets/google-client-id/versions/1" # Or hardcode if less sensitive

  # --- Flask Session ---
  # FLASK_SECRET_KEY: "projects/YOUR_PROJECT_ID/secrets/flask-secret-key/versions/1" # Generate a strong random key

  # --- FOR SIMPLICITY (but less secure) put values directly ---
  CLOUDINARY_CLOUD_NAME: "YOUR_CLOUDINARY_CLOUD_NAME"
  CLOUDINARY_API_KEY: "YOUR_CLOUDINARY_API_KEY"
  CLOUDINARY_API_SECRET: "YOUR_CLOUDINARY_API_SECRET"
  GOOGLE_CLIENT_ID: "YOUR_GOOGLE_OAUTH_CLIENT_ID.apps.googleusercontent.com" # Get from Cloud Console Credentials
  FLASK_SECRET_KEY: "a_very_secret_random_string_for_sessions" # CHANGE THIS! Generate a real secret.

handlers:
  # Serve static files
  - url: /static
    static_dir: static

  # All other requests go to the Flask app
  - url: /.*
    script: auto
```

**Important Security Note:** Storing secrets directly in `app.yaml` is convenient but **not recommended** for production. Use Google Secret Manager as indicated in the comments for better security. You would need to grant the App Engine service account permission to access these secrets.

---

**Step 4: `templates/base.html`**

A base template for common HTML structure.

```html
<!-- gae-cloudinary-manager/templates/base.html -->
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Cloudinary File Manager{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <!-- Google Platform Library for Sign-In -->
    <script src="https://apis.google.com/js/platform.js" async defer></script>
    <meta name="google-signin-client_id" content="{{ google_client_id }}">
    {% block head_extra %}{% endblock %}
</head>
<body>
    <header>
        <h1>AppEngine Cloudinary Manager</h1>
        <nav>
            {% if g.user %}
                <span>Welcome, {{ g.user['name'] }} ({{ g.user['email'] }})</span>
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
            {% endif %}
        </nav>
    </header>

    <main>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <ul class=flashes>
                {% for category, message in messages %}
                    <li class="{{ category }}">{{ message }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <footer>
        <p>Powered by App Engine & Cloudinary</p>
    </footer>

    <script src="{{ url_for('static', filename='script.js') }}"></script>
    {% block scripts_extra %}{% endblock %}
</body>
</html>
```

---

**Step 5: `templates/login.html`**

The login page with the Google Sign-In button.

```html
<!-- gae-cloudinary-manager/templates/login.html -->
{% extends "base.html" %}

{% block title %}Login{% endblock %}

{% block content %}
    <h2>Please Login</h2>
    <p>Login with your Google Account to manage files.</p>

    <!-- Google Sign-In Button -->
    <div id="google-signin-button" class="g-signin2" data-onsuccess="onSignIn" data-theme="dark"></div>

    <form id="google-auth-form" action="{{ url_for('auth_google') }}" method="post" style="display: none;">
        <input type="hidden" name="id_token" id="id_token_field">
    </form>

{% endblock %}

{% block scripts_extra %}
<script>
    function onSignIn(googleUser) {
      console.log('Google Sign-In Success');
      var id_token = googleUser.getAuthResponse().id_token;
      // console.log("ID Token: " + id_token); // For debugging
      document.getElementById('id_token_field').value = id_token;
      document.getElementById('google-auth-form').submit(); // Send token to backend
    }

    function signOut() {
        var auth2 = gapi.auth2.getAuthInstance();
        auth2.signOut().then(function () {
            console.log('User signed out.');
            // Redirect to backend logout to clear session
            window.location.href = "{{ url_for('logout') }}";
        });
    }

    // Optional: If user is already signed in, maybe trigger onSignIn automatically
    // gapi.load('auth2', function() {
    //     gapi.auth2.init().then(function(){
    //         var auth2 = gapi.auth2.getAuthInstance();
    //         if (auth2.isSignedIn.get()) {
    //             var googleUser = auth2.currentUser.get();
    //             onSignIn(googleUser);
    //         } else {
    //             // Render the button if not signed in
    //            gapi.signin2.render('google-signin-button', {
    //                'scope': 'profile email',
    //                'width': 240,
    //                'height': 50,
    //                'longtitle': true,
    //                'theme': 'dark',
    //                'onsuccess': onSignIn
    //            });
    //         }
    //     });
    // });
</script>
{% endblock %}
```

---

**Step 6: `templates/index.html`**

The main file manager interface (upload form and file list).

```html
<!-- gae-cloudinary-manager/templates/index.html -->
{% extends "base.html" %}

{% block title %}File Manager{% endblock %}

{% block content %}
    <h2>Upload New File</h2>
    <form method="post" action="{{ url_for('upload') }}" enctype="multipart/form-data">
        <label for="file">Choose file (Image or Video):</label>
        <input type="file" id="file" name="file" accept="image/*,video/*" required>
        <br><br>
        <fieldset>
            <legend>Optional Transformations on Upload</legend>
            <label for="width">Resize Width:</label>
            <input type="number" name="width" id="width" placeholder="e.g., 500"> px
            <br>
            <label for="height">Resize Height:</label>
            <input type="number" name="height" id="height" placeholder="e.g., 400"> px
            <br>
            <label for="crop">Crop Mode:</label>
            <select name="crop" id="crop">
                <option value="">None</option>
                <option value="fill">Fill</option>
                <option value="fit">Fit</option>
                <option value="crop">Crop</option>
                <option value="thumb">Thumbnail</option>
            </select>
             <br>
            <label for="effect">Effect:</label>
            <select name="effect" id="effect">
                <option value="">None</option>
                <option value="sepia">Sepia</option>
                <option value="grayscale">Grayscale</option>
                <option value="vignette">Vignette</option>
                <option value="cartoonify">Cartoonify</option>
            </select>
        </fieldset>
        <br>
        <button type="submit">Upload</button>
    </form>

    <hr>

    <h2>My Uploaded Files</h2>
    {% if assets %}
        <div class="file-grid">
            {% for asset in assets %}
                <div class="file-item">
                    <h3>{{ asset.public_id }}</h3>
                    <p>Type: {{ asset.resource_type }} | Format: {{ asset.format }}</p>
                    <p>Uploaded: {{ asset.created_at.strftime('%Y-%m-%d %H:%M') if asset.created_at else 'N/A' }}</p>

                    {% if asset.resource_type == 'image' %}
                        <img src="{{ asset.thumbnail_url }}" alt="Thumbnail for {{ asset.public_id }}">
                    {% elif asset.resource_type == 'video' %}
                        <video width="150" height="100" controls>
                            <source src="{{ asset.thumbnail_url }}" type="video/{{ asset.format if asset.format in ['mp4', 'webm', 'ogv'] else 'mp4' }}">
                            Your browser does not support the video tag.
                        </video>
                    {% else %}
                        <p><i>Preview not available</i></p>
                    {% endif %}

                    <p>
                        <a href="{{ asset.secure_url }}" target="_blank">View Original</a>
                    </p>
                    {% if asset.upload_transformations %}
                        <p><strong>Uploaded with:</strong> {{ asset.upload_transformations | join(', ') }}</p>
                    {% endif %}

                    <details>
                        <summary>More Details & Transformations</summary>
                        <p>Public ID: <code>{{ asset.public_id }}</code></p>
                        <p>Secure URL: <code>{{ asset.secure_url }}</code></p>
                         <p>
                           Thumbnail (150x100, fill): <a href="{{ asset.thumbnail_url }}" target="_blank">Link</a><br>
                           Grayscale: <a href="{{ asset.grayscale_url }}" target="_blank">Link</a><br>
                           Resized (w=300): <a href="{{ asset.resized_url }}" target="_blank">Link</a>
                        </p>
                    </details>

                    <form action="{{ url_for('delete_asset', asset_key_str=asset.key.urlsafe().decode('utf-8')) }}" method="post" style="margin-top: 10px;">
                         <button type="submit" class="delete-button" onclick="return confirm('Are you sure you want to delete {{ asset.public_id }}?');">Delete</button>
                    </form>
                </div>
            {% endfor %}
        </div>
    {% else %}
        <p>You haven't uploaded any files yet.</p>
    {% endif %}

{% endblock %}
```

---

**Step 7: `static/style.css`**

Basic styling.

```css
/* gae-cloudinary-manager/static/style.css */

body {
    font-family: sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: #f4f4f4;
    color: #333;
}

header {
    background: #333;
    color: #fff;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

header h1 {
    margin: 0;
    font-size: 1.5rem;
}

header nav a {
    color: #fff;
    text-decoration: none;
    margin-left: 1rem;
}
header nav span {
    margin-left: 1rem;
    font-style: italic;
}


main {
    padding: 2rem;
    max-width: 1000px;
    margin: 20px auto;
    background: #fff;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

footer {
    text-align: center;
    margin-top: 2rem;
    padding: 1rem;
    background: #eee;
    color: #555;
    font-size: 0.9rem;
}

/* Forms */
form label {
    display: block;
    margin-bottom: 5px;
}
form input[type="file"],
form input[type="number"],
form select {
    padding: 8px;
    margin-bottom: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
}
form button[type="submit"] {
    background: #5cb85c;
    color: white;
    padding: 10px 15px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
form button[type="submit"]:hover {
    background: #4cae4c;
}
form fieldset {
    border: 1px solid #ddd;
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 4px;
}
form legend {
    font-weight: bold;
    padding: 0 5px;
}


/* Flashes */
.flashes {
    list-style: none;
    padding: 0;
    margin-bottom: 1rem;
}
.flashes li {
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 5px;
}
.flashes .success { background-color: #dff0d8; border: 1px solid #d6e9c6; color: #3c763d; }
.flashes .error { background-color: #f2dede; border: 1px solid #ebccd1; color: #a94442; }
.flashes .info { background-color: #d9edf7; border: 1px solid #bce8f1; color: #31708f; }


/* File Grid */
.file-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.file-item {
    border: 1px solid #ddd;
    padding: 15px;
    background-color: #f9f9f9;
    border-radius: 5px;
    word-wrap: break-word; /* Ensure long IDs don't overflow */
}
.file-item h3 {
    margin-top: 0;
    font-size: 1.1rem;
}
.file-item img, .file-item video {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 10px 0;
    border: 1px solid #eee;
}
.file-item p {
    margin: 5px 0;
    font-size: 0.9rem;
}
.file-item code {
    background-color: #eee;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 0.85rem;
    word-break: break-all;
}
.file-item details {
    margin-top: 10px;
    font-size: 0.9rem;
}
.file-item summary {
    cursor: pointer;
    font-weight: bold;
}
.file-item .delete-button {
    background-color: #d9534f;
    color: white;
    padding: 5px 10px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
}
.file-item .delete-button:hover {
    background-color: #c9302c;
}

/* Google Signin Button */
#google-signin-button {
    margin-top: 20px;
    display: inline-block; /* Adjust alignment */
}

```

---

**Step 8: `static/script.js`**

Currently, this file is mainly needed for the Google Sign-In callback defined in `login.html` and `base.html`. You could add more frontend logic here if needed (e.g., AJAX uploads, dynamic transformation previews).

```javascript
// gae-cloudinary-manager/static/script.js

// Google Sign-In functions (onSignIn, signOut) are defined inline
// in login.html and base.html where they have access to Flask's url_for and config.

console.log("Static script loaded.");

// Add any other global frontend JavaScript here if needed.
```

---

**Step 9: `main.py`**

This is the core of the application.

```python
# gae-cloudinary-manager/main.py

import os
import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
)
from google.cloud import datastore
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import cloudinary
import cloudinary.uploader
import cloudinary.api
import cloudinary.utils

# --- Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key-change-me') # Essential for sessions
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm', 'mkv'} # Adjust as needed

# Cloudinary Configuration (using environment variables set in app.yaml or locally)
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
    secure = True # Use HTTPS URLs
)

# Google Cloud Datastore Client
datastore_client = datastore.Client()
ASSET_KIND = "CloudinaryAsset" # Datastore Kind for storing asset references

# --- Helper Functions ---

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Decorator to ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_info' not in session:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login'))
        # Make user info available globally in templates via 'g'
        g.user = session.get('user_info')
        return f(*args, **kwargs)
    return decorated_function

def verify_google_token(token):
    """Verifies Google ID token and returns user info."""
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        # ID token is valid. Get the user's Google Account ID from the decoded token.
        # Typically contains 'sub', 'email', 'name', 'picture', etc.
        return idinfo
    except ValueError as e:
        # Invalid token
        app.logger.error(f"Google token verification failed: {e}")
        return None
    except Exception as e:
        app.logger.error(f"An unexpected error occurred during token verification: {e}")
        return None

def save_asset_reference(user_email, upload_result, transformations_applied=None):
    """Saves asset metadata to Datastore."""
    key = datastore_client.key(ASSET_KIND) # Auto-generate ID
    entity = datastore.Entity(key=key)
    entity.update({
        'user_email': user_email,
        'public_id': upload_result['public_id'],
        'resource_type': upload_result['resource_type'],
        'format': upload_result.get('format'), # Format might not exist for raw files etc.
        'version': upload_result['version'],
        'secure_url': upload_result['secure_url'],
        'created_at': datetime.datetime.utcnow(),
        'bytes': upload_result['bytes'],
        'upload_transformations': transformations_applied or [] # Store list of transformations applied
    })
    datastore_client.put(entity)
    app.logger.info(f"Saved asset reference to Datastore: {entity.key}")
    return entity

def list_user_assets(user_email):
    """Lists assets for a specific user from Datastore."""
    query = datastore_client.query(kind=ASSET_KIND)
    query.add_filter('user_email', '=', user_email)
    query.order = ['-created_at'] # Show newest first
    results = list(query.fetch())

    # Add dynamically generated transformation URLs for easy display
    for asset in results:
         # Store the key for deletion purposes
        asset.key = asset.id or asset.key.name # Make key accessible directly

        # Basic thumbnail
        asset.thumbnail_url = cloudinary.utils.cloudinary_url(
            asset['public_id'],
            resource_type=asset['resource_type'],
            format=asset.get('format'),
            version=asset['version'],
            width=150, height=100, crop="fill", # Adjust thumbnail size/crop
            secure=True
        )[0] # cloudinary_url returns (url, options)

        # Example other transformations
        asset.grayscale_url = cloudinary.utils.cloudinary_url(
            asset['public_id'], resource_type=asset['resource_type'], format=asset.get('format'), version=asset['version'],
            effect="grayscale", secure=True
        )[0]
        asset.resized_url = cloudinary.utils.cloudinary_url(
            asset['public_id'], resource_type=asset['resource_type'], format=asset.get('format'), version=asset['version'],
            width=300, crop="limit", secure=True # Limit ensures it doesn't upscale
        )[0]

    return results

def delete_asset_reference_and_cloudinary(asset_key_str, user_email):
    """Deletes asset from Datastore and Cloudinary after verifying ownership."""
    try:
        key = datastore_client.key(ASSET_KIND, int(asset_key_str) if asset_key_str.isdigit() else asset_key_str) # Handle numeric/string IDs if structure changes
        # Or if using urlsafe key from template:
        key = datastore_client.key(urlsafe=asset_key_str.encode('utf-8'))

        entity = datastore_client.get(key)

        if not entity:
            app.logger.warning(f"Asset key {asset_key_str} not found in Datastore.")
            return False, "Asset not found."

        if entity['user_email'] != user_email:
            app.logger.error(f"User {user_email} attempted to delete asset belonging to {entity['user_email']}.")
            return False, "Permission denied."

        # Delete from Cloudinary first
        public_id = entity['public_id']
        resource_type = entity['resource_type']
        try:
            delete_result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            if delete_result.get('result') != 'ok' and delete_result.get('result') != 'not found':
                 # Log error but proceed to delete from Datastore maybe? Or stop?
                 app.logger.error(f"Cloudinary deletion failed for {public_id}: {delete_result}")
                 # Decide if this is a fatal error for the operation
                 # return False, "Cloudinary deletion failed."
            app.logger.info(f"Cloudinary deletion result for {public_id}: {delete_result.get('result')}")
        except Exception as e:
            app.logger.error(f"Error calling Cloudinary destroy for {public_id}: {e}")
            # Decide if this is a fatal error
            # return False, "Error during Cloudinary deletion."

        # Delete from Datastore
        datastore_client.delete(key)
        app.logger.info(f"Deleted asset {asset_key_str} (Cloudinary public_id: {public_id}) from Datastore.")
        return True, "Asset deleted successfully."

    except Exception as e:
        app.logger.error(f"Error deleting asset {asset_key_str}: {e}")
        return False, "An error occurred during deletion."


# --- Flask Routes ---

@app.before_request
def load_logged_in_user():
    """If user_id is stored in the session, load the user object."""
    user_info = session.get('user_info')
    if user_info is None:
        g.user = None
    else:
        g.user = user_info
    # Make Google Client ID available to base template
    g.google_client_id = GOOGLE_CLIENT_ID


@app.route('/login')
def login():
    """Renders the login page."""
    if g.user: # If already logged in, redirect to index
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/auth/google', methods=['POST'])
def auth_google():
    """Handles the callback from Google Sign-In."""
    token = request.form.get('id_token')
    if not token:
        flash('Authentication token missing.', 'error')
        return redirect(url_for('login'))

    user_info = verify_google_token(token)

    if user_info and 'email' in user_info:
        # Store essential user info in session
        session['user_info'] = {
            'id': user_info['sub'], # Google's unique user ID
            'name': user_info.get('name'),
            'email': user_info['email'],
            'picture': user_info.get('picture')
        }
        session.permanent = True # Make session last longer
        app.logger.info(f"User logged in: {user_info['email']}")
        flash(f"Welcome, {user_info.get('name', user_info['email'])}!", 'success')
        return redirect(url_for('index'))
    else:
        flash('Invalid Google Sign-In token. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logs the user out."""
    session.pop('user_info', None)
    flash('You have been logged out.', 'info')
    # Note: We don't strictly need to call Google's signout here,
    # as our session is cleared. The frontend JS handles Google's side if needed.
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Displays the main file manager page (list of files and upload form)."""
    user_email = g.user['email']
    assets = list_user_assets(user_email)
    return render_template('index.html', assets=assets)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    """Handles file uploads to Cloudinary."""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        try:
            # Build transformation options from form
            transform_options = []
            applied_transform_descriptions = [] # For storing in Datastore

            width = request.form.get('width')
            height = request.form.get('height')
            crop = request.form.get('crop')
            effect = request.form.get('effect')

            if width or height or crop:
                transform = {"width": width or None, "height": height or None, "crop": crop or None}
                # Remove None values before adding to options
                transform_options.append({k: v for k, v in transform.items() if v})
                desc = f"resize(w:{width or 'auto'}, h:{height or 'auto'}, crop:{crop or 'none'})"
                applied_transform_descriptions.append(desc)

            if effect:
                transform_options.append({"effect": effect})
                applied_transform_descriptions.append(f"effect({effect})")


            # Upload to Cloudinary
            # resource_type="auto" lets Cloudinary detect image/video
            # Pass transformations directly in the upload call
            # Use user's email (sanitized) or user ID as part of the public_id prefix for organization
            user_prefix = g.user['email'].split('@')[0].replace('.', '-') # Simple prefix
            public_id = f"user_{user_prefix}/{file.filename.rsplit('.', 1)[0]}_{os.urandom(4).hex()}" # Add randomness

            upload_result = cloudinary.uploader.upload(
                file,
                resource_type="auto",
                public_id=public_id,
                folder=f"appengine_uploads/{g.user['email']}", # Organize in Cloudinary folders
                transformation=transform_options if transform_options else None
                # Other options: tags=['appengine', 'user_upload'], context={'user_id': g.user['id']}
            )

            app.logger.info(f"Cloudinary upload successful: {upload_result.get('public_id')}")

            # Save reference to Datastore
            save_asset_reference(g.user['email'], upload_result, applied_transform_descriptions)

            flash(f"File '{upload_result.get('original_filename', file.filename)}' uploaded successfully!", 'success')

        except Exception as e:
            app.logger.error(f"Upload failed: {e}")
            flash(f'An error occurred during upload: {e}', 'error')
            # Consider more specific error handling for Cloudinary exceptions

        return redirect(url_for('index'))
    else:
        flash('File type not allowed.', 'error')
        return redirect(url_for('index'))


@app.route('/delete/<string:asset_key_str>', methods=['POST'])
@login_required
def delete_asset(asset_key_str):
    """Deletes an asset from Cloudinary and Datastore."""
    user_email = g.user['email']
    success, message = delete_asset_reference_and_cloudinary(asset_key_str, user_email)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('index'))


# --- Local Development Server ---
if __name__ == '__main__':
    # Load environment variables from .env file for local development (optional)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        # Reload config vars potentially overridden by .env
        app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key-change-me')
        GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
        cloudinary.config( # Re-configure Cloudinary with .env vars
            cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
            api_key = os.environ.get('CLOUDINARY_API_KEY'),
            api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
            secure = True
        )
        print("Loaded environment variables from .env")
    except ImportError:
        print("dotenv not installed, skipping .env file load.")
    except Exception as e:
        print(f"Error loading .env: {e}")

    # Check essential config
    if not GOOGLE_CLIENT_ID or not os.environ.get('CLOUDINARY_CLOUD_NAME'):
         print("\n*** WARNING: Essential configuration (GOOGLE_CLIENT_ID, CLOUDINARY_*) not found in environment variables. Set them directly or use a .env file for local testing. ***\n")

    # Run the app
    # Use host='0.0.0.0' to be accessible from network if needed
    # Debug=True enables auto-reloading and detailed error pages (DO NOT USE IN PRODUCTION)
    app.run(host='127.0.0.1', port=8080, debug=True)
```

---

**Step 10: Local Development (Optional but Recommended)**

1.  **Create `.env` file:** In the `gae-cloudinary-manager` directory, create a file named `.env` (this file should *not* be committed to version control).
    ```dotenv
    # gae-cloudinary-manager/.env
    FLASK_SECRET_KEY='your_strong_random_secret_key_here_for_local_dev'
    GOOGLE_CLIENT_ID='YOUR_GOOGLE_OAUTH_CLIENT_ID.apps.googleusercontent.com'
    CLOUDINARY_CLOUD_NAME='YOUR_CLOUDINARY_CLOUD_NAME'
    CLOUDINARY_API_KEY='YOUR_CLOUDINARY_API_KEY'
    CLOUDINARY_API_SECRET='YOUR_CLOUDINARY_API_SECRET'

    # Required for local Datastore emulator interaction if running it
    # DATASTORE_EMULATOR_HOST=localhost:8081
    # DATASTORE_PROJECT_ID=your-local-project-id # Can be different from cloud project
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run Locally:**
    ```bash
    python main.py
    ```
    Or using gunicorn (closer to App Engine environment):
    ```bash
    gunicorn -b 127.0.0.1:8080 main:app
    ```
4.  **Access:** Open `http://127.0.0.1:8080` or `http://localhost:8080` in your browser. Make sure you added `http://localhost:8080` to your Google OAuth Client ID's Authorized JavaScript origins.

    *(Optional: To test Datastore locally without connecting to the cloud, you can run the Datastore Emulator: `gcloud beta emulators datastore start`. Then uncomment the `DATASTORE_*` lines in your `.env` file).*

---

**Step 11: Deployment to App Engine**

1.  **Ensure `app.yaml` is configured:** Double-check your `runtime`, `entrypoint`, and especially the `env_variables`. **Use Secret Manager for production secrets!**
2.  **Authenticate gcloud:** Make sure you are logged into the correct Google Cloud account (`gcloud auth login`) and have set the correct project (`gcloud config set project YOUR_PROJECT_ID`).
3.  **Deploy:** Navigate to the `gae-cloudinary-manager` directory in your terminal and run:
    ```bash
    gcloud app deploy
    ```
4.  **Access:** After deployment, access your application using the URL provided by `gcloud` (usually `https://YOUR_PROJECT_ID.appspot.com`) or run `gcloud app browse`. Make sure this URL is also added to your Google OAuth Client ID's Authorized JavaScript origins.

---

This comprehensive setup provides a functional lightweight file manager on App Engine, leveraging Cloudinary for media handling and transformations, secured by Google Sign-In. Remember to replace placeholders and handle secrets appropriately for production use.
