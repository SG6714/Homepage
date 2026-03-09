from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Temporary data store
tasks = ["Learn Flask", "Build a cool app", "Drink coffee"]

@app.route('/')
def index():
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    task = request.json.get('task')
    if task:
        tasks.append(task)
        return jsonify({"success": True, "task": task}), 200
    return jsonify({"success": False}), 400

if __name__ == '__main__':
    app.run(debug=True)
