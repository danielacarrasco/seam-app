import os

from dotenv import load_dotenv
from flask import Flask

from web.routes import home, makes, measurements, patterns, projects, stash

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    app.register_blueprint(home.bp, url_prefix="/")
    app.register_blueprint(projects.bp, url_prefix="/projects")
    app.register_blueprint(stash.bp, url_prefix="/stash")
    app.register_blueprint(patterns.bp, url_prefix="/patterns")
    app.register_blueprint(makes.bp, url_prefix="/makes")
    app.register_blueprint(measurements.bp, url_prefix="/measurements")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", "5000")))
