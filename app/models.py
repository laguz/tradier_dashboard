from flask_login import UserMixin
from app import bcrypt

class User(UserMixin):
    """
    User model for interacting with user documents in MongoDB.
    This class inherits from UserMixin to get the properties required by Flask-Login.
    """
    def __init__(self, user_data):
        """
        Creates a User object from a dictionary (a MongoDB document).
        """
        self.data = user_data
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.tradier_api_key = user_data.get('tradier_api_key') # Optional
        self.tradier_account_number = user_data.get('tradier_account_number') # Optional
        self.password_hash = user_data.get('password')
        
        # Flask-Login requires the user's ID to be stored in self.id
        # The ID from MongoDB (_id) must be converted to a string.
        self.id = str(user_data.get('_id'))

    def check_password(self, password):
        """
        Checks if a given plaintext password matches the stored hash.
        
        Args:
            password (str): The password to check.
            
        Returns:
            bool: True if the password matches, False otherwise.
        """
        return bcrypt.check_password_hash(self.password_hash, password)