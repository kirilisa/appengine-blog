from google.appengine.ext import ndb


class Comment(ndb.Model):
    """ Represents a comment in the datastore

    Attributes:
        authorkey: The User key for the author of this comment
        articlekey: The Article key for the article that owns this comment    
        name: The name of the person making the comment
        content: The text content of the comment
        created: The date & time the comment was created
    """

    authorkey = ndb.KeyProperty(kind='User', required=True)
    articlekey = ndb.KeyProperty(kind='Article', required=True)
    name = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def fetch(cls, articleid, commentid=None):
        if commentid:
            key = ndb.Key('Article', articleid, 'Comment', commentid)
        else:
            key = ndb.Key('Article', articleid)

        return cls.query(cls.key == key).order(-cls.created).get()

    # get info about the author of this instance
    @property
    def author(self):
        return self.authorkey.get()

    # get info about the parent article of this instance
    @property
    def article(self):
        return self.articlekey.get()

    # deal with linebreaks for the content display
    def tidy_content(self):
        return self.content.replace('\n', '<br>')
