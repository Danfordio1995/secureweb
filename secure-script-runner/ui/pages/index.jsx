import { useEffect, useState } from "react";
import useSWR from 'swr'
const API = process.env.NEXT_PUBLIC_API_BASE
const fetcher = (url) => fetch(url, { headers: { 'X-Demo-User':'analyst@example.com' } }).then(r => r.json())

export default function Home(){
  const [modules, setModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch modules from API
  useEffect(() => {
    fetch("http://localhost:8080/modules", {
      headers: { "X-Demo-User": "analyst@example.com" }
    })
      .then(res => res.json())
      .then(data => setModules(data));
  }, []);

  // Fetch executions for selected module
  useEffect(() => {
    if (selectedModule) {
      fetch(`http://localhost:8080/executions?module_id=${selectedModule.id}`, {
        headers: { "X-Demo-User": "analyst@example.com" }
      })
        .then(res => res.json())
        .then(data => setExecutions(data));
    }
  }, [selectedModule]);

  // Run module (simplified)
  const runModule = async (id) => {
    setLoading(true);
    await fetch(`http://localhost:8080/executions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Demo-User": "analyst@example.com"
      },
      body: JSON.stringify({ module_id: id, params: {} }) // Add params as needed
    });
    setLoading(false);
    setSelectedModule(modules.find(m => m.id === id)); // Refresh executions
  };

  return (
    <main style={{padding:20,fontFamily:'sans-serif'}}>
      <h1>Secure Script Runner</h1>
      <p>Logged in as <b>analyst@example.com</b> (demo header)</p>
      <h2>Modules</h2>
      <ul>
        {modules.map(m => (
          <li key={m.id}>
            <b>{m.name}</b> - {m.description}
            <button onClick={() => setSelectedModule(m)}>View</button>
            <button onClick={() => runModule(m.id)} disabled={loading}>Run</button>
          </li>
        ))}
      </ul>
      {selectedModule && (
        <div style={{ marginTop: 32 }}>
          <h3>Executions for {selectedModule.name}</h3>
          <ul>
            {executions.map(e => (
              <li key={e.id}>
                Run at {e.created_at} - Status: {e.status}
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  )
}
