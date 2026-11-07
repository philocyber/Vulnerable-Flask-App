import json
import os
import shutil
import tempfile
import unittest

from app.app import User, app, db, setup_users


class InitialAdminTest(unittest.TestCase):
    def test_fresh_database_requires_operator_password(self):
        directory = tempfile.mkdtemp()
        previous_password = os.environ.pop('INITIAL_ADMIN_PASSWORD', None)
        previous_uri = app.config['SQLALCHEMY_DATABASE_URI']
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(directory, 'test.db').replace('\\', '/')
            app.config['TESTING'] = True
            client = app.test_client()

            with app.app_context():
                with self.assertRaises(RuntimeError):
                    setup_users()
                self.assertIsNone(User.query.first())

            os.environ['INITIAL_ADMIN_PASSWORD'] = 'a-unique-operator-secret-892'
            default_login = client.post('/login', data=json.dumps({
                'username': 'admin', 'password': 'admin123'}),
                content_type='application/json')
            self.assertNotEqual(default_login.status_code, 200)
            self.assertNotIn('Authorization', default_login.headers)

            protected = client.post('/fetch/customer', data=json.dumps({'id': 1}),
                                    content_type='application/json')
            self.assertEqual(protected.status_code, 403)

            provisioned_login = client.post('/login', data=json.dumps({
                'username': 'admin', 'password': 'a-unique-operator-secret-892'}),
                content_type='application/json')
            self.assertEqual(provisioned_login.status_code, 200)
            self.assertIn('Authorization', provisioned_login.headers)
        finally:
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
            app.config['SQLALCHEMY_DATABASE_URI'] = previous_uri
            app.config['TESTING'] = False
            if previous_password is None:
                os.environ.pop('INITIAL_ADMIN_PASSWORD', None)
            else:
                os.environ['INITIAL_ADMIN_PASSWORD'] = previous_password
            shutil.rmtree(directory)


if __name__ == '__main__':
    unittest.main()
