from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from app.models import db, User
from app.utils.auth import require_login

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
        else:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

        if not username or not email or not password:
            msg = "Username, email, and password are required."
            if request.is_json:
                return jsonify({"error": "Bad Request", "message": msg}), 400
            flash(msg, "danger")
            return render_template('register.html')

        if len(password) < 6:
            msg = "Password must be at least 6 characters long."
            if request.is_json:
                return jsonify({"error": "Bad Request", "message": msg}), 400
            flash(msg, "danger")
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            msg = "Username is already registered."
            if request.is_json:
                return jsonify({"error": "Conflict", "message": msg}), 409
            flash(msg, "danger")
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            msg = "Email address is already registered."
            if request.is_json:
                return jsonify({"error": "Conflict", "message": msg}), 409
            flash(msg, "danger")
            return render_template('register.html')

        new_user = User(
            username=username,
            email=email,
            api_key=User.generate_api_key()
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['username'] = new_user.username

        if request.is_json:
            return jsonify({
                "message": "User registered successfully.",
                "user": new_user.to_dict()
            }), 201

        flash("Registration successful! Welcome.", "success")
        return redirect(url_for('web.dashboard'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '')
        else:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

        user = User.query.filter(
            (User.username == username) | (User.email == username.lower())
        ).first()

        if not user or not user.check_password(password):
            msg = "Invalid username/email or password."
            if request.is_json:
                return jsonify({"error": "Unauthorized", "message": msg}), 401
            flash(msg, "danger")
            return render_template('login.html')

        session['user_id'] = user.id
        session['username'] = user.username

        if request.is_json:
            return jsonify({
                "message": "Login successful.",
                "user": user.to_dict()
            }), 200

        flash("Logged in successfully.", "success")
        next_page = request.args.get('next')
        return redirect(next_page or url_for('web.dashboard'))

    return render_template('login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    if request.is_json:
        return jsonify({"message": "Logged out successfully."}), 200
    flash("You have been logged out.", "info")
    return redirect(url_for('web.index'))

@auth_bp.route('/api/user/regenerate-key', methods=['POST'])
@require_login
def regenerate_api_key():
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.api_key = User.generate_api_key()
    db.session.commit()

    if request.is_json:
        return jsonify({
            "message": "API key regenerated successfully.",
            "api_key": user.api_key
        }), 200

    flash("Your API key has been regenerated.", "success")
    return redirect(url_for('web.dashboard'))
