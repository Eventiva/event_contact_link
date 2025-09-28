# -*- coding: utf-8 -*-
{
    'name': 'Event Contact Link',
    'version': '18.0.1.0.0',
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
    'depends': ['event', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/event_registration_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
