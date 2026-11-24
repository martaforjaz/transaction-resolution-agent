export const scenarios = {
  local: {wan: true, outage: false, dns: false},
  carrier: {wan: false, outage: true, dns: false},
  healthy: {wan: true, outage: false, dns: true},
};

export type Scenario = keyof typeof scenarios;
export type State = {
  stage: "consent" | "reboot" | "done";
  steps: number;
  result: string;
  trace: string[];
};

export function diagnose(scenario: Scenario): State {
  const {wan, outage, dns} = scenarios[scenario];
  const trace = [`WAN ${wan ? "up" : "down"} · DNS ${dns ? "reachable" : "unreachable"}`,
    outage ? "Provider outage reported" : "No provider outage reported"];
  if (outage || !wan) return {stage:"done", steps:0, result:"Escalated to provider. No restart requested.", trace};
  if (dns) return {stage:"done", steps:0, result:"Connectivity verified. No restart needed.", trace};
  return {stage:"consent", steps:1, result:"The router DNS resolver is unresponsive. May I restart it?", trace};
}

export function consent(state: State, allowed: boolean): State {
  if (state.stage !== "consent") return state;
  return allowed
    ? {stage:"reboot", steps:state.steps, result:"Restart requested. Waiting for the connectivity check.", trace:[...state.trace,"Consent recorded","Restart dispatched"]}
    : {stage:"done", steps:state.steps, result:"Restart declined. Escalated to support.", trace:[...state.trace,"Consent declined"]};
}

export function verify(state: State, reachable: boolean): State {
  if (state.stage !== "reboot") return state;
  return {...state, stage:"done", result:reachable ? "Connection restored and verified." : "Connection still unavailable. Escalated to support.",
    trace:[...state.trace, reachable ? "Post-restart DNS probe passed" : "Post-restart DNS probe failed"]};
}
