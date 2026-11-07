import json
import unittest

import jwt

from app.app import app, db, Customer, get_exp_date


class SearchCustomerTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()
        db.session.add(Customer(first_name='Alice', last_name='Example',
                                username='alice', ccn='4111111111111111',
                                password='customer-secret'))
        db.session.commit()
        token = jwt.encode({'user': 'test', 'exp': get_exp_date(), 'iss': 'we45'},
                           app.config['SECRET_KEY_HMAC'], algorithm='HS256')
        if isinstance(token, bytes):
            token = token.decode('ascii')
        self.headers = {'Authorization': token}
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def search(self, username):
        return self.client.post('/search',
                                data=json.dumps({'search': username}),
                                content_type='application/json',
                                headers=self.headers)

    def test_search_treats_union_payload_as_literal_username(self):
        response = self.search("' UNION SELECT ccn,password,email FROM customer -- ")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode('utf-8')), [])
        self.assertNotIn(b'4111111111111111', response.data)
        self.assertNotIn(b'customer-secret', response.data)

    def test_search_returns_only_public_fields_for_matching_username(self):
        response = self.search('alice')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode('utf-8')),
                         [['Alice', 'Example', 'alice']])


if __name__ == '__main__':
    unittest.main()
