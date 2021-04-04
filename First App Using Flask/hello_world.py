from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/about')
def sk():
    my_name = "Suryakant"

    return render_template('about.html', name=my_name)


app.run(debug=1)
