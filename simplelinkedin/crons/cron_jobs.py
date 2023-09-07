import subprocess  # nosec
from pathlib import Path

from crontab import CronTab

from simplelinkedin.linkedin import LinkedIn


class LinkedInCron(LinkedIn):
    CRON_JOB_COMMENT = "LinkedInJob"

    @classmethod
    def set_smart_cron(cls, cron_env_file, cron_user: str, hour_of_day: int):
        python_path = [
            path.strip()
            for path in subprocess.run("which python", shell=True, capture_output=True)  # nosec
            .stdout.decode()
            .split("\n")
        ][0]

        main_file_path = Path(__file__).absolute().parent.parent

        env_file = Path(cron_env_file).absolute()

        command = f"{python_path or 'python'} {main_file_path} --env {env_file}"

        cron = CronTab(user=cron_user)

        even_day_job = cron.new(command=command, comment=cls.CRON_JOB_COMMENT)
        even_day_job.hour.on(hour_of_day)
        even_day_job.dow.on(0, 1, 2, 3, 4, 5, 6)

        cron.write()

    @classmethod
    def remove_cron_jobs(cls, cron_user: str):
        """Remove cron jobs set by the module earlier with the comment specified by CRON_JOB_COMMENT var"""

        cron = CronTab(user=cron_user)
        cron.remove_all(comment=cls.CRON_JOB_COMMENT)
        cron.write()
