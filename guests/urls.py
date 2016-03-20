from django.conf.urls import url

from . import views
from guests.views import GuestListView, test_email, save_the_date_preview, save_the_date_random, export_guests, \
    invitation

urlpatterns = [
    url(r'^guests/$', GuestListView.as_view(), name='guest-list'),
    url(r'^guests/export$', export_guests, name='export-guest-list'),
    url(r'^invite/$', invitation, name='invitation'),
    url(r'^save-the-date/$', save_the_date_random, name='save-the-date-random'),
    url(r'^save-the-date/(?P<template_id>[\w-]+)/$', save_the_date_preview, name='save-the-date'),
    url(r'^email-test/(?P<template_id>[\w-]+)/$', test_email, name='test-email'),
]
