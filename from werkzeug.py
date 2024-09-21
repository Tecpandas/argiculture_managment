from werkzeug.security import check_password_hash

def verify_password(stored_hash, provided_password):
    """
    Verifies a password against a stored hash.
    
    :param stored_hash: The hashed password from the database.
    :param provided_password: The plain-text password provided by the user.
    :return: True if the password is correct, False otherwise.
    """
    return check_password_hash(stored_hash, provided_password)

# Example usage
stored_hash = 'farm123 ' # Replace with actual stored hash
provided_password = 'farm123'

if verify_password(stored_hash, provided_password):
    print("Password is correct!")
else:
    print("Password is incorrect!")
