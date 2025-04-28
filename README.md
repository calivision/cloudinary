# ☁️✨ Cloud Vision Manager ✨☁️

**(Powered by Cloudinary & Google Cloud Run)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Contribution Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)

Tired of juggling media files across different platforms? Need a simple, authenticated way to upload photos and videos straight to the cloud with cool transformations on the fly?

**Meet the Cloud Vision Manager!** 🎉

This nifty Python application, designed to run smoothly on Google Cloud Run, provides a lightweight file manager interface powered by the magic of Cloudinary. Log in securely with your Google Account and start managing your media assets with ease!

---

## 🚀 What it Does

*   **Secure Google Sign-In:** Access the manager only after authenticating with your Google Account. No complex user management needed!
*   **Cloudinary Uploads:** Directly upload images and videos to your Cloudinary account.
*   **On-the-Fly Transformations:** Apply basic Cloudinary transformations (resize, crop, effects) right when you upload.
*   **Lightweight File Management:** View your uploaded Cloudinary assets directly within the app.
*   **Easy Viewing & Deletion:** Access original files, see generated thumbnails, view applied transformations, and delete assets you no longer need.
*   **Cloud Run Ready:** Built with a Dockerfile specifically for easy deployment on Google Cloud Run.
*   **Datastore Metadata:** Keeps track of your uploads and associates them with your user account using Google Cloud Datastore.

---

## ✨ Key Features

*   **Simple Web UI:** Built with Flask for a clean and straightforward user experience.
*   **Google Identity Services:** Uses the modern GIS library for secure authentication.
*   **Direct Cloudinary Interaction:** Leverages the official Cloudinary Python library.
*   **Serverless Friendly:** Designed for the scale-to-zero, stateless nature of Cloud Run.
*   **Configurable:** Uses environment variables and Google Secret Manager for secure configuration.

---

## 🏁 Getting Started (Deploying on Cloud Run)

Ready to launch your own Cloud Vision Manager? Here's the high-level view:

**Prerequisites:**

1.  **Google Cloud Project:** You'll need a GCP project with billing enabled.
2.  **APIs Enabled:** Ensure Cloud Run API, Cloud Build API, Artifact Registry API, Datastore API, Secret Manager API, and IAM API are enabled.
3.  **Cloudinary Account:** Sign up at [Cloudinary.com](https://cloudinary.com/) and note your Cloud Name, API Key, and API Secret.
4.  **Google OAuth 2.0 Client ID:** Create credentials in GCP (APIs & Services -> Credentials) for a "Web application".
5.  **Secrets:** Store your Cloudinary API Secret and a strong Flask Secret Key in Google Secret Manager.
6.  `gcloud` CLI installed and configured.
7.  Git and Docker installed locally (for building).

**Quick Deployment Steps:**

1.  **Clone the Repository:** `git clone https://github.com/calivision/cloudinary.git`
2.  **Create Datastore Index:** Create the required composite index for `CloudinaryAsset` (see `index.yaml` or documentation). Deploy it: `gcloud datastore indexes create index.yaml --project=YOUR_PROJECT_ID` and wait for it to become "Serving".
3.  **Configure Secrets:** Create `CLOUDINARY_API_SECRET` and `flask-secret-key` in Secret Manager.
4.  **Build the Container:** `gcloud builds submit --tag REGION-docker.pkg.dev/YOUR_PROJECT_ID/YOUR_REPO/cloudinary-manager --project=YOUR_PROJECT_ID`
5.  **Deploy to Cloud Run:** Use the `gcloud run deploy` command, setting environment variables (`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `GOOGLE_CLIENT_ID`) and configuring secret access (`--set-secrets=...`). Assign a Service Account with `Datastore User` and `Secret Manager Secret Accessor` roles.
    ```bash
    # Example (replace placeholders and add other flags)
    gcloud run deploy YOUR_SERVICE_NAME \
        --image REGION-docker.pkg.dev/YOUR_PROJECT_ID/YOUR_REPO/cloudinary-manager:latest \
        --set-env-vars="GOOGLE_CLIENT_ID=YOUR_CLIENT_ID..." \
        --set-secrets="FLASK_SECRET_KEY=flask-secret-key:latest" \
        # ... other vars and secrets ...
        --service-account=YOUR_RUNTIME_SA@... \
        --allow-unauthenticated \
        --project=YOUR_PROJECT_ID --region=YOUR_REGION
    ```
6.  **Configure OAuth Origins:** Add the deployed Cloud Run Service URL to the "Authorized JavaScript origins" in your Google OAuth Client ID settings.
7.  **(If Needed) Configure Public Access/IAP:** If blocked by Org Policies, configure IAP or adjust policies to allow access.

➡️ **For detailed, step-by-step instructions, please see our full [Deployment Guide](link-to-your-docs-later.md)!**

---

## 🔮 Future Vision

We're just getting started! We envision Cloud Vision Manager becoming even more useful with:

*   📱 **Native Mobile Apps (Android & iOS):** Securely manage credentials and access the uploader on the go!
*   🖼️ **More Advanced Transformations:** Integrate more of Cloudinary's powerful features.
*   📂 **Folder Management:** Basic folder creation/navigation within the UI.
*   🏷️ **Tagging & Metadata Editing:** Manage tags and metadata directly.

---

## 🤝 Contributing

Want to help bring this vision to life? Contributions are welcome! Whether it's fixing bugs, improving the UI, adding features, or tackling the mobile apps, we'd love your input.

*   Check out the [Contribution Guidelines](CONTRIBUTING.md).
*   Browse the [Open Issues](link-to-your-issues).
*   Feel free to suggest new ideas!

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Let's manage media simply and securely in the cloud! 🚀