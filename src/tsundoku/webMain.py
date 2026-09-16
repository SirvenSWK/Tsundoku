from flask import Flask, render_template, request

from groq import Groq, AuthenticationError

from tsundoku.tools import organizer

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/organize", methods=["POST"])
def organize():
    text = request.form["taskText"].strip()
    apiKey = request.form["apiKey"].strip()

    if not text:
        return render_template(
            "home.html",
            message="Tell me what's up first."
        )

    if not apiKey:
        return render_template(
            "home.html",
            message="Add your Groq API key first."
        )

    try:
        client = Groq(api_key=apiKey)

        result = organizer.organizeWithLlm(
            text,
            client=client
        )

    except AuthenticationError:
        return render_template(
            "home.html",
            message="That Groq API key doesn't appear to be valid."
        )

    return render_template(
        "home.html",
        result=result
    )


if __name__ == "__main__":
    app.run()