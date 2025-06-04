from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import os
from dotenv import load_dotenv
from instagrapi import Client
import json

app = Flask(__name__)
# For Vercel, we'll use a static secret key
app.secret_key = 'your-secret-key-here'  # Replace with a secure secret key
load_dotenv()

class LoginForm(FlaskForm):
    username = StringField('Instagram Username', validators=[DataRequired()])
    password = PasswordField('Instagram Password', validators=[DataRequired()])
    submit = SubmitField('Analyze Followers')

def get_instagram_data(username, password):
    cl = Client()
    try:
        cl.login(username, password)
        user_id = cl.user_id
        
        # Get followers and following
        followers = cl.user_followers(user_id)
        following = cl.user_following(user_id)
        
        # Find users you follow who don't follow you back
        non_followers = {
            str(user_id): {
                "username": user_info.username,
                "full_name": user_info.full_name,
                "profile_pic_url": user_info.profile_pic_url
            }
            for user_id, user_info in following.items()
            if user_id not in followers
        }
        
        return {
            "success": True,
            "data": non_followers,
            "total": len(non_followers)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        result = get_instagram_data(form.username.data, form.password.data)
        if result["success"]:
            return render_template(
                'results.html',
                non_followers=result["data"],
                total=result["total"]
            )
        else:
            flash(f'Error: {result["error"]}', 'error')
            return redirect(url_for('index'))
    return render_template('index.html', form=form)

# This is needed for Vercel
app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))

# For local development
if __name__ == '__main__':
    app.run(debug=True) 