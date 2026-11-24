import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Turn = {message:string; reply:string; outcome:string; reference:string|null; trace:{tool:string;result:string}[]};
type Scenario = {name:string; expected:string; turns:Turn[]};
type Report = Record<"before" | "after", {summary:{correct:number;scenarios:number};scenarios:Scenario[]}>;

function App() {
  const [report,setReport] = useState<Report>();
  const [error,setError] = useState("");
  const [version,setVersion] = useState<"before"|"after">("after");
  const [scenario,setScenario] = useState(0);
  const [step,setStep] = useState(1);
  const [live,setLive] = useState(false);
  const [turns,setTurns] = useState<Turn[]>([]);
  const [message,setMessage] = useState("");
  const [busy,setBusy] = useState(false);
  useEffect(() => { fetch("./replay.json").then(r => {
    if (!r.ok) throw Error();
    return r.json() as Promise<Report>;
  }).then(setReport).catch(() => setError("Replay could not be loaded.")); }, []);
  const current = report?.[version].scenarios[scenario];
  const visible = live ? turns : current?.turns.slice(0,step) ?? [];
  async function send() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/turn", {method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message,previous:turns.at(-1)?.reference})});
      if (!response.ok) throw Error();
      const turn = await response.json() as Turn;
      setTurns([...turns,turn]); setMessage("");
    } catch { setError("Live service could not be reached. You can retry or switch to replay."); }
    finally { setBusy(false); }
  }
  return <main>
    <a href="https://martaforjaz.github.io/#transaction-resolution">Marta Forjaz · Portfolio</a>
    <h1>Transaction Resolution Agent</h1>
    <p>Replay synthetic support conversations and inspect how each action was verified.</p>
    {["127.0.0.1","localhost"].includes(location.hostname) && <button onClick={() => {setLive(!live);setError("");}}>{live ? "Open recorded replay" : "Connect to local Java service"}</button>}
    {!live && report && current && <div className="controls">
      <label>Version <select value={version} onChange={e=>setVersion(e.target.value==="before"?"before":"after")}><option value="before">Before reconciliation</option><option value="after">After reconciliation</option></select></label>
      <label>Scenario <select value={scenario} onChange={e=>{setScenario(Number(e.target.value));setStep(1);}}>{report[version].scenarios.map((s,i)=><option key={s.name} value={i}>{s.name}</option>)}</select></label>
      <button disabled={step<=1} onClick={()=>setStep(step-1)}>Back</button>
      <button disabled={step>=current.turns.length} onClick={()=>setStep(step+1)}>Next turn</button>
      <span>{step}/{current.turns.length} turns · {report[version].summary.correct}/{report[version].summary.scenarios} cases passed</span>
    </div>}
    {error && <p role="alert">{error}</p>}
    <div className="panels"><section><h2>Conversation</h2>{visible.map((turn,i)=><article key={i}><p><strong>Customer</strong><br/>{turn.message}</p><p><strong>Agent</strong><br/>{turn.reply}</p></article>)}
      {live && <form onSubmit={e=>{e.preventDefault();void send();}}><label>Message <input value={message} onChange={e=>setMessage(e.target.value)} required maxLength={1000}/></label><button disabled={busy}>Send</button></form>}
    </section><section><h2>Action log</h2>{visible.map((turn,i)=><article key={i}><strong>Turn {i+1} · {turn.outcome.replaceAll("_"," ")}</strong><ul>{turn.trace.map((entry,j)=><li key={j}>{entry.tool} · {entry.result}</li>)}{!turn.trace.length && <li>No tools called</li>}</ul></article>)}</section></div>
  </main>;
}
createRoot(document.getElementById("root")!).render(<App />);
