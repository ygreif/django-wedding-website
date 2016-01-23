import csv
import StringIO
from guests.models import Party, Guest


def import_guests(path):
    with open(path, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        first_row = True
        for row in reader:
            if first_row:
                first_row = False
                continue
            party_name, first_name, last_name, party_type, is_child, category, is_invited, email = row[:8]
            if not party_name:
                print 'skipping row {}'.format(row)
                continue
            party = Party.objects.get_or_create(name=party_name)[0]
            party.type = party_type
            party.category = category
            party.is_invited = _is_true(is_invited)
            party.save()
            if email:
                guest created = Guest.objects.get_or_create(party=party, email=email)
                guest.first_name = first_name
                guest.last_name = last_name
            else:
                guest = Guest.objects.get_or_create(party=party, first_name=first_name, last_name=last_name)[0]
            guest.is_child = _is_true(is_child)
            guest.save()


def export_guests():
    headers = [
        'party_name', 'first_name', 'last_name', 'party_type', 'is_child', 'category', 'is_invited', 'email'
    ]
    file = StringIO.StringIO()
    writer = csv.writer(file)
    writer.writerow(headers)
    for party in Party.objects.order_by('category', '-is_invited', 'name'):
        for guest in party.guest_set.all():
            writer.writerow([
                party.name,
                guest.first_name,
                guest.last_name,
                party.type,
                guest.is_child,
                party.category,
                party.is_invited,
                guest.email,
            ])
    return file


def _is_true(value):
    value = value or ''
    return value.lower() in ('y', 'yes')
