from flask import Flask, render_template, redirect, url_for, flash, Blueprint
from flask_login import current_user, login_user, login_required
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from . import db
from .models import User, OAuth
import os

google_blueprint = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID', 'YOUR CLIENT ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', 'YOUR CLIENT SECRET'),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user)
)

@oauth_authorized.connect_via(google_blueprint)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in.", category="error")
        return
    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        msg = "Failed to fetch user info."
        flash(msg, category="error")
        return

    google_name = resp.json()["name"]
    google_user_id = resp.json()["id"]
    google_email = resp.json()["email"]

    query = OAuth.query.filter_by(
        provider=blueprint.name, provider_user_id=google_user_id
    )
    try:
        oauth = query.one()
    except NoResultFound:
        google_user_login = google_name

        oauth = OAuth(
            provider=blueprint.name,
            provider_user_id=google_user_id,
            provider_user_login=google_user_login,
            token=token,
        )

    if current_user.is_anonymous:
        if oauth.user:
            login_user(oauth.user)
        else:
            user = User(username=google_name, email=google_email)

            oauth.user = user
            db.session.add_all([user, oauth])
            db.session.commit()
            login_user(user)
    else:
        if oauth.user:
            if current_user != oauth.user:
                url = url_for("auth.merge", username=oauth.user.username)
                return redirect(url)
        else:
            oauth.user = current_user
            db.session.add(oauth)
            db.commit()

    return redirect(url_for("main.profile"))


@oauth_error.connect_via(google_blueprint)
def google_error(blueprint, message, response):
    msg = ("OAuth error from {name}! " "message={message} response={response}").format(
        name=blueprint.name, message=message, response=response
    )
    flash(msg, category="error")
