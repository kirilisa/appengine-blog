import os
import time
import jinja2
import webapp2

from google.appengine.ext import ndb

from models.article import Article
from models.comment import Comment
from models.user import User
import utilities

# set up variables for the templating environment
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
JINJA = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR), autoescape=True)


class Handler(webapp2.RequestHandler):
    """ A Handler to act as a parent class for all Page classes,
    taking care of basic functionality for rendering, authorization,
    and dealing with cookie manipulations
    """

    user = None

    # so we don't have to keep writing self.response.write
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        template = JINJA.get_template(template)
        return template.render(params)

    def render(self, template, **kw):
        if 'user' not in kw:
            kw['user'] = self.user

        self.write(self.render_str(template, **kw))

    # return the value of a certain cookie, if it exists and is valid
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and utilities.check_secure_val(cookie_val)

    # set a cookie with a certain name and value
    def set_secure_cookie(self, name, val):
        cookie_val = utilities.make_secure_val(val)
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' %
                                         (name, str(cookie_val)))

    # delete a cookie of a certain name
    def delete_cookie(self, name):
        self.response.headers.add_header(
            'Set-Cookie', '%s=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT;'
            % name)

    # set the login cookie
    def login(self, user):
        self.set_secure_cookie('user_id', user.key.integer_id())

    # delete the login cookie
    def logout(self):
        self.delete_cookie('user_id')

    # redirect if nobody is logged in
    def authorize(self, user_id=None):
        if not self.user:
            return self.redirect("/login", abort=True)

        if user_id and user_id != self.user.key.id():
            return self.redirect("/unauthorized", abort=True)

        return True

    # google app engine calls this before every request
    # check user cookie: if it exists, lookup user and store in user variable
    # very useful, b/c then we automatically have user info on every page
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.lookup_id(int(uid))


class UnauthorizedPage(Handler):
    def get(self):
        self.render("unauthorized.html")

class NotFoundPage(Handler):
    def get(self):
        self.render("notfound.html")        

class MainPage(Handler):
    def get(self):
        self.render("index.html")


class BlogPage(Handler):
    def get(self, *a):
        # filter by user, if supplied
        if a and a[0]:
            articles = Article.fetch_by_username(a[0])            
        else:
            articles = Article.fetch()
            
        self.render("blog.html", articles=articles)


class SinglePage(Handler):
    def get(self, article_id):
        article = Article.fetch(int(article_id))
        if not article:
            return self.redirect("/notfound")
        else:
            self.render("single.html", article=article)


class DashboardPage(Handler):
    def get(self):
        self.authorize()
        self.render("dashboard.html")


class NewCommentPage(Handler):
    def post(self):
        # make sure we are logged in
        self.authorize()

        authorkey = ndb.Key(User, int(self.request.get(
            "author"))) if self.request.get("author").isdigit() else None
        articlekey = ndb.Key(Article, int(self.request.get(
            "article"))) if self.request.get("article").isdigit() else None
        content = self.request.get("content")
        name = self.user.username if self.user else None

        if name and content and authorkey and articlekey:
            comment = Comment(
                parent=articlekey,
                name=name,
                content=content,
                authorkey=authorkey,
                articlekey=articlekey)
            comment.put()

        # the cheater's way to give DB time to update
        time.sleep(0.1)
        self.redirect("/blog/%d" % articlekey.id())


class EditCommentPage(Handler):
    def post(self):
        # figure out what action this is
        action = self.request.get("action").lower()

        # get the posted data
        article_id = int(self.request.get("articlekey"))
        comment_id = int(self.request.get("commentkey"))

        # grab the comment's original info & author
        comment = Comment.fetch(article_id, comment_id)

        # if the comment doesn't exist, get out of here
        if not comment:
            return self.redirect("/notfound")

        author_id = comment.authorkey.id()

        # make sure we are logged in as the comment owner
        self.authorize(author_id)

        if action == "edit":
            # show the initial edit page
            self.render(
                "comment-edit.html",
                commentkey=comment_id,
                articlekey=article_id,
                content=comment.content)

        if action == "delete":
            # delete the article and redirect to the blog
            comment.key.delete()

            # the cheater's way to give DB time to update
            time.sleep(0.1)
            return self.redirect("/blog/%d" % article_id)


class UpdateCommentPage(Handler):
    def post(self):
        # get the posted data
        article_id = int(self.request.get("articlekey"))
        comment_id = int(self.request.get("commentkey"))
        content = self.request.get("content")

        # grab the article's original info & author
        comment = Comment.fetch(article_id, comment_id)

        # if the comment doesn't exist, get out of here
        if not comment:
            return self.redirect("/notfound")

        author_id = comment.authorkey.id()

        # make sure we are logged in as the comment owner
        self.authorize(author_id)

        if comment and content:
            comment.content = content
            comment.put()

            # the cheater's way to give DB time to update
            time.sleep(0.1)
            return self.redirect("/blog/%d" % article_id)
        else:
            error = "Please provide a comment!"
            self.render(
                "comment-edit.html",
                commentkey=comment_id,
                articlekey=article_id,
                content=content,
                error=error)


