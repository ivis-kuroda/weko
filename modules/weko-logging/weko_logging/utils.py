from flask_login import current_user

def get_current_user():
    return current_user

def print_user_id():
    user = get_current_user()
    print(f"userid={user.id}")

def print_user():
    user = get_current_user()
    print(f"user={user}")

