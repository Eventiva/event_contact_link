# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    event_registration_ids = fields.One2many(
        'event.registration',
        'contact_id',
        string='Linked Event Registrations',
        help='Event registrations linked to this contact',
    )
