from app import create_app

# The app instance is created by the factory function in app/__init__.py
app = create_app()

if __name__ == "__main__":
    # Runs the app on port 5003 in debug mode for development
    app.run(debug=True, port=5003)