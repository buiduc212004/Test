# src/authenticate.py
def authenticate_user(username, password):
    
    valid_users = {"user1": "pass123",
                    "admin": "admin456"}
    return valid_users.get(username) == password