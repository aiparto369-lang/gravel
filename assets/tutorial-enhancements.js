(function(){
  "use strict";
  function status(message){const old=document.querySelector(".gravel-share-status");if(old)old.remove();const el=document.createElement("div");el.className="gravel-share-status";el.setAttribute("role","status");el.textContent=message;document.body.append(el);setTimeout(()=>el.remove(),2200);}
  async function share(){
    const data={title:document.title,text:"این آموزش گراول را ببین:",url:location.href};
    try{if(navigator.share){await navigator.share(data);return;}await navigator.clipboard.writeText(location.href);status("لینک آموزش کپی شد");}
    catch(error){if(error&&error.name!=="AbortError")status("لینک را از نوار مرورگر کپی کن");}
  }
  document.addEventListener("DOMContentLoaded",function(){const button=document.querySelector("[data-gravel-share]");if(button)button.addEventListener("click",share);});
})();
