"use strict";

const CATEGORY_ICONS = {
  "شروع هوش مصنوعی":"🧭","برنامه‌نویسی":"💻","اتوماسیون":"⚙️",
  "ابزارهای هوش مصنوعی":"🤖","کریپتو و پرداخت":"🪙","سایر":"📦"
};
const TRACK_ICONS = {"شروع هوشمند":"🌱","OpenClaw":"🦾","ساخت و اتوماسیون":"⚙️","ابزارهای حرفه‌ای":"🧰","آموزش‌های مستقل":"🧭"};
const TRACK_DESCRIPTIONS = {
  "شروع هوشمند":"برای کسی که می‌خواهد تصویر روشن و ساده‌ای از هوش مصنوعی داشته باشد.",
  "OpenClaw":"از نصب اولیه تا استفادهٔ حرفه‌ای از دستیار شخصی هوش مصنوعی.",
  "ساخت و اتوماسیون":"ابزارهای پایه برای ساختن، کدنویسی و خودکارکردن کارها.",
  "ابزارهای حرفه‌ای":"مهارت‌های مکمل برای استفادهٔ جدی‌تر از ابزارهای هوشمند.",
  "آموزش‌های مستقل":"آموزش‌های کاربردی که می‌توانی جداگانه دنبال کنی."
};

const STORE_KEY = "gravel-state-v2";
let catalog = [];
let activeCategory = "همه";
let audience = "شروع از صفر";
let query = new URLSearchParams(location.search).get("q") || "";
let deferredInstall = null;
const state = readState();

function readState(){
  try{return Object.assign({done:{}},JSON.parse(localStorage.getItem(STORE_KEY)||"{}"));}
  catch{return {done:{}};}
}
function saveState(){try{localStorage.setItem(STORE_KEY,JSON.stringify(state));}catch{}}
function fa(value){return String(value).replace(/\d/g,d=>"۰۱۲۳۴۵۶۷۸۹"[d]);}
function norm(value){return String(value||"").toLowerCase().replace(/[يى]/g,"ی").replace(/ك/g,"ک").replace(/[أإآٱ]/g,"ا").replace(/[\u064B-\u0652\u0670\u0640]/g,"").replace(/\u200c/g," ").replace(/[^\p{L}\p{N}\s]/gu," ").replace(/\s+/g," ").trim();}
function iconFor(item){return item.emoji||CATEGORY_ICONS[item.category]||"📘";}
function byRank(a,b){return (b.rank||0)-(a.rank||0)||(b.added||"").localeCompare(a.added||"");}
function toast(message){const el=document.createElement("div");el.className="toast";el.setAttribute("role","status");el.textContent=message;document.body.append(el);setTimeout(()=>el.remove(),2400);}
function track(event,properties={}){if(window.GravelAnalytics)window.GravelAnalytics.track(event,properties);}
function shuffled(items){
  const result=[...items];
  for(let i=result.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[result[i],result[j]]=[result[j],result[i]];}
  return result;
}
function renderTopicStream(){
  const host=document.getElementById("topicStream");
  if(!host||!catalog.length)return;
  const group=document.createElement("div");group.className="topic-stream-group";
  shuffled(catalog).forEach(item=>{
    const link=document.createElement("a");link.href=item.file;link.className="topic-stream-item";
    const icon=document.createElement("span");icon.className="topic-stream-dot";icon.setAttribute("aria-hidden","true");icon.textContent=iconFor(item);
    const title=document.createElement("span");title.textContent=item.title;
    link.append(icon,title);link.addEventListener("click",()=>track("tutorial_opened",{tutorialId:item.id,source:"topic_stream"}));group.append(link);
  });
  const clone=group.cloneNode(true);clone.setAttribute("aria-hidden","true");clone.querySelectorAll("a").forEach(link=>link.tabIndex=-1);
  host.replaceChildren(group,clone);
}

async function loadCatalog(){
  const response=await fetch("catalog.json",{cache:"no-cache"});
  if(!response.ok)throw new Error("catalog unavailable");
  const data=await response.json();
  if(!Array.isArray(data.tutorials))throw new Error("invalid catalog");
  return data.tutorials;
}

function audienceItems(){
  if(audience==="شروع از صفر")return catalog.filter(x=>x.level==="مبتدی");
  if(audience==="توسعه مهارت")return catalog.filter(x=>x.level!=="حرفه‌ای");
  const professional=catalog.filter(x=>x.level==="حرفه‌ای"||x.level==="متوسط");
  return professional.length?professional:catalog;
}

