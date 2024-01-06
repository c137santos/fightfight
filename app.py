import os

from flask import jsonify

from torneios import create_app

DEFAULT_CONFIG_MODE = "development"

app = create_app(os.getenv("CONFIG_MODE") or DEFAULT_CONFIG_MODE)


@app.get("/")
def home():
    return jsonify({"message": "Hello World!"}), 200


if __name__ == "__main__":
    app.run()
