# AutoLinkedIn

Elevate your LinkedIn game with **AutoLinkedIn**, a Python package designed for automating routine LinkedIn tasks. Whether you want to connect with specific users, manage connection requests, or optimize your LinkedIn networking, this package has you covered.

### Key Features

- **Login to LinkedIn**: Seamlessly access your LinkedIn account.
- **Send Connection Requests**: Customize your connection requests by filtering users based on mutual connections, user types, and more.
- **Accept Connection Requests**: Simplify the process of accepting incoming connection requests.
- **Delete/Withdraw Sent Requests**: Keep your connection list clean by removing outdated sent requests.
- **Smart Follow-Unfollow**: Automatically manage connections, delete aged requests, and maximize your daily interactions within LinkedIn's limits.
- **Background Mode**: Run all tasks in the background mode without interfering with your regular work.
- **Search**: Search for people.


### Getting Started

To get started with **AutoLinkedIn**, first, install the package from PyPi using the following command:

```bash
pip install autolinkedin
```

Next, you can run and test the package by creating a script similar to `autolinkedin/scripts/sample_script.py`. Start by running your script with `headless=False` to ensure everything works as expected. Once you're confident, switch to `headless=True` to run your script in the background.

Here's a simplified example of running **AutoLinkedIn**:

```python
from autolinkedin.linkedin import LinkedIn


with LinkedIn(
        username="<username/email>",
        password="<pas$word>",
        browser="<Chrome/Firefox>",
        headless="<True/False>",
) as ln:
    # Perform LinkedIn actions here
    ln.withdraw_sent_invitations(older_than_days=14)
    last_week_invitations = ln.count_invitations_sent_last_week()

    ln.send_invitations(
        max_invitations=max(ln.WEEKLY_MAX_INVITATION - last_week_invitations, 0),
        min_mutual=10,
        max_mutual=450,
        preferred_users=["Quant", "Software"],  # file_path or list of features
        not_preferred_users=["Sportsman", "Doctor"],  # file_path or list of features
        view_profile=True,  # (recommended) view profile of users you sent connection requests to
    )

    ln.accept_invitations()

    # Customize your actions as needed
    # ...

    # Alternatively, use the smart follow-unfollow method for a streamlined approach
    ln.smart_follow_unfollow(
        min_mutual=0,
        max_mutual=500,
        withdraw_invite_older_than_days=14,
        max_invitations_to_send=0,
        users_preferred=["Quant"],  # file_path or list of features
        users_not_preferred=["Sportsman"],  # file_path or list of features
        remove_recommendations=True, # remove recommendations which do not match criteria
    )

    # Additional method
    ln.remove_recommendations(min_mutual=10, max_mutual=500)

    # Search for people
    ln.search_people("Microsoft Recruiter")
```

### Command Line Usage

**AutoLinkedIn** provides a convenient command-line interface for easy interaction. You can execute tasks directly from the command line with options like:

```bash
python -m autolinkedin -h
```

This command will display a list of available options, allowing you to configure and execute LinkedIn tasks without writing scripts.

```bash
> python -m autolinkedin -h
usage: autolinkedin [-h] [--env ENV] [--email EMAIL] [--password PASSWORD] [--browser BROWSER] [--headless] [--maxinvite MAXINVITE] [--minmutual MINMUTUAL] [--maxmutual MAXMUTUAL] [--withdrawdays WITHDRAWDAYS]
                   [--preferred PREFERRED] [--notpreferred NOTPREFERRED] [--cronfile CRONFILE] [--cronuser CRONUSER] [--rmcron | --no-rmcron] [--cronhour CRONHOUR]

options:
  -h, --help            show this help message and exit
  --env ENV             Linkedin environment file
  --email EMAIL         Email of LinkedIn user
  --password PASSWORD   Password of LinkedIn user
  --browser BROWSER     Browser used for LinkedIn
  --headless            Whether to run headless (i.e. without the browser visible in the front.)
  --maxinvite MAXINVITE
                        Maximum number of invitations to send
  --minmutual MINMUTUAL
                        Minimum number of mutual connections required.
  --maxmutual MAXMUTUAL
                        Maximum number of mutual connections required.
  --withdrawdays WITHDRAWDAYS
                        Withdraw invites older than this many days
  --preferred PREFERRED
                        Path to file containing preferred users characteristics
  --notpreferred NOTPREFERRED
                        Path to file containing characteristics of not preferred users
  --cronfile CRONFILE   Path to cronfile
  --cronuser CRONUSER   Name of user setting cron on the machine (needed by most OS)
  --rmcron, --no-rmcron
                        Whether to remove existing crons.
  --cronhour CRONHOUR   hour of the day you want to set cron for each day.
```

### Setting Up Cron Jobs

To schedule recurring tasks, you can set up cron jobs using **AutoLinkedIn**. Here's how:

1. Start with the following commands. (Use `example.env` as a reference while setting `.env` values)

```bash
python -m autolinkedin --env .env
```

2. You can supply `--rmcron` to remove existing cron jobs:

```bash
python -m autolinkedin --rmcron --cronuser osuser
```

3. To create a new cron job, specify the desired settings:

```bash
python -m autolinkedin --cronfile .cron.env --cronuser osuser --cronhour 23
```

These cron jobs enable you to automate your LinkedIn tasks at specific times, enhancing your networking efficiency.

### Extras

**AutoLinkedIn** heavily relies on another package I authored named [SeleniumTabs](https://github.com/inquilabee/selenium-tabs). Feel free to explore that package for additional functionality.

### example.env

```bash
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
```

### TODOs

- Enhance documentation
- Include comprehensive tests
