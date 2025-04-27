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


# --- The rest of your helper functions and routes remain the same ---
# ... (keep all functions from allowed_file down to the end of the file) ...


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