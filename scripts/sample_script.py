from linkedin import LinkedIn

settings = {
    "LINKEDIN_USER": "",
    "LINKEDIN_PASSWORD": "",
    "LINKEDIN_BROWSER": "Chrome",
    "LINKEDIN_BROWSER_DRIVER": "/Users/dayhatt/workspace/drivers/chromedriver",
    "LINKEDIN_BROWSER_HEADLESS": 0,
    "LINKEDIN_BROWSER_CRON": 0,
    "LINKEDIN_CRON_USER": "dayhatt",
    "LINKEDIN_PREFERRED_USER": "./data/user_preferred.txt",
    "LINKEDIN_NOT_PREFERRED_USER": "./data/user_not_preferred.txt",
}

with LinkedIn(
    username=settings.get("LINKEDIN_USER"),
    password=settings.get("LINKEDIN_PASSWORD"),
    browser=settings.get("LINKEDIN_BROWSER"),
    driver_path=settings.get("LINKEDIN_BROWSER_DRIVER"),
    headless=bool(settings.get("LINKEDIN_BROWSER_HEADLESS")),
) as ln:
    # all the steps manually
    ln.login()
    # ln.remove_sent_invitations(older_than_days=14)

    ln.send_invitations(
        max_invitation=max(ln.WEEKLY_MAX_INVITATION - ln.invitations_sent_last_week, 0),
        min_mutual=10,
        max_mutual=450,
        preferred_users=["Quant"],
        not_preferred_users=["Sportsman"],
        view_profile=True,
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
    # set cron
    ln.set_smart_cron(settings)

    # remove existing cron jobs
    ln.remove_cron_jobs(settings=settings)
