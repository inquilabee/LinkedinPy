# LinkedIn

Python ❤️ LinkedIn

Use Python to automate usual tasks on LinkedIn.

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
    last_week_invitations = ln.count_invitations_sent_last_week()

    ln.send_invitations(
        max_invitations=max(ln.WEEKLY_MAX_INVITATION - last_week_invitations , 0),
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
        min_mutual= 0,
        max_mutual = 500,
        withdraw_invite_older_than_days = 14,
        max_invitations_to_send= 0,
        users_preferred=settings.get("LINKEDIN_PREFERRED_USER") or [],
        users_not_preferred=settings.get("LINKEDIN_NOT_PREFERRED_USER") or [],
    )
```


### Command line usage

You can go the command line way, like below.

    > python -m simplelinkedin -h

    usage: simplelinkedin [-h] [--env ENV] [--email EMAIL] [--password PASSWORD]
                          [--browser BROWSER] [--headless] [--maxinvite MAXINVITE]
                          [--minmutual MINMUTUAL] [--maxmutual MAXMUTUAL]
                          [--withdrawdays WITHDRAWDAYS] [--preferred PREFERRED]
                          [--notpreferred NOTPREFERRED] [--cronfile CRONFILE]
                          [--cronuser CRONUSER] [--rmcron | --no-rmcron]
                          [--cronhour CRONHOUR]

    options:
      -h, --help            show this help message and exit
      --env ENV             Linkedin environment file
      --email EMAIL         Email of LinkedIn user
      --password PASSWORD   Password of LinkedIn user
      --browser BROWSER     Browser used for LinkedIn
      --headless            Whether to run headless (i.e. without the browser
                            visible in the front.)
      --maxinvite MAXINVITE
                            Maximum number of invitations to send
      --minmutual MINMUTUAL
                            Minimum number of mutual connections required.
      --maxmutual MAXMUTUAL
                            Maximum number of mutual connections required.
      --withdrawdays WITHDRAWDAYS
                            Withdraw invites older than this many days
      --preferred PREFERRED
                            Path to file containing preferred users
                            characteristics
      --notpreferred NOTPREFERRED
                            Path to file containing characteristics of not
                            preferred users
      --cronfile CRONFILE   Path to cronfile
      --cronuser CRONUSER   Name of user setting cron on the machine (needed by
                            most OS)
      --rmcron, --no-rmcron
                            Whether to remove existing crons.
      --cronhour CRONHOUR   hour of the day you want to set cron for each day.


Start with the following commands. (Use `example.env` file as reference while setting `.env` values)

    python -m simplelinkedin --env .env
    python -m simplelinkedin --email abc@gmail.com --password $3cRET --browser Chrome --preferred data/users_preferred.txt --notpreferred data/users_not_preferred.txt


### Settings crons

    python -m simplelinkedin --cronfile .cron.env --cronuser osuser --cronhour 23

Supply `--rmcron` to remove existing cron

    python -m simplelinkedin --rmcron --cronuser osuser
    python -m simplelinkedin --cronfile .cron.env --cronuser osuser --cronhour 23 --rmcron

### Example `example.env`

    LINKEDIN_USER=
    LINKEDIN_PASSWORD=
    LINKEDIN_BROWSER=Chrome
    LINKEDIN_BROWSER_HEADLESS=1
    LINKEDIN_PREFERRED_USER=data/users_preferred.txt
    LINKEDIN_NOT_PREFERRED_USER=data/users_not_preferred.txt
    LINKEDIN_MIN_MUTUAL=0
    LINKEDIN_MAX_MUTUAL=500
    LINKEDIN_MAX_INVITE=0
    LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS=14

### Extras

This package makes heavy use of another package named [simpleselenium](https://github.com/inquilabee/simpleselenium). Do check that out.

### TODOS

- improve documentation
- Include Tests
