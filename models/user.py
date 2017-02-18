from google.appengine.ext import ndb

import utilities


class User(ndb.Model):
    """ Represents a user in the datastore

    Attributes:
        username: The username for this user
        pass_hash: The hashed/secured password for this user
        email: The email of this user
    """

    username = ndb.StringProperty(required=True)
    pass_hash = ndb.StringProperty(required=True)
    email = ndb.StringProperty()

    @classmethod
    def lookup_id(cls, user_id):
        return cls.get_by_id(user_id)

    @classmethod
    def lookup_username(cls, username):
        return cls.query(cls.username == username).get()

    @classmethod
    def register(cls, username, password, email=None):
        pass_hash = utilities.make_pw_hash(username, password)

        user = cls(username=username, pass_hash=pass_hash, email=email)
        user.put()
        return user

    @classmethod
    def valid_credentials(cls, username, password):
        user = cls.lookup_username(username)
        if user and utilities.valid_pw(username, password, user.pass_hash):
            return user
