from __future__ import unicode_literals

from django.db import models
from django_date_extensions.fields import ApproximateDateField

from core.models import Event
from core.validators import validate_approximatedate

from .google import GoogleUsersAPI


INVOLVEMENT_CHOICES = (
    ("newcomer", "I’ve never been to a Django Girls event"),
    ("attendee", "I’m a former attendee"),
    ("coach", "I’m a former coach"),
    ("organizer", "I’m a former organizer"),
    ("contributor", "I contributed to the tutorial or translations"))


class EventApplication(models.Model):
    previous_event = models.ForeignKey(Event, null=True, blank=True)
    # workshop fields
    date = ApproximateDateField(validators=[validate_approximatedate])
    city = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    latlng = models.CharField(max_length=30, null=True, blank=True)
    website_slug = models.SlugField()
    main_organizer_email = models.EmailField()
    main_organizer_first_name = models.CharField(max_length=30)
    main_organizer_last_name = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    # application fields
    about_you = models.TextField()
    why = models.TextField()
    involvement = models.CharField(choices=INVOLVEMENT_CHOICES, max_length=15)
    experience = models.TextField()
    venue = models.TextField()
    sponsorship = models.TextField()
    coaches = models.TextField()

    def create_gmail_account(self, password):
        api = GoogleUsersAPI()
        if api.is_ok:
            if self.previous_event:
                # The previous event should have the email address city@djangogirls.org
                # It will be renamed to city-ddmmyy@djangogirls.org
                slug = self.previous_event.email_slug

                # Archive the old event and free up this one.
                old_date = self.previous_event.date
                archived_slug = '%s-%04d%02d%02d' % (slug, old_date.year, old_date.month, old_date.day)

                # Change the email address of the previous event's account
                api.rename_account(slug, archived_slug)

                # Create a new account for this event.
                api.create_account(slug, self.city, password)

                self.previous_event.email = '%s@djangogirls.org' % archived_slug
                self.previous_event.save()
            else:
                # New city...
                api.create_account(self.website_slug, self.city, password)

    class Meta:
        permissions = (
            ("can_accept_organize_application",
             "Can accept Organize Applications"),
        )


class Coorganizer(models.Model):
    event_application = models.ForeignKey(
        EventApplication,
        related_name="coorganizers")
    email = models.EmailField()
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    class Meta:
        verbose_name = "Co-organizer"
        verbose_name_plural = "Co-organizers"
