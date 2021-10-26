# LinkedIn

Python script to automate some usual tasks performed on social-networking site LinkedIn.

The script has been tested on macOS and is expected to work on Linux environment as well. Raise an issue/PR if you
encounter any issue while running the scripts.

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

Start with following commands. Use `example.env` file as reference while setting values. Use sudo in case you are
setting crons.

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
