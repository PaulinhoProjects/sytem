import unittest
import os
from app import create_app
from models import db, Usuario

class BasicTests(unittest.TestCase):
    def setUp(self):
        # Configução para teste
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_app_exists(self):
        self.assertFalse(self.app is None)

    def test_app_is_testing(self):
        self.assertTrue(self.app.config['TESTING'])

    def test_main_page_redirect(self):
        # Deve redirecionar para login por falta de autenticação
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)

if __name__ == "__main__":
    unittest.main()
