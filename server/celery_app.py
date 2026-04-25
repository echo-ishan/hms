from __future__ import annotations

from celery import Celery
from celery.schedules import crontab
from flask import Flask


def create_celery(app: Flask) -> Celery:
    celery = Celery(app.import_name)

    celery.conf.update(
        broker_url=app.config["CELERY"]["broker_url"],
        result_backend=app.config["CELERY"]["result_backend"],
        task_ignore_result=app.config["CELERY"].get("task_ignore_result", False),
        timezone=app.config.get("APP_TIMEZONE", "Asia/Kolkata"),
        imports=("tasks.reminders", "tasks.reports", "tasks.exports"),
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Explicit imports keep registration predictable without relying on Celery autodiscovery conventions.
    import tasks.reminders  # noqa: F401
    import tasks.reports  # noqa: F401
    import tasks.exports  # noqa: F401

    @celery.on_after_finalize.connect
    def setup_periodic_tasks(sender, **_kwargs):
        from tasks.reports import monthly_admin_report
        from tasks.reminders import daily_appointment_reminders

        reminder_hour = int(app.config.get("DAILY_REMINDER_HOUR", 8))
        reminder_minute = int(app.config.get("DAILY_REMINDER_MINUTE", 0))
        report_hour = int(app.config.get("MONTHLY_REPORT_HOUR", 9))
        report_minute = int(app.config.get("MONTHLY_REPORT_MINUTE", 0))

        sender.add_periodic_task(
            crontab(hour=reminder_hour, minute=reminder_minute),
            daily_appointment_reminders.s(),
            name="Send daily appointment reminders",
        )
        sender.add_periodic_task(
            crontab(hour=report_hour, minute=report_minute, day_of_month="1"),
            monthly_admin_report.s(),
            name="Send monthly doctor report on day 1",
        )

    return celery
