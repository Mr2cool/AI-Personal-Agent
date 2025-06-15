import unittest
from app import app, init_user_db, DB_PATH
import sqlite3

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        global DB_PATH
        self.app = app.test_client()
        # Use a test DB
        self._orig_db = DB_PATH
        self.test_db = 'test_users.db'
        DB_PATH = self.test_db
        app.config['TESTING'] = True
        init_user_db()

    def tearDown(self):
        global DB_PATH
        import os
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        DB_PATH = self._orig_db

    def test_register_login_logout(self):
        rv = self.app.post('/register', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
        self.assertIn(b'Registration successful', rv.data)
        rv = self.app.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
        self.assertIn(b'AI Search Assistant', rv.data)
        rv = self.app.get('/logout', follow_redirects=True)
        self.assertIn(b'Login', rv.data)

    def test_profile_edit(self):
        self.app.post('/register', data={'username': 'editme', 'password': 'pass'}, follow_redirects=True)
        self.app.post('/login', data={'username': 'editme', 'password': 'pass'}, follow_redirects=True)
        rv = self.app.post('/profile/edit', data={'username': 'edited'}, follow_redirects=True)
        self.assertIn(b'Profile updated', rv.data)

    def test_admin_delete_user(self):
        self.app.post('/register', data={'username': 'admin', 'password': 'adminpass'}, follow_redirects=True)
        self.app.post('/login', data={'username': 'admin', 'password': 'adminpass'}, follow_redirects=True)
        self.app.post('/register', data={'username': 'victim', 'password': 'pass'}, follow_redirects=True)
        rv = self.app.post('/admin/delete_user/2', follow_redirects=True)
        self.assertIn(b'User deleted', rv.data)

if __name__ == '__main__':
    unittest.main()
