from simplelinkedin.linkedin import LinkedIn

settings = {
    "LINKEDIN_USER": "",
    "LINKEDIN_PASSWORD": "",
    "LINKEDIN_BROWSER": "Chrome",
    "LINKEDIN_BROWSER_HEADLESS": 0,
    "LINKEDIN_PREFERRED_USER": "data/user_not_preferred.txt",
    "LINKEDIN_NOT_PREFERRED_USER": "data/user_preferred.txt",
}

with LinkedIn(
    username=settings.get("LINKEDIN_USER"),
    password=settings.get("LINKEDIN_PASSWORD"),
    browser=settings.get("LINKEDIN_BROWSER"),
    headless=bool(settings.get("LINKEDIN_BROWSER_HEADLESS")),
) as ln:
    ln.login()

    ln.remove_recommendations(min_mutual=0, max_mutual=50)

    max_invitations = ln.WEEKLY_MAX_INVITATION - ln.count_invitations_sent_last_week()

    print(max_invitations)

    ln.withdraw_sent_invitations(max_remove=2, older_than_days=14)

    ln.send_invitations(
        max_invitations=2,
        min_mutual=100,
        max_mutual=550,
        preferred_users="./data/user_preferred.txt",
        not_preferred_users="./data/user_not_preferred.txt",
        view_profile=True,
    )

    ln.accept_invitations()
