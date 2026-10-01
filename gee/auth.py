"""Google Earth Engine authentication and initialization utility.

Reads project ID from GEE_PROJECT environment variable or config.yaml.
Handles initialization with clear error messaging when credentials are
missing or unauthenticated.
"""

import os
import sys
import logging
from typing import Optional, Tuple
import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def load_config_project(config_path: str = "config.yaml") -> str:
    """Read the Earth Engine project ID from config.yaml or environment."""
    env_project = os.environ.get("GEE_PROJECT")
    if env_project:
        return env_project.strip()

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                return str(cfg.get("gee_project", "YOUR_PROJECT_ID")).strip()
        except Exception as e:
            logger.warning("Could not read %s: %s", config_path, e)

    return "YOUR_PROJECT_ID"


def initialize_earth_engine(config_path: str = "config.yaml") -> Tuple[bool, str]:
    """Initialize Google Earth Engine using the project configured in config.yaml or env.

    Returns:
        (success: bool, message: str)
    """
    project_id = load_config_project(config_path)

    try:
        import ee
    except ImportError:
        msg = "The 'earthengine-api' package is not installed. Please run: pip install earthengine-api"
        logger.error(msg)
        return False, msg

    if not project_id or project_id == "YOUR_PROJECT_ID":
        msg = (
            "Earth Engine project ID is not configured (currently 'YOUR_PROJECT_ID').\n"
            "Please update 'gee_project' in config.yaml or export GEE_PROJECT in your environment.\n"
            "If you haven't authenticated yet, run: earthengine authenticate"
        )
        return False, msg

    try:
        ee.Initialize(project=project_id)
        msg = f"Earth Engine successfully initialized with project: {project_id}"
        logger.info(msg)
        return True, msg
    except Exception as e:
        msg = (
            f"Failed to initialize Earth Engine with project '{project_id}':\n"
            f"Error: {e}\n\n"
            "Remediation steps:\n"
            "1. Run 'earthengine authenticate' in your terminal.\n"
            "2. Verify the project ID is valid and has Earth Engine API enabled in Google Cloud Console.\n"
            "3. Ensure your Google account has permissions on this project."
        )
        logger.error(msg)
        return False, msg


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success, msg = initialize_earth_engine()
    print(msg)
    sys.exit(0 if success else 1)
