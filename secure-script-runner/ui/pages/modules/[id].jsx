import { useRouter } from 'next/router'
import useSWR from 'swr'
import { useState } from 'react'
const API = process.env.NEXT_PUBLIC_API_BASE
const headers = { 'X-Demo-User':'analyst@example.com', 'Content-Type':'application/json' }
const fetcher = (url) => fetch(url, { headers }).then(r => r.json())

export default function ModulePage(){
  const router = useRouter()
  const { id } = router.query
  const { data: modules } = useSWR(id ? `${API}/api/modules` : null, fetcher)
  const mod = modules?.find(m=>m.id==id)
  const [execId, setExecId] = useState(null)
  const [logs, setLogs] = useState([])

  async function run(){
    const body = { parameters:{ db_name: 'dev', retention_days: 7, notify_email: 'analyst@example.com', backup_key: 'super-secret' } }
    const res = await fetch(`${API}/api/modules/${id}/execute`, { method:'POST', headers, body: JSON.stringify(body) })
    const ex = await res.json()
    setExecId(ex.id)
    pollLogs(ex.id, 0)
  }

  async function pollLogs(exId, seq){
    const res = await fetch(`${API}/api/modules/exec/${exId}/logs?sinceSeq=${seq}`, { headers })
    const chunks = await res.json()
    if(chunks.length){
      setLogs(prev => [...prev, ...chunks])
      const nextSeq = chunks[chunks.length-1].sequence_no + 1
      setTimeout(()=>pollLogs(exId, nextSeq), 1000)
    } else {
      setTimeout(()=>pollLogs(exId, seq), 1500)
    }
  }

  return (
    <main style={{padding:20,fontFamily:'sans-serif'}}>
      <h1>{mod?.name}</h1>
      <button onClick={run}>Run</button>
      {execId && <p>Execution ID: {execId}</p>}
      <pre style={{background:'#111',color:'#0f0',padding:10,height:300,overflow:'auto'}}>
        {logs.map(l => l.text).join('')}
      </pre>
    </main>
  )
}
