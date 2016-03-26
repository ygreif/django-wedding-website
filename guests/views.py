import base64
from collections import namedtuple
import os
import random
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import ListView
from postmark import PMMail
from guests import csv_import
from guests.invitation import get_invitation_context, INVITATION_TEMPLATE
from guests.models import Guest, Party, MEALS
from guests.save_the_date import get_save_the_date_context, send_save_the_date_email, SAVE_THE_DATE_TEMPLATE, \
    SAVE_THE_DATE_CONTEXT_MAP


class GuestListView(ListView):
    model = Guest


@login_required
def export_guests(request):
    export = csv_import.export_guests()
    response = HttpResponse(export.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=all-guests.csv'
    return response


@login_required
def invitation(request, invite_id):
    party = _guess_party_by_invite_id_or_404(invite_id)
    if request.method == 'POST':
        for response in _parse_invite_params(request.POST):
            guest = Guest.objects.get(pk=response.guest_pk)
            assert guest.party == party
            guest.is_attending = response.is_attending
            guest.meal = response.meal
            guest.save()
    return render(request, template_name='guests/invitation.html', context={
        'party': party,
        'meals': MEALS,
    })


def _guess_party_by_invite_id_or_404(invite_id):
    try:
        return Party.objects.get(invitation_id=invite_id)
    except Party.DoesNotExist:
        if settings.DEBUG:
            # in debug mode allow access by ID
            return Party.objects.get(id=int(invite_id))
        else:
            raise Http404()


InviteResponse = namedtuple('InviteResponse', ['guest_pk', 'is_attending', 'meal'])


def _parse_invite_params(params):
    responses = {}
    for param, value in params.items():
        if param.startswith('attending'):
            pk = int(param.split('-')[-1])
            response = responses.get(pk, {})
            response['attending'] = True if value == 'yes' else False
            responses[pk] = response
        elif param.startswith('meal'):
            pk = int(param.split('-')[-1])
            response = responses.get(pk, {})
            response['meal'] = value
            responses[pk] = response

    for pk, response in responses.items():
        yield InviteResponse(pk, response['attending'], response['meal'])


@login_required
def invitation_email_preview(request, invite_id):
    try:
        party = Party.objects.get(invitation_id=invite_id)
    except Party.DoesNotExist:
        if settings.DEBUG:
            # in debug mode allow access by ID
            party = Party.objects.get(id=int(invite_id))
        else:
            raise Http404()

    context = get_invitation_context()
    context.update({
        'invitation_id': party.invitation_id,
        'party': party,
        'meals': MEALS,
    })
    return render(request, INVITATION_TEMPLATE, context=context)


def save_the_date_random(request):
    template_id = random.choice(SAVE_THE_DATE_CONTEXT_MAP.keys())
    return save_the_date_preview(request, template_id)


def save_the_date_preview(request, template_id):
    context = get_save_the_date_context(template_id)
    context['email_mode'] = False
    return render(request, SAVE_THE_DATE_TEMPLATE, context=context)


@login_required
def test_email(request, template_id):
    context = get_save_the_date_context(template_id)
    send_save_the_date_email(context, ['cory.zue@gmail.com'])
    # send_save_the_date_email(context, ['cory.zue@gmail.com', 'rowenaluk@gmail.com'])
    return HttpResponse('sent!')


@login_required
def test_postmark_email(request):
    template_text = render_to_string('guests/email_templates/save_the_date.html', context={'email_mode': True})
    attachments = []
    for filename in ('hearts.png', 'selfie.jpg'):
        attachment_path = os.path.join(os.path.dirname(__file__), 'static', 'save-the-date', 'images', filename)
        encoded_attachment = _base64_encode(attachment_path)
        attachments.append(
            (filename, encoded_attachment, 'image/{}'.format(filename.split('.')[-1]), 'cid:{}'.format(filename))
        )

    mail = PMMail(
        to='Cory Zue <cory.zue@gmail.com>',
        subject='save the date!',
        html_body=template_text,
        text_body='sorry, you need to view this in html mode',
        attachments=attachments
    )
    mail.send()
    return HttpResponseRedirect(reverse('save-the-date'))


def _base64_encode(filepath):
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read())
