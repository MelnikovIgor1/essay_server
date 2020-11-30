import io
import unittest
import os


from main import app
import server_module


class BasicTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server_module.DATABASENAME = 'testdatabase.db'

        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'testdatabase.db')
        os.remove(path)

        cls.app = app.test_client()
        server_module.make_database(server_module.DATABASENAME)

    def test_main_page(self):
        response = self.app.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    def test_new_account(self):
        response = self.new_account_request('username_test', 'password', 'MIPT')
        self.assertEqual(response.status_code, 200)

        response = self.login('username_test', 'password')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'username: username_test', response.data)

    def test_create_existing_account(self):
        response = self.new_account_request('new_user_test', 'password', 'MIPT')
        self.assertEqual(response.status_code, 200)

        response = self.new_account_request('new_user_test', 'password', 'MIPT')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sorry, this login is already taken.', response.data)

    def test_searching(self):
        response = self.new_account_request('new_searcher_test', 'password', 'MIPT')
        self.assertEqual(response.status_code, 200)

        response = self.search('new_searcher_test', 'art')
        self.assertEqual(response.status_code, 200)

    def test_peer_essay(self):
        response = self.new_account_request('new_searcher_test_', 'password', 'MIPT')
        self.assertEqual(response.status_code, 200)
        response = self.new_account_request('new_maker_test', 'password', 'MIPT')
        self.assertEqual(response.status_code, 200)

        response = self.load_new_essay('new_maker_test', 'test_title', 'test_tag')
        self.assertEqual(response.status_code, 200)

        response = self.search('new_searcher_test_', 'test_tag')
        self.assertEqual(response.status_code, 200)

        self.assertNotIn(b'.txt', response.data)

    def new_account_request(self, umane, psw, institution):
        return self.app.post('/create_account', data=dict(
            uname=umane,
            psw=psw,
            institution=institution
        ), follow_redirects=True)

    def load_new_essay(self, username, title, tags):
        data = dict(
            title=title,
            tags=tags,
            file=(io.BytesIO(b"abcdef"), '0.txt'),
            info=f"{{'name': '{username}'}}"
        )
        return self.app.post(f'/user/{username}/upload_essay', data=data, follow_redirects=True)

    def login(self, umane, psw):
        return self.app.post('/login', data=dict(
            uname=umane,
            psw=psw
        ), follow_redirects=True)

    def search(self, umane, tag):
        return self.app.post(f'/search/{umane}', data=dict(
            tag=tag,
            info={'name': umane}
        ), follow_redirects=True)
