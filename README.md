# LinkedIn

Python package to automate some usual tasks performed on social-networking site LinkedIn.

### What can you do?

The package helps to do the followings [with a number of improvements planned in future]

- Login to LinkedIn
- Send connection requests
    - Filter by minimum and maximum number of mutual connections
    - Filter by kinds of users (preferred and not preferred)
    - Maximum number of requests to be sent
    - Optionally, view the profile of those sending request to
- Accept connection requests
- Delete/Withdraw sent connection requests depending on how old they are
- Run smart follow-unfollow
    - Delete sent requests older than 14 days
    - Follow the maximum number of people possible for the day (based on LinkedIn's weekly limit)
    - Accept all pending requests
- Run all of these in the background mode without affecting your usual work

Note: The package has been tested on macOS and is expected to work on Linux/Unix environments as well. Raise an issue/PR
if you encounter any issue while running the scripts.

### Getting Started

Install file from PyPi

```bash
pip install simplelinkedin
```

The best way to run and test the package for your needs is to use `sample_script.py` like below. Start with running your
package by supplying `LINKEDIN_BROWSER_HEADLESS=0` and if everything runs well, you can set the same back
to `LINKEDIN_BROWSER_HEADLESS=1` to run your script in the background.

```python
from simplelinkedin.linkedin import LinkedIn

settings = {
    "LINKEDIN_USER": "<username>",
    "LINKEDIN_PASSWORD": "<password>",
    "LINKEDIN_BROWSER": "Chrome",
    "LINKEDIN_BROWSER_HEADLESS": 0,
    "LINKEDIN_PREFERRED_USER": "/path/to/preferred/user/text_doc.text",
    "LINKEDIN_NOT_PREFERRED_USER": "/path/to/not/preferred/user/text_doc.text",
}

with LinkedIn(
        username=settings.get("LINKEDIN_USER"),
        password=settings.get("LINKEDIN_PASSWORD"),
        browser=settings.get("LINKEDIN_BROWSER"),
        headless=bool(settings.get("LINKEDIN_BROWSER_HEADLESS")),
) as ln:
    # do all the steps manually
    ln.login()
    ln.remove_sent_invitations(older_than_days=14)

    ln.send_invitations(
        max_invitation=max(ln.WEEKLY_MAX_INVITATION - ln.invitations_sent_last_week, 0),
        min_mutual=10,
        max_mutual=450,
        preferred_users=["Quant"],  # file_path or list of features
        not_preferred_users=["Sportsman"],  # file_path or list of features
        view_profile=True,  # (recommended) view profile of users you sent connection request to
    )

    ln.accept_invitations()

    # OR
    # run smart follow-unfollow method which essentially does the same thing as
    # all the above steps
    ln.smart_follow_unfollow(
        users_preferred=settings.get("LINKEDIN_PREFERRED_USER") or [],
        users_not_preferred=settings.get("LINKEDIN_NOT_PREFERRED_USER") or [],
    )
```

Alternatively, you can go the command line way, like below.

    > python -m simplelinkedin -h

    usage: simplelinkedin [-h] [--env ENV] [--email EMAIL] [--password PASSWORD]
                          [--browser BROWSER] [--headless] [--preferred PREFERRED]
                          [--notpreferred NOTPREFERRED]

    options:
      -h, --help            show this help message and exit
      --env ENV             Linkedin environment file
      --email EMAIL         Email of linkedin user
      --password PASSWORD   Password of linkedin user
      --browser BROWSER     Browser used for linkedin
      --headless            Whether to run headless
      --preferred PREFERRED
                            Path to file containing preferred users
                            characteristics
      --notpreferred NOTPREFERRED
                            Path to file containing characteristics of not
                            preferred users

Start with the following commands.
Use `example.env` file as reference while setting `.env` values.

    python linkedin.py --env .env
    python linkedin.py --email abc@gmail.com --password $3cRET --browser Chrome --preferred data/users_preferred.txt --notpreferred data/users_not_preferred.txt


`example.env`

    LINKEDIN_USER=
    LINKEDIN_PASSWORD=
    LINKEDIN_BROWSER=Chrome
    LINKEDIN_BROWSER_HEADLESS=1
    LINKEDIN_PREFERRED_USER=data/users_preferred.txt
    LINKEDIN_NOT_PREFERRED_USER=data/users_not_preferred.txt


### Extras

This package makes use of another package named [simpleselenium](https://github.com/inquilabee/simpleselenium). Do check that out.

### TODOS

- improve documentation
- Include Tests
