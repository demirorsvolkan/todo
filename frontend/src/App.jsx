import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "/api";

function App() {
  const [todos, setTodos] = useState([]);
  const [title, setTitle] = useState("");

  const loadTodos = async () => {
    const response = await fetch(`${API_URL}/todos`);
    const data = await response.json();
    setTodos(data);
  };

  useEffect(() => {
    loadTodos();
  }, []);

  const addTodo = async () => {
    if (!title.trim()) return;

    await fetch(`${API_URL}/todos`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: title.trim(),
        isCompleted: false,
      }),
    });

    setTitle("");
    loadTodos();
  };

  const deleteTodo = async (id) => {
    await fetch(`${API_URL}/todos/${id}`, {
      method: "DELETE",
    });

    loadTodos();
  };

  const toggleTodo = async (todo) => {
    await fetch(`${API_URL}/todos/${todo.id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: todo.title,
        isCompleted: !todo.isCompleted,
      }),
    });

    loadTodos();
  };

  return (
    <div className="app">
      <h1>Todo App</h1>

      <div className="add-todo">
        <input
          type="text"
          placeholder="Todo yaz..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") addTodo();
          }}
        />

        <button onClick={addTodo}>Ekle</button>
      </div>

      <ul>
        {todos.map((todo) => (
          <li key={todo.id}>
            <label>
              <input
                type="checkbox"
                checked={todo.isCompleted}
                onChange={() => toggleTodo(todo)}
              />

              <span className={todo.isCompleted ? "completed" : ""}>
                {todo.title}
              </span>
            </label>

            <button onClick={() => deleteTodo(todo.id)}>Sil</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;