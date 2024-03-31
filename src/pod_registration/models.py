from django.conf import settings
from django.db import models
from django.shortcuts import reverse

from datetime import datetime
from pytz import timezone

import pytz

# Create your models here.


class SolidPod(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    url = models.URLField(default='')
    last_viewed = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.url

    def viewed(self):
        self.last_viewed = datetime.utcnow()
        self.save()
        return

    @property
    def local_last_viewed(self):
        eastern = timezone('US/Eastern')
        return self.last_viewed.astimezone(eastern)

    @property
    def view_url(self):
        base_url = reverse('pod_registration:view_resource', kwargs={"pk": self.pk})
        final_url = base_url + '?url=' + self.url
        return final_url


class OpenIDprovider(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField()
    provider_info = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        return self.url


# class WebID(models.Model):
#     provider = models.ForeignKey(to=OpenIDprovider, on_delete=models.CASCADE)
#     user = models.ForeignKey(to=settings.AUTH_USER_MODEL,
#                              on_delete=models.CASCADE)
#     webid = models.URLField(default='')
#
#     def __str__(self):
#         return f"issuer: {self.webid}"


class StateSessionManager(models.Manager):
    def with_webid(self, user):
        return super(StateSessionManager, self).filter(user=user).exclude(webid__isnull=True).exclude(webid='')


class StateSession(models.Model):
    webid           = models.URLField(default='', null=True, blank=True)
    oicdp           = models.ForeignKey(to=OpenIDprovider, on_delete=models.CASCADE, null=True, blank=True)
    user            = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    state           = models.CharField(max_length=255, unique=True)
    redirect_view   = models.CharField(max_length=255, default='', null=True, blank=True)
    client_id       = models.CharField(max_length=255, default='', null=True, blank=True)
    client_secret   = models.CharField(max_length=255, default='', null=True, blank=True)
    DPoP_key        = models.JSONField(default=dict, null=True, blank=True)
    code_verifier   = models.CharField(max_length=255, default='', null=True, blank=True)
    access_token    = models.CharField(max_length=1024, default='', null=True, blank=True)
    id_token        = models.CharField(max_length=1024, default='', null=True, blank=True)
    refresh_token   = models.CharField(max_length=1024, default='', null=True, blank=True)
    expires_at      = models.DateTimeField(null=True, blank=True)
    token_type      = models.CharField(max_length=255, default='', null=True, blank=True)
    timestamp       = models.DateTimeField(auto_now=False, auto_now_add=True, blank=True)
    updated         = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True)
    objects = StateSessionManager()

    def __str__(self):
        return f"state: {self.state}"

    @property
    def is_active(self):
        now = datetime.now(pytz.UTC)
        return self.expires_at > now

    @property
    def local_expires_at(self):
        if self.expires_at:
            eastern = timezone('US/Eastern')
            return self.expires_at.astimezone(eastern)
        else:
            return None

    def refresh_token_query(self, redirect_view):
        refresh_token_view = reverse('connector:refresh-token')
        refresh_token_query = f'{refresh_token_view}?session_pk={self.pk}&redirect_uri={redirect_view}'
        return refresh_token_query
