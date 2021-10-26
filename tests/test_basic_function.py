import os

import pytest

from scripts.sample_script import run_script


def test_run_without_exception():
    """Not a good test at all. :("""
    try:
        settings = {
            "LINKEDIN_USER": os.getenv("LINKEDIN_USER"),
            "LINKEDIN_PASSWORD": os.getenv("LINKEDIN_PASSWORD"),
            "LINKEDIN_BROWSER": "Chrome",
            "LINKEDIN_BROWSER_DRIVER": "/Users/dayhatt/workspace/drivers/chromedriver",
            "LINKEDIN_BROWSER_HEADLESS": 0,
            "LINKEDIN_BROWSER_CRON": 0,
            "LINKEDIN_CRON_USER": "dayhatt",
            "LINKEDIN_PREFERRED_USER": "./data/user_preferred.txt",
            "LINKEDIN_NOT_PREFERRED_USER": "./data/user_not_preferred.txt",
        }
        run_script(settings=settings)
    except Exception as e:  # noqa
        pytest.fail("Test failed: Scripts failed to run.")
