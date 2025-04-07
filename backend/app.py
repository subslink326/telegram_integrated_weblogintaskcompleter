from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from task_manager import TaskManager
import os
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Use existing TaskManager instead of creating a new Telegram bot instance
task_manager = TaskManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = task_manager.get_all_tasks()
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.json
    task = task_manager.create_task(data)
    return jsonify(task), 201

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    task = task_manager.update_task(task_id, data)
    return jsonify(task)

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    task_manager.delete_task(task_id)
    return '', 204

@app.route('/api/task-status/<task_id>')
def get_task_status(task_id):
    status = task_manager.get_task_status(task_id)
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
