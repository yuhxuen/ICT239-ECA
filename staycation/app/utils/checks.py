from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def non_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(*args, **kwargs):
        if current_user.is_authenticated and getattr(current_user, "is_admin", False):
            flash("This is a non-admin function. Please log in as a non-admin user to use this function.", "info")
            return redirect(url_for('packageController.packages'))
        return view_func(*args, **kwargs)
    return _wrapped

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            flash("Admin access required.", "warning")
            return redirect(url_for('packageController.packages'))
        return view_func(*args, **kwargs)
    return _wrapped
