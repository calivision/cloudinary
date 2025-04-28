# Contributing to Cloud Vision Manager 🎉

First off, thank you for considering contributing! 🙌 We're thrilled you're interested in helping make Cloud Vision Manager even better. Whether you're fixing a bug, proposing a new feature, or improving documentation, your help is valued.

This project aims to provide a simple, deployable service for managing Cloudinary assets with Google authentication. We welcome contributions of all kinds!

## Table of Contents

*   [Ways to Contribute](#ways-to-contribute)
*   [Reporting Bugs 🐛](#reporting-bugs-)
*   [Suggesting Enhancements 💡](#suggesting-enhancements-)
*   [Your First Code Contribution 💻](#your-first-code-contribution-)
*   [Development Setup 🔧](#development-setup-)
*   [Pull Request Process 🙏](#pull-request-process-)
*   [Coding Style Guide 🎨](#coding-style-guide-)
*   [Code of Conduct ❤️](#code-of-conduct-%EF%B8%8F)
*   [Questions? ❓](#questions-)

## Ways to Contribute

You can contribute in several ways:

*   **Reporting Bugs:** If you find something not working as expected.
*   **Suggesting Enhancements:** Proposing new features or improvements to existing ones.
*   **Code Contributions:** Fixing bugs or implementing new features via Pull Requests.
*   **Documentation:** Improving the README, deployment guides, or inline code comments.
*   **Feedback:** Providing feedback on existing features or the project direction.

## Reporting Bugs 🐛

Bugs are tracked as [GitHub Issues](link-to-your-issues-page). Before submitting a bug report, please:

1.  **Check Existing Issues:** See if the bug has already been reported.
2.  **Provide Details:** If it's a new bug, please provide as much detail as possible:
    *   A clear and descriptive title.
    *   Steps to reproduce the behavior.
    *   What you expected to happen.
    *   What actually happened (include screenshots or error messages if possible).
    *   Your environment (Browser version, OS, Cloud Run revision if applicable).

➡️ [**Submit a Bug Report**](link-to-your-new-issue-page-with-bug-template-if-any)

## Suggesting Enhancements 💡

Have an idea for a new feature or an improvement? We'd love to hear it! Please submit enhancements as [GitHub Issues](link-to-your-issues-page).

1.  **Check Existing Issues/Requests:** See if your idea has already been discussed.
2.  **Be Specific:** Provide a clear description of the enhancement and the motivation behind it (the "why").
3.  **Explain the Use Case:** How would this feature help users?

➡️ [**Suggest an Enhancement**](link-to-your-new-issue-page-with-feature-template-if-any)

## Your First Code Contribution 💻

Unsure where to start? Look for issues tagged `good first issue` or `help wanted`. These are usually smaller, well-defined tasks perfect for getting started. Don't hesitate to ask questions on the issue thread if you need clarification!

## Development Setup 🔧

Ready to dive into the code? Here’s how to set up your development environment:

1.  **Prerequisites:**
    *   Python 3.9+
    *   Git
    *   Docker (Recommended)
    *   `gcloud` CLI (Optional, for testing deployment)
    *   A Google Cloud Project (for testing Datastore/Secrets/Cloud Run)
    *   A Cloudinary Account
2.  **Fork the Repository:** Click the "Fork" button on GitHub.
3.  **Clone Your Fork:** `git clone https://github.com/YOUR_USERNAME/cloud-vision-manager.git`
4.  **Navigate to Directory:** `cd cloud-vision-manager`
5.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
6.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
7.  **Local Configuration (`.env`):** Create a `.env` file in the root directory (this is ignored by git). Add the necessary environment variables for local testing (see `main.py` configuration section). You'll need at least:
    ```dotenv
    FLASK_SECRET_KEY='a_strong_random_key_for_local_dev'
    GOOGLE_CLIENT_ID='YOUR_LOCAL_TEST_GOOGLE_OAUTH_CLIENT_ID.apps.googleusercontent.com'
    CLOUDINARY_CLOUD_NAME='YOUR_CLOUDINARY_CLOUD_NAME'
    CLOUDINARY_API_KEY='YOUR_CLOUDINARY_API_KEY'
    CLOUDINARY_API_SECRET='YOUR_CLOUDINARY_API_SECRET'
    # Optional: For local Datastore emulator
    # DATASTORE_EMULATOR_HOST=localhost:8081
    # DATASTORE_PROJECT_ID=your-local-project-id
    ```
    *Remember to configure Authorized JavaScript Origins for `http://localhost:8080` or `http://127.0.0.1:8080` in your Google OAuth Client ID settings for local testing.*
8.  **Run Locally:**
    ```bash
    python main.py
    ```
    Access the app at `http://127.0.0.1:8080`.

## Pull Request Process 🙏

1.  **Ensure Setup:** Make sure your development environment is set up correctly.
2.  **Create a Branch:** Create a new branch off `main` for your changes: `git checkout -b feature/your-feature-name` or `bugfix/issue-number`.
3.  **Make Your Changes:** Write your code and add tests if applicable.
4.  **Test Locally:** Ensure your changes work and don't break existing functionality. Run any linters or formatters (see Coding Style).
5.  **Commit Changes:** Use clear and descriptive commit messages. Reference the issue number if fixing a specific issue (e.g., `git commit -m "Fix #123: Handle missing asset format"`).
6.  **Push to Your Fork:** `git push origin feature/your-feature-name`.
7.  **Open a Pull Request (PR):** Go to the original repository on GitHub and open a PR from your fork's branch to the main repository's `main` branch.
8.  **Describe Your PR:** Fill out the PR template, explaining the changes, linking the relevant issue, and providing any necessary context for the reviewer.
9.  **Review:** A maintainer will review your PR. Be prepared to discuss your changes and make adjustments based on feedback.
10. **Merge:** Once approved, your PR will be merged! 🎉

## Coding Style Guide 🎨

*   **Python:** Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/). We recommend using formatters like [Black](https://github.com/psf/black) and linters like [Flake8](https://flake8.pycqa.org/en/latest/).
*   **HTML/CSS/JS:** Maintain readability and consistency. Use standard formatting.
*   **Comments:** Add comments to explain complex logic or non-obvious code sections.

## Code of Conduct ❤️

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. Please read the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) file. We expect all contributors to interact respectfully and constructively.

## Questions? ❓

If you have questions about contributing, feel free to open an issue and tag it with `question`.

Thank you again for your interest in contributing! We look forward to your ideas and contributions. ✨