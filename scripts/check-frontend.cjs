// Exercise the shipped frontend's functions against the real API using a minimal DOM.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const elements = new Map();
const element = id => {
  if (!elements.has(id)) elements.set(id, {innerHTML:'', textContent:'', value:'',
    classList:{add(){}, remove(){}}, addEventListener(){}});
  return elements.get(id);
};
const timers = new Set();
const context = vm.createContext({
  document:{getElementById:element},
  localStorage:{getItem(){return null},setItem(){},removeItem(){}},
  fetch:(url, options)=>fetch('http://localhost'+url, options),
  setTimeout:(fn,ms)=>{const t=setTimeout(fn,ms); t.unref(); return t},
  setInterval:(fn,ms)=>{const t=setInterval(fn,ms);timers.add(t);return t},
  clearInterval:t=>{clearInterval(t);timers.delete(t)}
});
const html = fs.readFileSync('nginx/frontend/index.html','utf8');
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
(async()=>{
 try {
  element('email').value = 'ui-'+Date.now()+'@example.com';
  element('password').value = 'Demo-password-123';
  await context.doRegister();
  await context.loadPlans();
  assert(element('plans-container').innerHTML.includes('VPS Basic'));
  await context.orderPlan(1,'VPS Basic',5);
  assert(element('order-details').innerHTML.includes('Pending Payment'));
  await context.payOrder();
  for(let i=0;i<30 && !element('order-details').innerHTML.includes('Server is ready');i++)
    await new Promise(resolve=>setTimeout(resolve,1000));
  assert(element('order-details').innerHTML.includes('Server is ready'));
  await context.loadServers();
  assert(element('servers-container').innerHTML.includes('active'));
  context.logout();
  console.log('PASS: frontend registration, catalog, order, payment, polling, servers, logout');
 } finally { for(const t of timers) clearInterval(t); }
})().catch(e=>{console.error(e);process.exitCode=1});
