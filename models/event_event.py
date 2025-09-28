# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class EventEvent(models.Model):
    _inherit = 'event.event'

    # Enhanced booking detection fields
    is_participating_enhanced = fields.Boolean(
        "Is Participating (Enhanced)", 
        compute="_compute_is_participating_enhanced",
        search="_search_is_participating_enhanced",
        help="Enhanced participation detection that includes contact-linked registrations"
    )
    
    registration_count_enhanced = fields.Integer(
        "Registration Count (Enhanced)",
        compute="_compute_registration_count_enhanced",
        help="Count of registrations including those linked via contacts"
    )

    @api.depends('registration_ids', 'registration_ids.contact_id')
    @api.depends_context('uid')
    def _compute_is_participating_enhanced(self):
        """Enhanced participation detection that includes contact-linked registrations"""
        participating_events = self._fetch_is_participating_events_enhanced()
        participating_events.is_participating_enhanced = True
        (self - participating_events).is_participating_enhanced = False

    @api.model
    def _search_is_participating_enhanced(self, operator, value):
        """Search for events where user is participating (enhanced)"""
        if operator not in ['=', '!=']:
            raise NotImplementedError('This operator is not supported')
        if not isinstance(value, bool):
            raise UserError('Value should be True or False (not %)', value)
        check_is_participating = operator == '=' and value or operator == '!=' and not value

        return [('id', 'in' if check_is_participating else 'not in', self._fetch_is_participating_events_enhanced().ids)]

    @api.model
    def _fetch_is_participating_events_enhanced(self):
        """Enhanced version that includes contact-linked registrations"""
        current_visitor = self.env['website.visitor']._get_visitor_from_request()
        if self.env.user._is_public() and not current_visitor:
            return self.env['event.event']

        base_domain = [('state', 'in', ['open', 'done'])]
        if self:
            base_domain = expression.AND([[('event_id', 'in', self.ids)], base_domain])

        visitor_domain = []
        partner_id = self.env.user.partner_id
        if current_visitor:
            visitor_domain = [('visitor_id', '=', current_visitor.id)]
            partner_id = current_visitor.partner_id

        # Enhanced domain that includes contact-linked registrations
        if partner_id:
            # Original logic: direct partner_id match
            visitor_domain = expression.OR([visitor_domain, [('partner_id', '=', partner_id.id)]])
            
            # Enhanced logic: contact_id match
            visitor_domain = expression.OR([visitor_domain, [('contact_id', '=', partner_id.id)]])
            
            # Enhanced logic: email match (for manually added registrations)
            if partner_id.email:
                visitor_domain = expression.OR([visitor_domain, [('email', '=ilike', partner_id.email)]])

        registrations_events = self.env['event.registration'].sudo()._read_group(
            expression.AND([visitor_domain, base_domain]),
            ['event_id'], ['__count'])
        return self.env['event.event'].browse([event.id for event, _reg_count in registrations_events])

    @api.depends('registration_ids', 'registration_ids.contact_id')
    @api.depends_context('uid')
    def _compute_registration_count_enhanced(self):
        """Enhanced registration count that includes contact-linked registrations"""
        for event in self:
            current_visitor = self.env['website.visitor']._get_visitor_from_request()
            partner_id = self.env.user.partner_id
            if current_visitor:
                partner_id = current_visitor.partner_id

            if not partner_id:
                event.registration_count_enhanced = 0
                continue

            # Count registrations where user is participating (enhanced)
            domain = [
                ('event_id', '=', event.id),
                ('state', 'in', ['open', 'done']),
                '|',  # OR conditions
                ('partner_id', '=', partner_id.id),  # Direct partner match
                '|',  # OR conditions
                ('contact_id', '=', partner_id.id),  # Contact-linked match
                ('email', '=ilike', partner_id.email)  # Email match
            ]
            
            event.registration_count_enhanced = self.env['event.registration'].search_count(domain)

    def get_user_registrations_enhanced(self, user_id=None):
        """Get all registrations for a user including contact-linked ones"""
        if not user_id:
            user_id = self.env.user.id
        
        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            return self.env['event.registration']
            
        domain = [
            ('event_id', 'in', self.ids),
            ('state', 'in', ['open', 'done']),
            '|',  # OR conditions
            ('partner_id', '=', user.partner_id.id),  # Direct partner match
            '|',  # OR conditions
            ('contact_id', '=', user.partner_id.id),  # Contact-linked match
            ('email', '=ilike', user.email)  # Email match
        ]
        
        return self.env['event.registration'].search(domain)

    def is_user_registered_enhanced(self, user_id=None):
        """Check if a user is registered for this event (enhanced)"""
        if not user_id:
            user_id = self.env.user.id
            
        return len(self.get_user_registrations_enhanced(user_id)) > 0