class EditArticlePage(Handler):
    def post(self):
        # figure out what action this is
        action = self.request.get("action").lower()

        # look up the article by its passed id
        article_id = int(self.request.get("articlekey"))
        article = Article.fetch(article_id)

        # if the article doesn't exist, get out of here
        if not article:
            return self.redirect("/notfound")
        
        author_id = article.author.key.id()

        if action == "edit":
            # make sure we are logged in as the article owner
            self.authorize(author_id)

            # show the initial edit page
            self.render(
                "article-edit.html",
                authorkey=author_id,
                articlekey=article_id,
                subject=article.subject,
                content=article.content)

        elif action == "delete":
            # make sure we are logged in as the article owner
            self.authorize(author_id)

            # delete the article and redirect to the blog
            article.key.delete()

            # the cheater's way to give DB time to update
            time.sleep(0.1)
            return self.redirect("/blog")

        elif action == "unlike":
            # authorization not really necessary as we are checking
            # the current user against existing likes by said user

            # run through the existing likes and remove this user
            keys = []
            for item in article.likekeys:
                if self.user.key != item:
                    keys.append(self.user.key)

            # store the updated likelist in the article
            article.likekeys = keys
            article.put()

            # the cheater's way to give DB time to update
            time.sleep(0.1)
            self.redirect("/blog/%d" % article_id)

        elif action == "like":
            # make sure we are logged in as someone *other* than article owner
            self.authorize()

            if self.user.key.id() == author_id:
                self.redirect("/blog/%d" % article_id)
            else:
                if self.user.key not in article.likekeys:
                    article.likekeys.append(self.user.key)
                    article.put()

                # the cheater's way to give DB time to update
                time.sleep(0.1)
                self.redirect("/blog/%d" % article_id)


class UpdateArticlePage(Handler):
    def post(self):
        # grab the article's original info
        article_id = int(self.request.get("articlekey"))
        article = Article.fetch(article_id)

        # if the article doesn't exist, get out of here
        if not article:
            return self.redirect("/notfound")

        author_id = article.author.key.id()

        # make sure we are logged in as the article owner
        self.authorize(author_id)

        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            article.subject = subject
            article.content = content
            article.put()

            # the cheater's way to give DB time to update
            time.sleep(0.1)
            return self.redirect("/blog/%d" % article_id)
        else:
            error = "Please fill out both fields!"
            self.render(
                "article-edit.html",
                authorkey=author_id,
                articlekey=article_id,
                subject=subject,
                content=content,
                error=error)


class NewArticlePage(Handler):
    def show_page(self, subject="", content="", error=""):
        self.render(
            "article-new.html", subject=subject, content=content, error=error)

    def get(self):
        # make sure we are logged in
        self.authorize()
        self.show_page()

    def post(self):
        # make sure we are logged in
        self.authorize()

        subject = self.request.get("subject")
        content = self.request.get("content")
        authorkey = ndb.Key(User, int(self.request.get(
            "author"))) if self.request.get("author").isdigit() else None

        if subject and content and authorkey:
            article = Article(
                subject=subject, content=content, authorkey=authorkey)
            article.put()

            new_id = article.key.integer_id()

            # the cheater's way to give DB time to update
            time.sleep(0.1)
            self.redirect("/blog/%s" % new_id)
        else:
            error = "Please fill out both fields!"
            self.show_page(subject, content, error)


class LoginPage(Handler):
    def get(self):
        if self.user:
            return self.redirect("/dashboard")
        self.render("login.html")

    def post(self):
        if self.user:
            return self.redirect("/dashboard")

        username = self.request.get("username")
        password = self.request.get("password")

        user = User.valid_credentials(username, password)
        if user:
            self.login(user)
            self.redirect("/dashboard")
        else:
            error = "Invalid credentials."
            self.render("login.html", username=username, error=error)


class LogoutPage(Handler):
    def get(self):
        self.logout()
        self.redirect("/login")


class RegistrationPage(Handler):
    def get(self):
        if self.user:
            return self.redirect("/dashboard")
        self.render("register.html")

    def post(self):
        if self.user:
            return self.redirect("/dashboard")

        success = True

        username = self.request.get("username")
        email = self.request.get("email")
        password = self.request.get("password")
        verify = self.request.get("verify")

        params = {"username": username, "email": email}

        # validate input
        if not utilities.is_username(username):
            params["u_error"] = "Invalid username."
            success = False

        if email != "" and not utilities.is_email(email):
            params["e_error"] = "Invalid email."
            success = False

        if not utilities.is_password(password):
            params["p_error"] = "Invalid password."
            success = False
        elif password != verify:
            params["v_error"] = "Passwords do not match."
            success = False

        # make sure this username isn't already being used
        if User.lookup_username(username):
            params["u_error"] = "Username already exists."
            success = False

        if success:
            # create a new user
            user = User.register(username, password, email)

            # log in with our new user
            self.login(user)
            self.redirect("/dashboard")
        else:
            self.render("register.html", **params)


app = webapp2.WSGIApplication(
    [
        ('/?', BlogPage),
        ('/dashboard/?', DashboardPage),
        ('/blog/([0-9]+)/?', SinglePage),
        ('/blog/([a-zA-Z0-9_-]+)/?', BlogPage),
        ('/blog/?', BlogPage),
        ('/new-article/?', NewArticlePage),
        ('/edit-article/?', EditArticlePage),
        ('/update-article/?', UpdateArticlePage),
        ('/new-comment/?', NewCommentPage),
        ('/edit-comment/?', EditCommentPage),
        ('/update-comment/?', UpdateCommentPage),
        ('/register/?', RegistrationPage),
        ('/login/?', LoginPage),
        ('/logout/?', LogoutPage),
        ('/unauthorized/?', UnauthorizedPage),
        ('/notfound/?', NotFoundPage),
    ],
    debug=True)
