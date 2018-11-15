from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Rating(models.Model):
    user_a = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='rating_from_user')
    orga_a = models.ForeignKey('Organisation.Organisation', on_delete=models.CASCADE, blank=True, null=True,
                               related_name='rating_from_orga')

    user_b = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='rating_to_user')
    orga_b = models.ForeignKey('Organisation.Organisation', on_delete=models.CASCADE, blank=True, null=True,
                               related_name='rating_to_orga')

    rating = models.FloatField(default=0.0)

    def __str__(self):
        return str(self.rating)


class Report(models.Model):
    REASON_CHOICES = (
        ('--', 'None'),
        ('AB', 'Abuse'),
        ('HA', 'Hate'),
    )

    user_a = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='report_from_user')
    orga_a = models.ForeignKey('Organisation.Organisation', on_delete=models.CASCADE, blank=True, null=True,
                               related_name='report_from_orga')

    user_b = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='report_to_user')
    orga_b = models.ForeignKey('Organisation.Organisation', on_delete=models.CASCADE, blank=True, null=True,
                               related_name='report_to_orga')

    text = models.TextField()
    reason = models.CharField(max_length=2, choices=REASON_CHOICES, default='--')

    def __str__(self):
        return self.reason