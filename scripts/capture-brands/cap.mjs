import { spawn } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
const S=process.argv[2];
const CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
// items.json は run.sh が app/data/partner-captures.json から作る
const ITEMS=JSON.parse(readFileSync(S+"/items.json","utf8")).filter(i=>!process.argv[3]||process.argv[3].split(",").includes(i[0]));
const PORT=9377, UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(CHROME,["--headless=new","--disable-gpu","--hide-scrollbars","--remote-debugging-port="+PORT,"--remote-allow-origins=*","--user-data-dir="+S+"/prof","--user-agent="+UA,"--lang=ja-JP","about:blank"],{stdio:"ignore"});
await sleep(2500);
let msgId=0;
function rpc(ws,method,params={},sessionId){return new Promise((res,rej)=>{const id=++msgId;const on=ev=>{let d;try{d=JSON.parse(ev.data)}catch{return}if(d.id===id){ws.removeEventListener("message",on);d.error?rej(new Error(d.error.message)):res(d.result)}};ws.addEventListener("message",on);ws.send(JSON.stringify(sessionId?{id,method,params,sessionId}:{id,method,params}))})}
const ver=await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
const ws=new WebSocket(ver.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener("open",r,{once:true}));
const out=[];
for(const [slug,name,url] of ITEMS){
  try{
    const {targetId}=await rpc(ws,"Target.createTarget",{url:"about:blank"});
    const {sessionId}=await rpc(ws,"Target.attachToTarget",{targetId,flatten:true});
    await rpc(ws,"Page.enable",{},sessionId);await rpc(ws,"Runtime.enable",{},sessionId);
    await rpc(ws,"Network.setUserAgentOverride",{userAgent:UA,acceptLanguage:"ja-JP,ja"},sessionId);
    await rpc(ws,"Emulation.setDeviceMetricsOverride",{width:1280,height:800,deviceScaleFactor:2,mobile:false},sessionId);
    rpc(ws,"Page.navigate",{url},sessionId).catch(()=>{});
    await sleep(7000);
    const t=await rpc(ws,"Runtime.evaluate",{expression:"window.scrollTo(0,0);document.title",returnByValue:true},sessionId);
    await sleep(800);
    const {data}=await rpc(ws,"Page.captureScreenshot",{format:"png",clip:{x:0,y:0,width:1280,height:800,scale:2}},sessionId);
    writeFileSync(`${S}/png/${slug}.png`,Buffer.from(data,"base64"));
    await rpc(ws,"Target.closeTarget",{targetId});
    out.push({slug,name,url,title:t.result.value}); console.log("ok",slug,t.result.value);
  }catch(e){console.log("FAIL",slug,e.message)}
}
ws.close();chrome.kill();
writeFileSync(S+"/titles"+(process.argv[3]?"-retry":"")+".json",JSON.stringify(out,null,1));
