import os

import click
from flask import Flask, render_template


from kkblog.extensions import bootstrap, db, ckeditor, mail, moment,login_manager,csrf
from kkblog.settings import config
from kkblog.models import Admin, Post, Category, Comment, Link
from kkblog.blueprints.blog import blog_bp
from kkblog.blueprints.auth import auth_bp
from kkblog.blueprints.admin import admin_bp
from flask_login import current_user

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')


    app = Flask("kkapp")
    app.config.from_object(config[config_name])

    register_logging(app)# 注册日志处理器
    register_extensions(app)# 注册扩展（扩展初始化）
    register_blueprints(app)# 注册蓝图
    register_commands(app)# 注册自定义shell命令
    register_errors(app)# 注册错误处理视图函数
    register_shell_context(app)# 注册shell上下文处理函数
    register_template_context(app)# 注册模板上下文处理函数
    return app


def register_logging(app):
    pass


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    ckeditor.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)



def register_blueprints(app):
    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp,url_prefix='/admin')


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db)


def register_template_context(app):
    @app.context_processor
    def make_shell_context():
        categories = Category.query.order_by(Category.name).all()
        link = Link.query.order_by(Link.name).all()
        admin = Admin.query.first()

        sqll = "SELECT DISTINCT strftime('%Y', timestamp)  as year from post"
        sql_year_count = "SELECT count(*) from post GROUP BY strftime('%Y', timestamp)"
        years = list(db.session.execute(sqll))
        year_counts = list(db.session.execute(sql_year_count))
        a=sorted([int(k[0]) for k in years],reverse=True)
        b=sorted([int(v[0]) for v in year_counts],reverse=True)
        years_list = list(zip(a,b))

        if current_user.is_authenticated:
            unread_comments = Comment.query.filter_by(reviewed=False).count()
        else:
            unread_comments = None

        return dict(db=db, admin=admin,links=link, categories=categories, unread_comments=unread_comments,Post=Post, Category=Category,Comment=Comment,years_list=years_list)




def register_errors(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500



def register_commands(app):
    @app.cli.command()
    @click.option('--category', default=10, help='Quantity of categories, default is 10.')
    @click.option('--post', default=50, help='Quantity of posts, default is 50.')
    @click.option('--comment', default=500, help='Quantity of comments, default is 500.')
    def forge(category, post, comment):
        """Generate fake data."""
        from kkblog.fakes import fake_admin, fake_categories, fake_posts, fake_comments, fake_links

        db.drop_all()
        db.create_all()

        click.echo('Generating the administrator...')
        fake_admin()

        click.echo('Generating %d categories...' % category)
        fake_categories(category)

        click.echo('Generating %d posts...' % post)
        fake_posts(post)

        click.echo('Generating %d comments...' % comment)
        fake_comments(comment)

        click.echo('Generating links...')
        fake_links()

        click.echo('Done.')

    @app.cli.command()
    @click.option('--username', prompt=True, help='The username used to login.')
    @click.option('--password', prompt=True, hide_input=True,
                  confirmation_prompt=True, help='The password used to login.')
    def init(username, password):
        """Building Bluelog, just for you."""

        click.echo('Initializing the database...')
        db.create_all()

        admin = Admin.query.first()
        print(admin)
        if admin is not None:
            click.echo('The administrator already exists, updating...')
            admin.username = username
            admin.set_password(password)
        else:
            click.echo('Creating the temporary administrator account...')
            admin = Admin(
                username=username,
                blog_title='Alchemy&Z',
                blog_sub_title="Tis true without lying, certain & most true.",
                name='Talleyran',
                about='Anything about you.'
            )
            admin.set_password(password)
            db.session.add(admin)

        category = Category.query.first()
        if category is None:
            click.echo('Creating the default category...')
            category = Category(name='Default')
            db.session.add(category)

        db.session.commit()
        click.echo('Done.')


if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0")