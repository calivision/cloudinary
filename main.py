# --- START OF main.py ---
import os
import datetime
import sys # Import sys for stderr
from functools import wraps

# ... (other imports) ...
import cloudinary
import cloudinary.uploader
import cloudinary.api
import cloudinary.utils

from google.cloud import datastore
# Removed problematic import from google.oauth2.id_token
# from google.oauth2.id_token import verify_oauth2_token
# Let's use the definition within the file for now
from google.auth.transport import requests as google_requests # Need this for verify_google_token
from google.oauth2 import id_token # Need this for verify_google_token

# THIS IS THE CRITICAL IMPORT
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, g, jsonify, make_response
)

print("--- Imports completed ---", file=sys.stderr) # Added print to stderr

# --- Configuration ---
app = Flask(__name__)

# --- Read Secrets ---

# Flask Secret Key (from Environment Variable set by Cloud Run secret config)
app_secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app_secret_key:
    app.logger.error("FLASK_SECRET_KEY environment variable not set.")
    # Handle error appropriately - maybe raise an exception or use a default only for non-prod
    app_secret_key = 'fallback-insecure-key-only-for-local-dev' # Avoid using this in prod
app.config['SECRET_KEY'] = app_secret_key

# Google Client ID (from Environment Variable)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
if not GOOGLE_CLIENT_ID:
     app.logger.error("GOOGLE_CLIENT_ID environment variable not set.")
     # Potentially raise error

# Cloudinary API Secret (from file mounted by Cloud Run secret config)
CLOUDINARY_SECRET_FILE_PATH = '/secrets/cloudinary-secret'
cloudinary_api_secret = None
try:
    with open(CLOUDINARY_SECRET_FILE_PATH, 'r') as f:
        cloudinary_api_secret = f.read().strip()
    app.logger.info(f"Successfully read Cloudinary secret from {CLOUDINARY_SECRET_FILE_PATH}")
except FileNotFoundError:
    app.logger.error(f"Cloudinary secret file not found at {CLOUDINARY_SECRET_FILE_PATH}. Check Cloud Run secret volume mount configuration.")
    # Handle error - raise exception? The app likely cannot function without it.
except IOError as e:
     app.logger.error(f"Error reading Cloudinary secret file at {CLOUDINARY_SECRET_FILE_PATH}: {e}")
     # Handle error

# Cloudinary Cloud Name & API Key (from Environment Variables)
cloudinary_cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
cloudinary_api_key = os.environ.get('CLOUDINARY_API_KEY')
if not cloudinary_cloud_name or not cloudinary_api_key:
    app.logger.error("CLOUDINARY_CLOUD_NAME or CLOUDINARY_API_KEY environment variables not set.")
    # Handle error

# --- Initialize Services ---

# Cloudinary Configuration (using variables read above)
if cloudinary_cloud_name and cloudinary_api_key and cloudinary_api_secret:
    try:
        cloudinary.config(
            cloud_name = cloudinary_cloud_name,
            api_key = cloudinary_api_key,
            api_secret = cloudinary_api_secret, # Use value read from file
            secure = True # Use HTTPS URLs
        )
        app.logger.info("Cloudinary configured successfully.")
    except Exception as e:
        app.logger.error(f"Error configuring Cloudinary: {e}")
else:
     app.logger.error("Cloudinary configuration skipped due to missing variables/secrets.")


# Google Cloud Datastore Client
try:
    datastore_client = datastore.Client()
    app.logger.info("Datastore client initialized.")
except Exception as e:
    app.logger.error(f"Failed to initialize Datastore client: {e}")
    # The app might not work without datastore, consider raising an exception


ASSET_KIND = "CloudinaryAsset" # Datastore Kind for storing asset references
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm', 'mkv'} # Adjust as needed
print("--- Global constants defined ---", file=sys.stderr)

# --- HELPER FUNCTION DEFINITIONS ---
print("--- Defining Helper Functions ---", file=sys.stderr)

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

    # --- ADD LOGGING HERE ---
    client_id_from_env = os.environ.get('GOOGLE_CLIENT_ID')
    app.logger.info(f"Value of GOOGLE_CLIENT_ID from env in before_request: '{client_id_from_env}'")
    if not client_id_from_env:
         app.logger.warning("GOOGLE_CLIENT_ID env var is empty or None in before_request!")
    
    # --- END LOGGING ---

    # Make Google Client ID available to base template
    g.google_client_id = client_id_from_env # Use the variable we just logged

    # Make Google Client ID available to base template
    # previous --> $ g.google_client_id = GOOGLE_CLIENT_ID


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
    app.logger.info(f"Serving index page for user: {user_email}") # Add log
    # --- TEMPORARILY COMMENT OUT ASSET LOADING ---
    assets = []
    # assets = list_user_assets(user_email)
    # --- END OF TEMPORARY CHANGE ---
    app.logger.info(f"Rendering index template (assets bypassed)") # Add log
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


print("Functions and routes defined.", file=sys.stderr) # Added print

# --- Local Development Server ---
# This block remains unchanged - it's only for local execution.
# The changes above affect how the app gets configured when run via Gunicorn in Cloud Run.
if __name__ == '__main__':
    # Load environment variables from .env file for local development (optional)
    # NOTE: For local testing of the *new* secret reading logic, you might need to
    # manually create a /secrets directory and a cloudinary-secret file,
    # or adjust the local fallback logic. Alternatively, set CLOUDINARY_API_SECRET
    # in your .env file and keep the original os.environ.get() logic inside the
    # if __name__ == '__main__': block specifically for local testing,
    # while the top-level code uses the file reading method.
    try:
        from dotenv import load_dotenv
        load_dotenv()
        # Reload config vars potentially overridden by .env
        # Check if running locally and need to re-read from env vars if file not found
        local_secret = os.environ.get('CLOUDINARY_API_SECRET') # Read from .env for local fallback

        app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key-change-me')
        GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')

        # Re-configure Cloudinary *for local dev* using .env vars
        # Only if the file method failed earlier and local secret exists
        if not cloudinary_api_secret and local_secret:
             app.logger.warning("Using Cloudinary secret from .env for local development.")
             cloudinary.config(
                 cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
                 api_key = os.environ.get('CLOUDINARY_API_KEY'),
                 api_secret = local_secret, # Use .env value locally
                 secure = True
             )
        print("Loaded environment variables from .env for local dev")
    except ImportError:
        print("dotenv not installed, skipping .env file load.")
    except Exception as e:
        print(f"Error processing .env or local config: {e}")

    # Check essential config for local run
    if not GOOGLE_CLIENT_ID or not os.environ.get('CLOUDINARY_CLOUD_NAME'):
         print("\n*** WARNING: Essential configuration (GOOGLE_CLIENT_ID, CLOUDINARY_*) not found for local testing. Set them in environment or .env file. ***\n")

    # Run the app locally
    app.run(host='127.0.0.1', port=8080, debug=True)

    print("main.py loaded successfully.", file=sys.stderr) # Final confirmation

    # Note: The above print statement will show in the console when running locally.
    # In production, the logger will handle output to stderr as configured in the app.