function renderNext(){
  const host=document.getElementById("nextCard");host.replaceChildren();
  const candidates=audienceItems().filter(x=>!state.done[x.id]).sort(byRank);
  const item=candidates[0]||audienceItems().sort(byRank)[0]||catalog[0];
  if(!item){host.hidden=true;return;} host.hidden=false;
  const icon=document.createElement("span");icon.className="next-icon";icon.textContent=iconFor(item);
  const copy=document.createElement("div");const title=document.createElement("h3");title.textContent="پیشنهاد بعدی برای تو: "+item.title;const desc=document.createElement("p");desc.textContent=item.desc||`${item.level} · ${item.track}`;copy.append(title,desc);
  const link=document.createElement("a");link.href=item.file;link.textContent="شروع این آموزش";link.addEventListener("click",()=>track("next_tutorial_clicked",{tutorialId:item.id}));
  host.append(icon,copy,link);
}

function renderPaths(){
  const host=document.getElementById("pathGrid");host.replaceChildren();
  const groups=new Map();
  catalog.forEach(item=>{const key=item.track||"آموزش‌های مستقل";if(!groups.has(key))groups.set(key,[]);groups.get(key).push(item);});
  [...groups.entries()].sort((a,b)=>Math.max(...b[1].map(x=>x.rank||0))-Math.max(...a[1].map(x=>x.rank||0))).forEach(([name,items])=>{
    items.sort((a,b)=>(a.sequence??999)-(b.sequence??999)||byRank(a,b));
    const card=document.createElement("article");card.className="path-card";
    const head=document.createElement("div");head.className="path-head";
    const icon=document.createElement("span");icon.className="path-icon";icon.textContent=TRACK_ICONS[name]||"🧭";
    const heading=document.createElement("div");const h=document.createElement("h3");h.textContent=name;const p=document.createElement("p");p.className="path-summary";p.textContent=`${fa(items.length)} آموزش · ${TRACK_DESCRIPTIONS[name]||"یک مسیر موضوعی و منظم."}`;heading.append(h,p);head.append(icon,heading);
    const list=document.createElement("ol");list.className="path-steps";
    items.slice(0,5).forEach((item,index)=>{const li=document.createElement("li");li.dataset.step=fa(index+1);const a=document.createElement("a");a.href=item.file;a.textContent=item.title;a.addEventListener("click",()=>track("path_selected",{track:name,tutorialId:item.id}));li.append(a);list.append(li);});
    card.append(head,list);host.append(card);
  });
  document.getElementById("pathCount").textContent=fa(groups.size);
}

function renderFilters(){
  const host=document.getElementById("categoryFilters");host.replaceChildren();
  const counts={};catalog.forEach(x=>counts[x.category]=(counts[x.category]||0)+1);
  ["همه",...Object.keys(counts)].forEach(name=>{
    const button=document.createElement("button");button.type="button";button.className="filter-button";button.setAttribute("aria-pressed",String(activeCategory===name));
    button.textContent=name==="همه"?`همه (${fa(catalog.length)})`:`${CATEGORY_ICONS[name]||"📦"} ${name} (${fa(counts[name])})`;
    button.addEventListener("click",()=>{activeCategory=name;renderFilters();renderLibrary();});host.append(button);
  });
}

function filteredItems(){
  const q=norm(query);
  let items=catalog.filter(item=>{
    if(activeCategory!=="همه"&&item.category!==activeCategory)return false;
    if(!q)return true;
    const hay=norm([item.title,item.desc,item.keywords,item.category,item.track,item.level].join(" "));
    return q.split(" ").every(word=>hay.includes(word));
  });
  const sort=document.getElementById("sortSelect").value;
  if(sort==="newest")items.sort((a,b)=>(b.added||"").localeCompare(a.added||""));
  else if(sort==="beginner")items.sort((a,b)=>(a.level==="مبتدی"?-1:1)-(b.level==="مبتدی"?-1:1)||byRank(a,b));
  else if(sort==="title")items.sort((a,b)=>a.title.localeCompare(b.title,"fa"));
  else items.sort(byRank);
  return items;
}

