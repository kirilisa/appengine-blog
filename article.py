from google.appengine.ext import ndb

from comment import Comment
from user import User


class Article(ndb.Model):
    """ Represents an article in the datastore

    Attributes:
        authorkey: The User key for the author of this article
        likekeys: A list of User keys of users that have liked this article
        subject: The title/subject of the article
        content: The text content of the article
        created: The date & time the article was created
    """

    authorkey = ndb.KeyProperty(kind='User', required=True)
    likekeys = ndb.KeyProperty(kind='User', repeated=True)
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def fetch(cls, articleid=None, limit=10):
        if articleid:
            key = ndb.Key(cls, articleid)
            article = cls.query(cls.key == key).get()
        else:
            article = cls.query().order(-cls.created).fetch(limit)
        return article

    @classmethod
    def fetch_by_username(cls, username, limit=10):
        user = User.query(User.username == username).fetch(1)
        if len(user) == 1:
            return Article.query(
                Article.authorkey ==
                user[0].key).order(-Article.created).fetch(limit)
        return None

    # get info about the author of this instance
    @property
    def author(self):
        return self.authorkey.get()

    # fetch comments for this instance
    # is there some better way of doing this?
    @property
    def comments(self):
        comments = Comment.query(
            Comment.articlekey == self.key).order(-Comment.created)
        return comments

    # get the count of comments for this instance
    # is there some better way of doing this?
    @property
    def numcomments(self):
        #options = ndb.QueryOptions(keys_only = True)
        qry = Comment.query(Comment.articlekey == self.key)
        return qry.count()

    # get the count of likes for this instance
    @property
    def numlikes(self):
        return len(self.likekeys)

    # deal with linebreaks for the content display
    def tidy_content(self):
        return self.content.replace('\n', '<br>')
