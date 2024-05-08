import os, psycopg
from psycopg.rows import dict_row
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

PORT=8501 

load_dotenv()
db_url = os.environ.get("DB_URL")

conn = psycopg.connect(db_url, autocommit=True, row_factory=dict_row)
app = Flask(__name__)
CORS(app) 
app.config['JSON_AS_ASCII'] = False


@app.route("/todos", methods=["GET", "POST"])
def handle_todos():
    if request.method == "GET":
        
        api_key = request.headers.get("Authorization")

        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT todo.id, todo.title, todo.done, category.category_name
                FROM todo
                JOIN category ON todo.category_id = category.id
                WHERE todo.user_id = (SELECT id FROM users WHERE api_key = %s)
            """, (api_key,))
            rows = cur.fetchall()

        
        todos = []
        for row in rows:
            todo_item = {
                "id": row['id'],
                "title": row['title'],
                "done": row['done'],
                "category_name": row['category_name']
            }
            todos.append(todo_item)

        
        return jsonify(todos)
    
    elif request.method == "POST":
        
        api_key = request.headers.get("Authorization")
        request_body = request.get_json()
        title = request_body.get("title")
        category_id = request_body.get("category_id")
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO todo (user_id, category_id, title, done)
                VALUES (
                    (SELECT id FROM users WHERE api_key = %s), %s, %s, false
                )
                RETURNING id
            """, (api_key, category_id, title))
            row = cur.fetchone()
            todo_id = row['id']
            return {
                "msg": "En ny task lagrad",
                "id": todo_id
            }

@app.route("/todos/<int:id>", methods=["PATCH", "DELETE"])
def update_or_delete_todo(id):
    if request.method == "PATCH":
        
        status = True  
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE todo
                SET done = %s
                WHERE id = %s
            """, (status, id))
        return {
            "msg": "Markerad som done",
            "id": id
        }
    elif request.method == "DELETE":
        
        with conn.cursor() as cur:
            cur.execute("DELETE FROM todo WHERE id = %s", (id,))
        return {
            "msg": "Tasken raderad", 
            "id": id
        }   


        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True, ssl_context=(
        '/etc/letsencrypt/fullchain.pem', 
        '/etc/letsencrypt/privkey.pem'
    ))


