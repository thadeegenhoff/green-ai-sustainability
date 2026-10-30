const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const flow = JSON.parse(fs.readFileSync(path.join(__dirname, '../nodered/flows.json'), 'utf8'));
const source = flow.find(node => node.type === 'function' && node.name === 'Daten-Transformieren').func;
const transform = new Function('msg', 'Buffer', source);

function parse(topic, payload) { return transform({topic, payload}, Buffer); }
for (const value of [null, undefined, '', ' ', false, 'not-a-number']) {
    assert.equal(parse('shellies/probe/relay/0/power', value), null);
}
for (const value of [0, '0']) {
    const result = parse('shellies/probe/relay/0/power', value);
    assert.equal(result.payload[0].power_w, 0);
}
const valid = parse('probe/status/switch:0', JSON.stringify({apower: 17.5, voltage: 230}));
assert.equal(valid.payload[0].power_w, 17.5);
assert.equal(valid.payload[1].device, 'probe');
assert.equal(parse('probe/status/switch:0', '{"apower":null}'), null);
assert.equal(parse('unrelated/topic', '{broken'), null);
assert.equal(parse('shellies/probe/relay/0/energy', '60').payload[0].energy_wh, 1);
console.log('Flow checks passed: missing values stay absent; real zero and Shelly readings are retained.');
