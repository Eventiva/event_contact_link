# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestEventContactLink(TransactionCase):

    def setUp(self):
        super().setUp()
        self.event = self.env['event.event'].create({
            'name': 'Test Event',
            'date_begin': '2024-01-01 09:00:00',
            'date_end': '2024-01-01 17:00:00',
        })

    def test_contact_auto_creation(self):
        """Test that contacts are automatically created when creating registrations"""
        # Create a registration with email and name
        registration = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '+1234567890',
            'company_name': 'Test Company',
        })

        # Check that a contact was created and linked
        self.assertTrue(registration.contact_id)
        self.assertEqual(registration.contact_id.name, 'John Doe')
        self.assertEqual(registration.contact_id.email, 'john.doe@example.com')
        self.assertEqual(registration.contact_id.phone, '+1234567890')
        self.assertEqual(registration.contact_id.company_name, 'Test Company')
        self.assertFalse(registration.contact_id.is_company)

    def test_contact_reuse(self):
        """Test that existing contacts are reused when creating registrations"""
        # Create a contact first
        contact = self.env['res.partner'].create({
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'is_company': False,
        })

        # Create a registration with the same email
        registration = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
        })

        # Check that the existing contact was linked
        self.assertEqual(registration.contact_id, contact)

        # Check that contact information was updated
        self.assertEqual(contact.name, 'Jane Smith')

    def test_contact_field_synchronization(self):
        """Test that contact field changes sync to registration fields"""
        # Create a registration
        registration = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Test User',
            'email': 'test@example.com',
        })

        # Update the contact
        registration.contact_id.write({
            'name': 'Updated Name',
            'phone': '+9876543210',
        })

        # Check that registration fields are updated via onchange
        registration._onchange_contact_id()
        self.assertEqual(registration.name, 'Updated Name')
        self.assertEqual(registration.phone, '+9876543210')

    def test_multiple_registrations_same_contact(self):
        """Test that multiple registrations can be linked to the same contact"""
        # Create first registration
        registration1 = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Multi User',
            'email': 'multi@example.com',
        })
        
        # Create second event
        event2 = self.env['event.event'].create({
            'name': 'Test Event 2',
            'date_begin': '2024-01-02 09:00:00',
            'date_end': '2024-01-02 17:00:00',
        })
        
        # Create second registration with same email
        registration2 = self.env['event.registration'].create({
            'event_id': event2.id,
            'name': 'Multi User',
            'email': 'multi@example.com',
        })
        
        # Check that both registrations are linked to the same contact
        self.assertEqual(registration1.contact_id, registration2.contact_id)
        self.assertEqual(len(registration1.contact_id.event_registration_ids), 2)

    def test_enhanced_booking_detection(self):
        """Test enhanced booking detection for contact-linked registrations"""
        # Create a user
        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser@example.com',
            'email': 'testuser@example.com',
        })
        
        # Create a registration with the user's email (but not directly linked)
        registration = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Test User',
            'email': 'testuser@example.com',
            'state': 'open',
        })
        
        # Check enhanced participation detection
        self.assertTrue(self.event.is_user_registered_enhanced(user.id))
        self.assertTrue(self.event.is_participating_enhanced)
        self.assertEqual(self.event.registration_count_enhanced, 1)
        
        # Get user registrations
        user_registrations = self.event.get_user_registrations_enhanced(user.id)
        self.assertEqual(len(user_registrations), 1)
        self.assertEqual(user_registrations[0], registration)

    def test_enhanced_booking_detection_contact_linked(self):
        """Test enhanced booking detection for contact-linked registrations"""
        # Create a user
        user = self.env['res.users'].create({
            'name': 'Test User 2',
            'login': 'testuser2@example.com',
            'email': 'testuser2@example.com',
        })
        
        # Create a registration and link it to the user's contact
        registration = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Different Name',
            'email': 'different@example.com',
            'contact_id': user.partner_id.id,
            'state': 'open',
        })
        
        # Check enhanced participation detection
        self.assertTrue(self.event.is_user_registered_enhanced(user.id))
        self.assertTrue(self.event.is_participating_enhanced)
        self.assertEqual(self.event.registration_count_enhanced, 1)
        
        # Get user registrations
        user_registrations = self.event.get_user_registrations_enhanced(user.id)
        self.assertEqual(len(user_registrations), 1)
        self.assertEqual(user_registrations[0], registration)

    def test_booking_status_for_user(self):
        """Test the booking status method for individual registrations"""
        # Create a user
        user = self.env['res.users'].create({
            'name': 'Test User 3',
            'login': 'testuser3@example.com',
            'email': 'testuser3@example.com',
        })
        
        # Create a registration with the user's email
        registration = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Test User 3',
            'email': 'testuser3@example.com',
            'state': 'open',
        })
        
        # Check booking status
        self.assertTrue(registration._get_booking_status_for_user(user.id))
        
        # Test with different user
        other_user = self.env['res.users'].create({
            'name': 'Other User',
            'login': 'other@example.com',
            'email': 'other@example.com',
        })
        self.assertFalse(registration._get_booking_status_for_user(other_user.id))
