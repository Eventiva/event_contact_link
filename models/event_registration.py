'''
@license
@preserve
File: \\event_registration.py
Project: models (<<projectversion>>)
Created Date: Sunday, September 28th 2025, 4:35:16 pm
Author: Jonathan Stevens

--------------------------------------------------------------------------------

Last Modified: Sunday, 28th September 2025 4:36:04 pm
Modified By: Jonathan Stevens <jonathan.stevens@resnovas.com>

--------------------------------------------------------------------------------

Code of Conduct: This project abides by the Contributor Covenant, v2.0.
Please interact in ways that contribute to an open, welcoming, diverse,
inclusive, and healthy community. Our Code of Conduct can be found at
https://github.com/eventiva/eventiva/blob/develop/CODE_OF_CONDUCT.md

Contributing: Please read through our contributing guidelines. Included
are directions for opening issues, coding standards, and notes on
development. These can be found at
https://github.com/eventiva/eventiva/blob/develop/CONTRIBUTING.md

--------------------------------------------------------------------------------

Copyright (c) 2025 Jonathan Stevens T/a Resnovas, Resnovas Ltd or its affiliates
License: Fair Core License, Version 1.0, MIT Future License (FCL-1.0-MIT)

This program has been provided under confidence of the copyright holder
and is licensed for copying, distribution andmodification under the terms
of the Fair Core License, Version 1.0, MIT Future License (FCL-1.0-MIT)
published as the License, or any later version of this license. You must
not move, change, disable, or circumvent the license key functionality in
the Software; or modify any portion of the Software protected by the
license key to: enable access to the protected functionality without a
valid license key; or remove the protected functionality. This program is
distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the Fair Core License, Version 1.0, MIT Future
License for more details. You should have received a copy of the
Fair Core License, Version 1.0, MIT Future License (FCL-1.0-MIT)
along with this program. If not, please write to:
licensing@resnovas.com, see the official website
https://fcl.dev/ or Review the GitHub repository
https://github.com/keygen-sh/fcl.dev/

This project abides the Resnovas Cooperation Commitment
Adapted from the GPL Cooperation Commitment (GPLCC). Before filing or
continuing to prosecute any legal proceeding or claim (other than a
Defensive Action) arising from termination of a Covered License, we
commit to adhering to the Resnovas Cooperation Commitment.
You should have received a copy of the Resnovas Cooperation Commitment
along with this program. If not, please write to:
licensing@resnovas.com.

--------------------------------------------------------------------------------

For the purpose of determining the applicable license terms, a file
history is provided herein. As this historical record may be
incomplete, it is recommended that the repository be cloned and the
following command executed:

git checkout `git rev-list -n 1 --before='2 years ago' main`.

In the event that the licensed file is subject to the FCL, the version
under the Open Source terms of the change license shall apply.

HISTORY:
Date      	By	Comments
----------	---	----------------------------------------------------------------
'''


# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import email_normalize


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    # New field to link to contact
    contact_id = fields.Many2one(
        'res.partner',
        string='Contact',
        help='The contact associated with this registration',
        domain=[('is_company', '=', False)]
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically find or create contacts"""
        for vals in vals_list:
            # Process if we have email or name and no contact_id is provided
            if not vals.get('contact_id') and (vals.get('email') or vals.get('name')):
                contact = self._find_or_create_contact(vals)
                if contact:
                    vals['contact_id'] = contact.id

        return super().create(vals_list)

    def write(self, vals):
        """Override write to automatically find or create contacts when email/name changes"""
        # Clear contact_id if email or name is being changed (to allow re-evaluation)
        # We need to clear it per-record, so we'll do it after super().write()
        result = super().write(vals)

        # Clear contact_id for records where email or name was changed
        if 'email' in vals or 'name' in vals:
            for record in self:
                if record.contact_id:
                    record.contact_id = False

        # Only process if contact_id is not already set and we have email or name
        for record in self:
            if not record.contact_id and (record.email or record.name):
                contact = record._find_or_create_contact({
                    'email': record.email,
                    'name': record.name,
                    'phone': record.phone,
                    'company_name': record.company_name,
                })
                if contact:
                    record.contact_id = contact.id

        return result

    def _find_or_create_contact(self, vals):
        """Find existing contact by email or name, or create a new one"""
        email = vals.get('email')
        name = vals.get('name', '')
        phone = vals.get('phone', '')
        company_name = vals.get('company_name', '')

        if not email and not name:
            return False

        existing_contact = None

        # First, try to find existing contact by normalized email
        if email:
            email_normalized = email_normalize(email)
            if email_normalized:
                existing_contact = self.env['res.partner'].search([
                    ('email_normalized', '=', email_normalized),
                    ('is_company', '=', False)
                ], limit=1)

        # If no contact found by email and we have a name, try to find by name
        if not existing_contact and name:
            # Search for contacts with the same name (case-insensitive)
            existing_contact = self.env['res.partner'].search([
                ('name', '=ilike', name),
                ('is_company', '=', False)
            ], limit=1)

        # If we found an existing contact, update it with new information
        if existing_contact:
            update_vals = {}
            if email and email != existing_contact.email:
                update_vals['email'] = email
            # Skip name update if it's an auto-generated guest name (contains "Guest")
            # This prevents auto-generated guest registration names from overwriting the contact name
            if name and name != existing_contact.name and ' Guest ' not in name:
                update_vals['name'] = name
            if phone and phone != existing_contact.phone:
                update_vals['phone'] = phone
            if company_name and company_name != existing_contact.company_name:
                update_vals['company_name'] = company_name

            if update_vals:
                existing_contact.write(update_vals)

            return existing_contact

        # If no existing contact found, create a new one
        create_vals = {
            'is_company': False,
        }

        if email:
            create_vals['email'] = email
            create_vals['name'] = name or email.split('@')[0]
        else:
            create_vals['name'] = name or 'Unknown Contact'

        if phone:
            create_vals['phone'] = phone
        if company_name:
            create_vals['company_name'] = company_name

        return self.env['res.partner'].create(create_vals)

    @api.onchange('contact_id')
    def _onchange_contact_id(self):
        """Update registration fields when contact is selected"""
        if self.contact_id:
            self.name = self.contact_id.name
            self.email = self.contact_id.email
            self.phone = self.contact_id.phone
            self.company_name = self.contact_id.company_name
            self.partner_id = self.contact_id

    @api.onchange('email', 'name', 'phone', 'company_name')
    def _onchange_contact_fields(self):
        """Clear contact_id when fields change to allow re-evaluation on save"""
        # Clear contact_id when email or name fields change so it gets re-evaluated on save
        # This ensures that when email/name changes, the contact is re-evaluated
        self.contact_id = False

    def _get_booking_status_for_user(self, user_id=None):
        """Get booking status for a specific user based on contact linking"""
        if not user_id:
            user_id = self.env.user.id

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            return False

        # Check if this registration is linked to the user's contact
        if self.contact_id and self.contact_id == user.partner_id:
            return True

        # Check if this registration was created by the user
        if self.partner_id and self.partner_id == user.partner_id:
            return True

        # Check if the registration email matches the user's email
        if self.email and user.email and self.email.lower() == user.email.lower():
            return True

        return False

    def action_link_to_existing_contact(self):
        """Action to manually link registration to an existing contact"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Link to Existing Contact',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'target': 'new',
            'context': {
                'default_is_company': False,
                'link_registration_id': self.id,
            },
            'domain': [('is_company', '=', False)],
        }

    def action_find_or_create_contact(self):
        """Manually trigger contact finding/creation based on current field values"""
        if self.email or self.name:
            contact = self._find_or_create_contact({
                'email': self.email,
                'name': self.name,
                'phone': self.phone,
                'company_name': self.company_name,
            })
            if contact:
                self.contact_id = contact.id
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Contact Linked',
                        'message': f'Registration linked to contact: {contact.name}',
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'No Contact Found',
                        'message': 'No matching contact found. Please check the name and email.',
                        'type': 'warning',
                    }
                }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Missing Information',
                    'message': 'Please provide a name or email to find/create a contact.',
                    'type': 'warning',
                }
            }

    @api.model
    def fix_duplicate_contacts(self):
        """Method to fix duplicate contacts and link registrations properly"""
        # Find registrations without contact_id but with name
        registrations_without_contact = self.search([
            ('contact_id', '=', False),
            ('name', '!=', False)
        ])

        for registration in registrations_without_contact:
            # Try to find existing contact by name
            existing_contact = self.env['res.partner'].search([
                ('name', '=ilike', registration.name),
                ('is_company', '=', False)
            ], limit=1)

            if existing_contact:
                # Link registration to existing contact
                registration.contact_id = existing_contact.id

                # Update contact with registration information if missing
                update_vals = {}
                if registration.email and not existing_contact.email:
                    update_vals['email'] = registration.email
                if registration.phone and not existing_contact.phone:
                    update_vals['phone'] = registration.phone
                if registration.company_name and not existing_contact.company_name:
                    update_vals['company_name'] = registration.company_name

                if update_vals:
                    existing_contact.write(update_vals)