function makeCard(item){
  const fragment=document.getElementById("tutorialTemplate").content.cloneNode(true);
  const card=fragment.querySelector("article");card.dataset.id=item.id;card.classList.toggle("is-done",!!state.done[item.id]);
  const link=fragment.querySelector(".card-link");link.href=item.file;fragment.querySelector(".open-label").href=item.file;
  [link,fragment.querySelector(".open-label")].forEach(a=>a.addEventListener("click",()=>track("tutorial_opened",{tutorialId:item.id,source:"library"})));
  fragment.querySelector(".card-icon").textContent=iconFor(item);
  fragment.querySelector(".level-badge").textContent=item.level;
  fragment.querySelector("h3").textContent=item.title;
  fragment.querySelector(".card-desc").textContent=item.desc||"آموزش گام‌به‌گام و کاربردی گراول.";
  const meta=fragment.querySelector(".card-meta");[item.track,item.time].filter(Boolean).forEach(value=>{const span=document.createElement("span");span.textContent=value;meta.append(span);});
  const checkbox=fragment.querySelector("input");checkbox.checked=!!state.done[item.id];
  checkbox.addEventListener("change",()=>{state.done[item.id]=checkbox.checked;track(checkbox.checked?"tutorial_completed":"tutorial_opened",{tutorialId:item.id,source:"progress"});saveState();renderLibrary();renderNext();renderProgress();});
  return fragment;
}

function renderLibrary(){
  const items=filteredItems();const host=document.getElementById("tutorialGrid");host.replaceChildren();items.forEach(item=>host.append(makeCard(item)));
  document.getElementById("emptyState").hidden=items.length>0;
  document.getElementById("resultSummary").textContent=`${fa(items.length)} آموزش برای نمایش`;
  const active=document.getElementById("activeSearch");active.hidden=!query;active.querySelector("strong").textContent=query;
}

function renderProgress(){
  const done=catalog.filter(x=>state.done[x.id]).length;const percent=catalog.length?Math.round(done/catalog.length*100):0;
  document.getElementById("progressNumber").textContent=fa(percent)+"٪";document.getElementById("progressFill").style.width=percent+"%";
  document.getElementById("progressText").textContent=done?`${fa(done)} آموزش را کامل کرده‌ای؛ قدم بعدی آماده است.`:"اولین آموزش را تمام کن؛ گراول ادامه مسیرت را نگه می‌دارد.";
}

function applySearch(value){
  query=value.trim();document.getElementById("searchInput").value=query;renderLibrary();
  if(query){const results=filteredItems().length;track(results?"search_performed":"search_no_result",{query:query.slice(0,80),results});}
  if(query)document.getElementById("library").scrollIntoView({behavior:"smooth"});
  const url=new URL(location.href);query?url.searchParams.set("q",query):url.searchParams.delete("q");history.replaceState({},"",url);
}

function bindEvents(){
  const search=document.getElementById("searchInput");search.value=query;search.addEventListener("input",()=>{query=search.value.trim();renderLibrary();});
  search.addEventListener("change",()=>applySearch(search.value));
  document.querySelectorAll("[data-query]").forEach(button=>button.addEventListener("click",()=>applySearch(button.dataset.query)));
  document.addEventListener("keydown",event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="k"){event.preventDefault();search.focus();search.select();}});
  document.querySelectorAll("[data-audience]").forEach(button=>button.addEventListener("click",()=>{audience=button.dataset.audience;track("level_selected",{level:audience});document.querySelectorAll("[data-audience]").forEach(x=>x.setAttribute("aria-pressed",String(x===button)));renderNext();}));
  document.getElementById("sortSelect").addEventListener("change",renderLibrary);
  document.querySelector("#activeSearch button").addEventListener("click",()=>applySearch(""));
  document.getElementById("requestButton").addEventListener("click",()=>{const value=document.getElementById("requestText").value.trim();if(!value){toast("اول موضوع آموزش را بنویس ✍️");return;}track("topic_requested",{topic:value.slice(0,80)});const text=`سلام مهدی! پیشنهاد آموزش برای گراول:\n«${value}»\nhttps://mygravel.ir`;window.open("https://t.me/Mehdirezghi?text="+encodeURIComponent(text),"_blank","noopener");});
  window.addEventListener("beforeinstallprompt",event=>{event.preventDefault();deferredInstall=event;document.getElementById("installBtn").hidden=false;});
  document.getElementById("installBtn").addEventListener("click",async()=>{if(!deferredInstall)return;deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null;document.getElementById("installBtn").hidden=true;});
}

async function init(){
  document.getElementById("year").textContent=fa(new Date().getFullYear());bindEvents();
  try{catalog=await loadCatalog();document.getElementById("tutorialCount").textContent=fa(catalog.length);renderTopicStream();renderNext();renderPaths();renderFilters();renderLibrary();renderProgress();}
  catch(error){document.getElementById("resultSummary").textContent="فهرست آموزش‌ها فعلاً در دسترس نیست.";document.getElementById("emptyState").hidden=false;console.error(error);}
  if("serviceWorker" in navigator&&location.protocol==="https:")window.addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));
}
init();
