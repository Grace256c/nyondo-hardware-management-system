from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('sales_attendant', 'Sales Attendant'),
        ('store_manager',   'Store Manager'),
        ('admin',           'Admin'),
    ]

    user       = models.OneToOneField(User, on_delete=models.CASCADE)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='sales_attendant')
    phone      = models.CharField(max_length=20)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()