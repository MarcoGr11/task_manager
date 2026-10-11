"""Gitleaks demo: credentials come from the environment, never from source code."""
import os

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
