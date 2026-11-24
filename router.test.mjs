import assert from 'node:assert/strict';
import { consent, diagnose, verify } from './router.ts';

const local = diagnose('local');
assert.equal(local.steps, 1);
assert.equal(verify(local, true), local);
const reboot = consent(local, true);
assert.equal(consent(reboot, true), reboot);
assert.match(verify(reboot, true).result, /restored and verified/);
assert.match(verify(reboot, false).result, /still unavailable/);
assert.equal(consent(local, false).trace.includes("Restart dispatched"), false);
const carrier = diagnose('carrier');
assert.equal(carrier.steps, 0);
assert.equal(consent(carrier, true), carrier);
assert.equal(diagnose('healthy').steps, 0);
console.log('Router checks passed: recovery, failed recovery, duplicate restart, declined consent, outage, healthy.');
