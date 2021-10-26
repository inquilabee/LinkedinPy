# LinkedIn

Python script to automate some usual tasks performed on social-networking site LinkedIn. The script has been tested on
macOS and is expected to work on Linux environment as well. Raise an issue/PR if you encounter any issue while running
the scripts.

Before you proceed:

- Download appropriate chrome driver from https://chromedriver.chromium.org/downloads for the version of the Chrome you
  have installed in your machine.
- Allow the script to execute the chrome-driver file downloaded above

The best way to run and test the package for your needs is to use `sample_script.py` like below:

```python
from simplelinkedin import LinkedIn

settings = {
  "LINKEDIN_USER": "<username>",
  "LINKEDIN_PASSWORD": "<password>",
  "LINKEDIN_BROWSER": "Chrome",
  "LINKEDIN_BROWSER_DRIVER": "/path/to/chromedriver",
  "LINKEDIN_BROWSER_HEADLESS": 0,
  "LINKEDIN_BROWSER_CRON": 0,
  "LINKEDIN_CRON_USER": "<root_user>",
  "LINKEDIN_PREFERRED_USER": "/path/to/preferred/user/text_doc.text",
  "LINKEDIN_NOT_PREFERRED_USER": "/path/to/not/preferred/user/text_doc.text",
}

with LinkedIn(
        username=settings.get("LINKEDIN_USER"),
        password=settings.get("LINKEDIN_PASSWORD"),
        browser=settings.get("LINKEDIN_BROWSER"),
        driver_path=settings.get("LINKEDIN_BROWSER_DRIVER"),
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
  # run smart follow-unfollow method (without setting cron jobs) which essentially does the same thing as
  # all the above steps
  ln.smart_follow_unfollow(
    users_preferred=settings.get("LINKEDIN_PREFERRED_USER") or [],
    users_not_preferred=settings.get("LINKEDIN_NOT_PREFERRED_USER") or [],
  )

  # setting and un-setting cron
  # Use sudo in case you are setting/un-setting cron.

  # set cron on your machine
  ln.set_smart_cron(settings)

  # remove existing cron jobs
  ln.remove_cron_jobs(settings=settings)
```

Alternatively, you can go the command line way, like below.

    usage: linkedin.py [-h] [--env ENV] [--email EMAIL] [--password PASSWORD] [--browser BROWSER] [--driver DRIVER] [--headless] [--cron] [--cronuser CRONUSER]
                       [--preferred PREFERRED] [--notpreferred NOTPREFERRED]

    optional arguments:
      -h, --help            show this help message and exit
      --env ENV             Linkedin environment file
      --email EMAIL         Email of linkedin user
      --password PASSWORD   Password of linkedin user
      --browser BROWSER     Browser used for linkedin
      --driver DRIVER       Path to Chrome/Firefox driver
      --headless            Whether to run headless
      --cron                Whether to create a cron job
      --cronuser CRONUSER   Run cron jobs as this user
      --rmcron              Whether to remove existing cron
      --preferred PREFERRED
                            Path to file containing preferred users characteristics
      --notpreferred NOTPREFERRED
                            Path to file containing characteristics of not preferred users

Start with following commands. Use `example.env` file as reference while setting values. Prepend `sudo` if
setting/un-setting cron in the commands below.

    python linkedin.py --env .env
    python linkedin.py --email abc@gmail.com --password $3cRET --browser Chrome --driver /path/to/chromedriver --cronuser john --preferred data/users_preferred.txt --notpreferred data/users_not_preferred.txt

If the above command works, you can change `.env` file and set `LINKEDIN_BROWSER_CRON=1` or pass `--cron` in the second
command.

`example.env`

    LINKEDIN_USER=
    LINKEDIN_PASSWORD=
    LINKEDIN_BROWSER=Chrome
    LINKEDIN_BROWSER_DRIVER=
    LINKEDIN_BROWSER_HEADLESS=0
    LINKEDIN_BROWSER_CRON=0
    LINKEDIN_CRON_USER=
    LINKEDIN_PREFERRED_USER=data/users_preferred.txt
    LINKEDIN_NOT_PREFERRED_USER=data/users_not_preferred.txt

TODOS:

- improve documentation
- Include Tests
