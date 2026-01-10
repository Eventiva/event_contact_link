# -*- coding: utf-8 -*-
{
    'name': 'Event Contact Link',
    'version': '1.2.2',
    'category': 'Events',
    'summary': 'Link event registrations to contacts with automatic contact creation',
    'description': """
        This module automatically creates or finds contacts when people are added to event registrations.
        It establishes a many2one relationship between event registrations and contacts, allowing multiple
        registrations to be linked to a single contact.
    """,
    'author': 'Eventiva',
    'website': 'www.eventiva.com',
    'license': 'Other proprietary',
    'depends': ['event', 'base', 'website_event'],
    'data': [
        'security/ir.model.access.csv',
        'views/event_registration_views.xml',
        'views/res_partner_views.xml',
        'views/website_event_templates.xml',
    ],
    'test': [
        'tests/test_event_contact_link.py',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
