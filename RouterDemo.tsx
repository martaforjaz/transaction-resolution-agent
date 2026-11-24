import { useState } from "react";
import { consent, diagnose, verify } from "./router";
import type { Scenario } from "./router";

export function RouterDemo() {
  const [scenario, setScenario] = useState<Scenario>("local");
  const [fails, setFails] = useState(false);
  const [state, setState] = useState(() => diagnose("local"));
  return <main>
    <a href="../#device-troubleshooting">Marta Forjaz · Portfolio</a>
    <h1>Device Troubleshooting Agent</h1>
    <p>Simulate a router report and follow the diagnosis, consent and connectivity check.</p>
    <div className="controls">
      <label>Scenario <select value={scenario} onChange={e => {
        const next = e.target.value as Scenario;
        setScenario(next); setState(diagnose(next));
      }}>
        <option value="local">Router DNS failure</option><option value="carrier">Provider outage</option><option value="healthy">Healthy router</option>
      </select></label>
      <label><input type="checkbox" checked={fails} onChange={e=>setFails(e.target.checked)}/> Simulate failed recovery</label>
      <button onClick={()=>setState(diagnose(scenario))}>Reset</button>
    </div>
    <div className="panels">
      <section><h2>Conversation</h2><article><strong>Customer</strong><p>My device connects to Wi-Fi, but I cannot get online.</p></article>
        <article aria-live="polite"><strong>Agent</strong><p>{state.result}</p></article>
        {state.stage === "consent" && <div className="controls"><button onClick={()=>setState(old=>consent(old,true))}>Allow restart</button><button onClick={()=>setState(old=>consent(old,false))}>Decline</button></div>}
        {state.stage === "reboot" && <button onClick={()=>setState(old=>verify(old,!fails))}>Run connectivity check</button>}
      </section>
      <section><h2>Telemetry and actions</h2><p>Required customer steps: {state.steps}</p><ol>{state.trace.map(event=><li key={event}>{event}</li>)}</ol></section>
    </div>
  </main>;
}
