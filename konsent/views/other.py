from sqlalchemy import and_
from flask_login import current_user, login_required
from flask import (Blueprint, render_template, flash, session,
                   redirect, abort, request, url_for)

from konsent import union_required, REQUIRED_VOTES_DIVISOR
from konsent.models import db, Union, Post, Vote, Comment
from konsent.forms import ArticleForm

view = Blueprint('other', __name__)


# view a single solution that's been confirmed (phase 4)
@view.route('/completed/post/<int:post_id>', methods=['GET'])
@login_required
@union_required
def post_completed(post_id):
    # find posts
    post = Post.query.get(post_id)
    # TODO: Check that the post is in the correct Union, return a
    # proper error if not
    if post.union_id != current_user.union_id:
        post = None

    return render_template('post.html', post=post,
        comments=post.list_comments(current_user.username), phase=4)



# new post
@view.route('/new-post', methods=['GET', 'POST'])
@login_required
@union_required
def new_post():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        if request.form['unit'] == 'minutes':
            resting_time = form.resting_time.data * 60
        elif request.form['unit'] == 'hours':
            resting_time = form.resting_time.data * 60 * 60
        elif request.form['unit'] == 'days':
            resting_time = form.resting_time.data * 60 * 60 * 24
        else:
            error = 'An error occurred while trying to submit your post'
            return render_template('index.html', error=error)

        if resting_time < 3000:
            flash('Resting time cannot be less than 50 minutes', 'error')
            return redirect(url_for('other.new_post'))

        # LIGHT THE FUSES, COMRADES!!!
        post = Post(title, body, current_user.union_id, current_user.id, resting_time)
        db.session.add(post)
        db.session.commit()

        flash('Your post have been published', 'success')
        return redirect(url_for('phase1.get'))
    return render_template('new-post.html', form=form)


# blocked solutions
@view.route('/vetoed')
@login_required
@union_required
def vetoed():
    posts = Post.query.filter(
        and_(
            Post.union_id == current_user.union_id,
            Post.vetoed_by_id != None
        )
    ).all()

    if posts:
        return render_template('vetoed.html', posts=posts)
    else:
        return render_template('vetoed.html', msg=NO_RESULTS_ERROR)


# finished solutions
@view.route('/completed')
@login_required
@union_required
def completed():
    # Find posts
    posts = Post.query.filter(
        and_(
            Post.phase == 4,
            Post.union_id == current_user.union_id,
            Post.vetoed_by_id == None
        )
    ).all()

    if posts:
        return render_template('completed.html', posts=posts)
    else:
        return render_template('completed.html', msg=NO_RESULTS_ERROR)


@view.route('/about')
def about():
    return render_template('about.html')


@view.route('/members')
@login_required
@union_required
def members():
    union = Union.query.filter(Union.id == current_user.union_id).one()
    return render_template('union-members.html', members=union.list_members())


# who voted on this post?
@view.route('/who-voted/<string:what>/<int:id>')
@login_required
@union_required
def who_voted(what, id):
    if what == 'post':
        cls = Post
    elif what == 'comment':
        cls = Comment
    else:
        abort(404)
    obj = cls.query.filter(cls.id == id).one()
    votes = obj.list_votes()
    return render_template('who-voted.html', votes=votes)
