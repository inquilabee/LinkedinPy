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

    print(ln.invitations_sent_last_week())

    ln.remove_sent_invitations(older_than_days=14)

    ln.send_invitations(
        max_invitation=max(ln.WEEKLY_MAX_INVITATION - ln.invitations_sent_last_week(), 0),
        min_mutual=10,
        max_mutual=450,
        preferred_users="./scripts/data/user_preferred.txt",
        not_preferred_users="./scripts/data/user_not_preferred.txt",
        view_profile=True,
    )

    ln.accept_invitations()
