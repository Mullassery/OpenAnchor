"""Post-install messaging for OpenAnchor"""

def post_install():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ OpenAnchor installed successfully!

📌 WHAT IS THIS?
   Token intelligence + 6D attribution

🚀 GET STARTED:
   $ python3 -c "from openanchor import *; print('OpenAnchor ready')"
   $ python3 -c "import openanchor; print(f'v{openanchor.__version__ if hasattr(openanchor, \"__version__\") else \"latest\"}')"

📖 DOCUMENTATION:
   Repo:     https://github.com/Mullassery/OpenAnchor
   Tutorials: https://github.com/Mullassery/OpenAnchor#readme
   Issues:    https://github.com/Mullassery/OpenAnchor/issues

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)

if __name__ == "__main__":
    post_install()
