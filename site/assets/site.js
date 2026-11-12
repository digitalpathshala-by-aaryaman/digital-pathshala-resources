(() => {
'use strict';
const CONFIG = Object.freeze({
  preview: false,
  appScript: 'https://script.google.com/macros/s/AKfycbwldCtUXGeD3LqeyGqj8TjSUKdasREcXDvfIoMYrhXI3UaHBoM25i6Ypp60ctQu-Efd/exec',
  manifest: 'videos.json',
  independentManifest: 'independent.json',
  channel: 'https://www.youtube.com/@DigitalPathshalabyAaryaman',
  demoZip: window.DP_DEMO_ZIP || ''
});
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const isVideoId = s => /^[a-z0-9][a-z0-9-]{1,71}$/i.test(s||'');
let published=[], independent=[], selected=null, kind='all', filterText='', busy=false;
// Preserve request IDs after transient failures so retries cannot create duplicate leads.
let pendingDownloadRequest=null, pendingFeedbackRequest=null;
function nowIst(){return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date()).reduce((a,x)=>{a[x.type]=x.value;return a;},{});}
function istString(){const v=nowIst();return `${v.year}-${v.month}-${v.day} ${v.hour}:${v.minute}`;}
function validRelease(v){return v.status==='live' && /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(v.release_at_ist || '') && v.release_at_ist<=istString();}
function validLink(v){if(CONFIG.preview)return true;try {let u=new URL(v.resource_url,location.href);return u.origin===location.origin && u.pathname.startsWith(new URL('resources/',location.href).pathname) && /\.zip$/i.test(u.pathname);}catch(_){return false;}}
function publishedOnly(videos){return videos.filter(v=>isVideoId(v.id) && validRelease(v) && validLink(v)).sort((a,b)=>b.release_at_ist.localeCompare(a.release_at_ist));}
function validIndependentLink(v) {
 try {
   const u=new URL(v.resource_url,location.href),root=new URL('downloads/',document.baseURI);
   return u.origin===root.origin&&u.pathname.startsWith(root.pathname)&&/\.(pdf|xlsx|xlsm|zip)$/i.test(u.pathname)&&!u.search&&!u.hash;
 }catch(_){return false;}
}
function visibleIndependent(items) {
 return items.filter(v=>v&&v.status==='live'&&/^(ebook|template|guide|tool|resource)$/.test(v.kind||'')&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(v.slug||'')&&v.published_at_ist<=istString()&&validIndependentLink(v))
   .sort((a,b)=>b.published_at_ist.localeCompare(a.published_at_ist));
}
function independentCards() {
 const grid=$('independentCards'),empty=$('independentEmpty');if(!grid||!empty)return;
 const filtered=independent.filter(v=>[v.title,v.description,v.category,v.kind].join(' ').toLowerCase().includes(filterText));
 grid.innerHTML=filtered.map(window.DPIndependent.card).join('');
 empty.innerHTML=filtered.length?'':independent.length?'<div class="empty"><h3>No independent resources found.</h3><p>Try a different search.</p></div>':'<div class="empty"><div class="empty-icon">📚</div><h3>Free e-books and tools coming soon.</h3><p>Independent guides, Excel templates and practical tools will appear as they are published.</p></div>';
}
function independentDetail(v) {
 selected=v;document.title=v.title+' | Digital Pathshala';
 $('app').innerHTML=window.DPIndependent.detail(v);
 $('openDownload').addEventListener('click',openModal);
 $('feedbackForm').addEventListener('submit',submitFeedback);
}
function type(v){return v.type==='short' || v.type==='short_video'?'Short':'Full Lesson';}
function keywords(v){const s=(v.title||'').toLowerCase();return s.includes('excel')?'Excel':s.includes('gemini')?'Google Gemini':s.includes('canva')?'Canva':s.includes('chatgpt')?'ChatGPT':'Digital Skills';}
function stat(){
  // Only count actually published, downloadable resources from both catalogues.
  // Prepared or scheduled-but-unreleased files are never included.
  const total=published.length+independent.length;
  $('publishedCount').textContent=total;
  $('heroIndependentCount').textContent=independent.length;
  $('heroVideoStatus').textContent=published.length?published.length+' available':'Coming soon';
  $('independentHeaderCount').textContent=independent.length+' available '+(independent.length===1?'resource':'resources');
  $('counterText').textContent=published.length
    ?published.length+' published video '+(published.length===1?'resource':'resources')
    :'Video resources coming soon';
}
function card(v){let words=esc(v.title);return `<a href="?v=${encodeURIComponent(v.id)}" class="video-card"><div class="thumb"><span class="label">${esc(type(v)).toUpperCase()}</span><div class="text">${esc(keywords(v))}<br>Resources</div><span class="play">▶</span></div><div class="card-body"><span class="card-type">${esc(keywords(v))} · ${esc(type(v))}</span><h3>${words}</h3><p>${esc(v.description||'Download the companion learning material for this Digital Pathshala video.')}</p><div class="card-bottom"><span>${(v.resources||[]).length || 'Free'} included files</span><span>View Resources →</span></div></div></a>`}
function home(){document.title='Free Learning Resources | Digital Pathshala';$('app').innerHTML=`<section class="hero"><div class="container hero-grid"><div><div class="eyebrow">Digital Pathshala · Learn · Create · Grow</div><h1>Learn something.<br><em>Take something useful home.</em></h1><p>Practical resources from Digital Pathshala by Aaryaman Goenka. Discover published video packs alongside independent free e-books, Excel templates and useful tools.</p><div class="hero-actions"><a href="#independent" class="btn btn-primary">Explore free e-books & tools ↓</a><a href="#resources" class="btn btn-outline">Video learning resources ↓</a><a href="${CONFIG.channel}" target="_blank" rel="noopener" class="btn btn-outline">Watch on YouTube ↗</a></div></div><div class="hero-side"><div class="sup">Currently available</div><div class="bigstat" id="publishedCount">—</div><h3>Total free resources</h3><p>Explore our growing collection of useful e-books, templates, guides and companion downloads.</p><div class="stat-break"></div><div class="mini-row"><strong>E-books & practical tools</strong><span id="heroIndependentCount">—</span></div><div class="mini-row"><strong>Video learning resources</strong><span id="heroVideoStatus">Coming soon</span></div></div></div></section><div class="library-search-wrap"><div class="container"><label class="library-search-label" for="searchVideos">Find your next useful resource</label><input id="searchVideos" class="search library-search-input" aria-label="Search all published e-books, templates, tools and video resources" placeholder="Search all resources: ChatGPT, Excel, Gemini, Claude..."/><p class="library-search-hint">One search for e-books, templates, practical tools and published video learning materials.</p></div></div><section class="section independent-section" id="independent"><div class="container"><div class="section-head"><div><div class="kicker">Independent Resource Library</div><h2>Free e-books, templates & practical tools.</h2><p>Discover practical PDF guides, e-books, Excel templates and tools—each with its own permanent page.</p></div><div class="live-count" id="independentHeaderCount">Available resources</div></div><div class="grid" id="independentCards"></div><div id="independentEmpty"></div></div></section><section class="section" id="resources"><div class="container"><div class="section-head"><div><div class="kicker">Your Learning Library</div><h2>Resources from published videos.</h2><p>Companion materials appear here only after the matching YouTube video is released.</p></div><div class="live-count" id="counterText">0 published resources</div></div><div class="toolbar video-filters-toolbar"><div class="filters" id="filters"><button type="button" class="chip active" data-kind="all">All</button><button type="button" class="chip" data-kind="long">Full videos</button><button type="button" class="chip" data-kind="short">Shorts</button></div></div><div class="grid" id="cards"></div><div id="empty"></div></div></section><section class="section steps"><div class="container"><div class="kicker">Simple & Free</div><div class="section-head"><h2>How to get a resource.</h2></div><div class="steps-grid"><div class="step"><span class="step-num">01</span><h3>Explore a resource</h3><p>Choose an e-book, practical tool, template or resource from a published video.</p></div><div class="step"><span class="step-num">02</span><h3>Request your download</h3><p>Submit your name and email. Phone number is optional.</p></div><div class="step"><span class="step-num">03</span><h3>Get the original file</h3><p>After confirmation, the matching PDF, Excel file or ZIP starts downloading.</p></div></div></div></section>`;$('searchVideos').addEventListener('input',e=>{filterText=e.target.value.toLowerCase();cards();independentCards()});$('filters').addEventListener('click',e=>{if(!e.target.dataset.kind)return;kind=e.target.dataset.kind;$('filters').querySelectorAll('button').forEach(b=>b.classList.toggle('active',b===e.target));cards()});stat();cards();independentCards();}
function cards(){const rows=published.filter(v=>(kind==='all'||(kind==='long'?type(v)==='Full Lesson':type(v)==='Short'))&&((v.title||'').toLowerCase().includes(filterText)||keywords(v).toLowerCase().includes(filterText)));$('cards').innerHTML=rows.map(card).join('');$('empty').innerHTML=rows.length?'':published.length?'<div class="empty"><div class="empty-icon">🔎</div><h3>No matches found</h3><p>Try another search or choose a different filter.</p></div>':'<div class="empty"><div class="empty-icon">📚</div><h3>Our resource library is opening soon.</h3><p>We are preparing free companion materials. As each Digital Pathshala video is released, its resource pack will appear here automatically. Subscribe to be the first to know.</p><p style="margin-top:22px"><a class="btn btn-dark" href="'+CONFIG.channel+'" target="_blank" rel="noopener">Visit our YouTube channel ↗</a></p></div>';}
function fileRows(v){if(!Array.isArray(v.resources)||!v.resources.length)return '<p class="detail-copy">The resource pack contains the supporting files for this lesson.</p>';return v.resources.map(f=>{const name=typeof f==='string'?f:f.file;const ext=String(name).split('.').pop().toUpperCase();const size=f.bytes?`${Math.max(1,Math.round(f.bytes/1024))} KB`:'';return `<div class="file-row"><span class="file-icon">${esc(ext.slice(0,5))}</span><span><strong>${esc(name)}</strong><small>${esc(size)}</small></span></div>`}).join('');}
function embed(v){const url=String(v.youtube_url||'');let id='';try{const u=new URL(url);if(u.hostname==='youtu.be')id=u.pathname.slice(1);else if(['www.youtube.com','youtube.com','m.youtube.com'].includes(u.hostname))id=u.searchParams.get('v')||'';}catch(_){ }return /^[a-zA-Z0-9_-]{11}$/.test(id)?`<iframe title="YouTube video" src="https://www.youtube-nocookie.com/embed/${id}" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer;autoplay;encrypted-media;gyroscope;picture-in-picture" allowfullscreen loading="lazy"></iframe>`:`<div class="video-fallback"><strong>Digital Pathshala on YouTube</strong><p>Watch the lesson and follow along with its companion resources.</p><a href="${CONFIG.channel}" target="_blank" rel="noopener">Visit the channel ↗</a></div>`;}
function detail(v){selected=v;document.title=`${v.title} | Digital Pathshala Resources`;$('app').innerHTML=`<section class="detail"><div class="container"><a class="back" href="?">← All published resources</a><div class="detail-grid"><div class="panel detail-main"><div class="detail-tag">${esc(type(v))} · ${esc(keywords(v))}</div><h1 class="detail-title">${esc(v.title)}</h1><p class="detail-copy">${esc(v.description||'Explore the free learning material prepared for this video. Review the included files below, then request the complete ZIP.')}</p><div class="tags"><span class="tag">● Released</span><span class="tag">${(v.resources||[]).length || 'Free'} companion files</span><span class="tag">No payment needed</span></div><div class="video-embed">${embed(v)}</div><hr class="separator"><div class="inside-head"><h2>What's inside your ZIP?</h2><span>${(v.resources||[]).length || ''} FILES</span></div>${fileRows(v)}</div><div><aside class="panel aside"><div class="free">✦ Free companion materials</div><h2>Get the full resource pack.</h2><p>One ZIP with the companion material for this lesson. You'll enter your details only after clicking download.</p><button class="btn btn-primary" type="button" id="openDownload">↓ Download Resources</button><small>One quick form · Name and email required · Phone optional</small></aside><section class="panel feedback"><h3>Have a question or suggestion?</h3><p>Tell us privately what you would like to learn or what problem you're facing. Your message won't be visible to other viewers.</p><form id="feedbackForm"><label for="feedbackType">Message type</label><select name="feedback_type" id="feedbackType"><option value="question">Question about this video</option><option value="idea">Request a new topic</option><option value="issue">Problem with the resource</option><option value="other">Other feedback</option></select><label for="feedbackMessage">Your message *</label><textarea id="feedbackMessage" name="message" maxlength="1800" required placeholder="Share your question or idea..."></textarea><label for="feedbackName">Your name (optional)</label><input id="feedbackName" name="full_name" maxlength="100"/><label class="privacy-check"><input type="checkbox" name="privacy_consent" required/><span>I agree to the <a href="?privacy=1">privacy notice</a> for this private message.</span></label><button type="submit" class="btn btn-dark">Send private feedback</button><div id="feedbackStatus" role="status" aria-live="polite" class="form-note"></div></form></section></div></div></div></section>`;$('openDownload').addEventListener('click',openModal);$('feedbackForm').addEventListener('submit',submitFeedback);}
function unavailable(){document.title='Resource not available | Digital Pathshala';$('app').innerHTML=`<section class="section"><div class="container"><div class="empty"><div class="empty-icon">🔒</div><h3>This resource is not available yet.</h3><p>If you arrived from an upcoming YouTube video link, the resources will appear only when that video has been released. No downloadable materials are public before then.</p><p style="margin-top:21px"><a href="?" class="btn btn-dark">Browse available resources ←</a></p></div></div></section>`;}
function privacy(){document.title='Privacy notice | Digital Pathshala';$('app').innerHTML=`<section class="section"><div class="container"><a href="?" class="back">← Home</a><h1 style="font-size:36px">Privacy notice</h1><p style="max-width:800px;line-height:1.9;margin-top:16px;color:var(--mute)">When you request a resource, Digital Pathshala collects your name, email address, optional phone number, the resource you requested and your submission time in a private Google Sheet. We use these details to record your request and provide the download. Your optional private feedback is used to review questions and suggestions. Promotional updates are only selected through a separate optional checkbox. Information is not displayed in the public resource library.</p><p style="max-width:800px;line-height:1.9;margin-top:16px;color:var(--mute)">For questions about your submitted details, or to request correction or deletion, email <a href="mailto:aaryamang2008@gmail.com">aaryamang2008@gmail.com</a>. Digital Pathshala will complete and review its final retention policy and privacy notice before opening lead collection.</p></div></section>`;}
function openModal(){if(!selected)return;const text=document.querySelector('#downloadModal p');if(text)text.textContent=selected.kind?'Enter your details to download this free '+selected.file_type+' file. Name and email are required; phone is optional.':"Enter your details to get this video's companion ZIP. Name and email are required; phone is optional.";const tag=document.querySelector('.modal-kicker');if(tag)tag.textContent=selected.kind?'FREE '+selected.kind.toUpperCase():'FREE VIDEO RESOURCE';$('downloadModal').hidden=false;$('downloadModal').querySelector('input[name=full_name]').focus();document.body.style.overflow='hidden';$('downloadForm').reset();$('modalStatus').textContent='';$('modalStatus').className='status-msg';$('fallbackDownload').classList.remove('show');$('fallbackDownload').textContent='Download manually if it does not start';}
function closeModal(){if(busy)return;$('downloadModal').hidden=true;document.body.style.overflow='';}
function uuid(){if(crypto?.randomUUID)return crypto.randomUUID();const x=crypto.getRandomValues(new Uint8Array(16));x[6]=(x[6]&15)|64;x[8]=(x[8]&63)|128;const h=[...x].map(b=>b.toString(16).padStart(2,'0')).join('');return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`;}
function pageUrl(v){if(v.kind)return v.page_url;const url=new URL(location.href);url.search='?v='+encodeURIComponent(v.id);url.hash='';return url.href;}
function commonPayload(v,action){const params=new URLSearchParams(location.search);return {request_id:uuid(),action,video_id:v.id,page_url:pageUrl(v),referrer:document.referrer||'',utm_source:params.get('utm_source')||'',utm_medium:params.get('utm_medium')||'',utm_campaign:params.get('utm_campaign')||'',website:'',privacy_consent:true};}
function jsonp(args,timeout=8000){return new Promise((resolve,reject)=>{let done=false;const name='dpCallback'+Math.random().toString(36).slice(2,12);const script=document.createElement('script');const kill=()=>{script.remove();delete window[name];clearTimeout(timer);};const timer=setTimeout(()=>{if(!done){done=true;kill();reject(new Error('Confirmation service timed out.'));}},timeout);window[name]=data=>{if(done)return;done=true;kill();resolve(data)};script.onerror=()=>{if(done)return;done=true;kill();reject(new Error('Confirmation service not reachable.'))};script.src=CONFIG.appScript+'?'+new URLSearchParams({...args,callback:name,_t:Date.now()});document.head.appendChild(script);});}
async function confirmedSubmit(payload){
  // no-cors returns an opaque response, which is NOT proof the Sheet was written.
  // Receipt verification is authoritative; transient JSONP errors must not
  // cause a second request ID or an incorrect "not saved" message.
  try {
    await fetch(CONFIG.appScript,{
      method:'POST',mode:'no-cors',
      headers:{'Content-Type':'text/plain;charset=utf-8'},
      body:JSON.stringify(payload)
    });
  } catch(error) {
    const err=new Error('The submission connection failed; your details may not have been received.');
    err.retryable=true;throw err;
  }
  let successfulLookups=0,networkFailures=0;
  const started=Date.now();
  for(let n=0;n<18 && Date.now()-started<35000;n++){
    await new Promise(resolve=>setTimeout(resolve,n===0?900:Math.min(1100+Math.floor(n/5)*250,1650)));
    let receipt;
    try {
      // Google ContentService redirects to a one-time googleusercontent URL;
      // an occasional redirect failure is recoverable on a new GET.
      receipt=await jsonp({action:'receipt',request_id:payload.request_id},4800);
    } catch(error) {
      networkFailures++;
      if(networkFailures>=7 && successfulLookups===0)break;
      continue;
    }
    successfulLookups++;
    if(receipt.status==='ok'){
      if(receipt.video_id===payload.video_id&&receipt.action===payload.action)return receipt;
      throw new Error('The confirmation does not match this resource. Contact Digital Pathshala.');
    }
    if(receipt.status==='error')throw new Error(receipt.message||'The submission was rejected. Please check your details.');
    if(receipt.status!=='pending')throw new Error('Unexpected confirmation response. Please try again.');
  }
  const error=new Error(successfulLookups
    ? 'Your submission is still being processed. We could not confirm that it was saved.'
    : 'The confirmation service could not be reached from this browser.');
  error.retryable=true;
  throw error;
}
function startDownload(url){const a=document.createElement('a');a.href=url;a.download=CONFIG.preview?'Digital_Pathshala_PREVIEW_Only.zip':url.split('/').pop().split('?')[0];a.rel='noopener';a.style.display='none';document.body.appendChild(a);a.click();a.remove();}
function setBusy(v){busy=v;$('submitDownload').disabled=v;$('submitDownload').innerHTML=v?'<span class="spinner" aria-hidden="true"></span> Saving your request...':'Submit & Download ↓';$('closeDownload').disabled=v;}
async function submitDownload(ev){
  ev.preventDefault();
  if(!selected||busy)return;
  const form=ev.currentTarget;
  if(!form.reportValidity())return;
  const fields=new FormData(form);
  const values={
    full_name:String(fields.get('full_name')||'').trim(),
    email:String(fields.get('email')||'').trim(),
    phone:String(fields.get('phone')||'').trim(),
    marketing_opt_in:fields.has('marketing_opt_in')
  };
  const signature=JSON.stringify([selected.id,values]);
  if(!pendingDownloadRequest||pendingDownloadRequest.signature!==signature){
    pendingDownloadRequest={
      signature,
      payload:{...commonPayload(selected,'download'),...values}
    };
  }
  const payload=pendingDownloadRequest.payload;
  setBusy(true);
  $('modalStatus').className='status-msg';
  $('modalStatus').textContent='Saving your request and verifying confirmation...';
  const fallback=$('fallbackDownload');
  fallback.classList.remove('show');
  try{
    let receipt;
    if(CONFIG.preview){
      await new Promise(r=>setTimeout(r,450));
      receipt={status:'ok',video_id:selected.id,action:'download',download_url:CONFIG.demoZip};
    }else{
      receipt=await confirmedSubmit(payload);
    }
    const url=receipt.download_url;
    if(!url||(!CONFIG.preview&&!(selected.kind
      ?validIndependentLink({...selected,resource_url:url})
      :validLink({...selected,resource_url:url}))))
      throw new Error('The download link is not ready. Please contact Digital Pathshala.');
    $('modalStatus').className='status-msg form-success';
    $('modalStatus').textContent=CONFIG.preview
      ?'Preview only: no information was saved.'
      :'Your request was verified and saved. Your download should begin automatically.';
    fallback.href=url;
    fallback.download=CONFIG.preview?'Digital_Pathshala_PREVIEW_Only.zip':
      (selected.kind?selected.file_name:selected.id+'.zip');
    fallback.textContent='Click here if your file did not download';
    fallback.classList.add('show');
    startDownload(url);
    pendingDownloadRequest=null;
    form.querySelectorAll('input').forEach(x=>x.disabled=true);
  }catch(error){
    $('modalStatus').className='status-msg form-error';
    if(error.retryable){
      // Only a public, checksum-published manifest URL can be used here.
      // Never claim the submission was saved without a confirmed receipt.
      const url=selected.resource_url;
      const safe=selected.kind
        ?validIndependentLink({...selected,resource_url:url})
        :validLink({...selected,resource_url:url});
      $('modalStatus').textContent=String(error.message||'Confirmation unavailable.')+
        ' Your request may already have reached us. You may retry using the same request ID without a duplicate entry.';
      if(safe){
        fallback.href=url;
        fallback.download=selected.kind?selected.file_name:selected.id+'.zip';
        fallback.textContent='Download the resource directly (saving not confirmed)';
        fallback.classList.add('show');
      }
    }else{
      $('modalStatus').textContent=String(error.message||'Submission failed. Please check your details.');
    }
  }finally{setBusy(false);}
}
async function submitFeedback(ev){
  ev.preventDefault();
  const form=ev.currentTarget;
  if(!form.reportValidity()||!selected)return;
  const fields=new FormData(form),status=$('feedbackStatus');
  const values={
    feedback_type:fields.get('feedback_type'),
    message:String(fields.get('message')||'').trim(),
    full_name:String(fields.get('full_name')||'').trim()
  };
  const signature=JSON.stringify([selected.id,values]);
  if(!pendingFeedbackRequest||pendingFeedbackRequest.signature!==signature){
    pendingFeedbackRequest={
      signature,
      payload:{...commonPayload(selected,'feedback'),...values}
    };
  }
  status.className='form-note';
  status.textContent='Sending your private message and checking confirmation...';
  form.querySelector('button').disabled=true;
  try{
    if(!CONFIG.preview){
      const receipt=await confirmedSubmit(pendingFeedbackRequest.payload);
      if(receipt.status!=='ok')throw new Error('Confirmation not received');
    }else await new Promise(r=>setTimeout(r,450));
    pendingFeedbackRequest=null;
    status.className='form-note form-success';
    status.textContent=CONFIG.preview
      ?'Preview only: message not stored.'
      :'Your private message was verified and recorded. Thank you!';
    form.reset();
  }catch(error){
    status.className='form-note form-error';
    status.textContent=String(error.message||'Please try again.')+
      (error.retryable?' You can retry safely without creating a duplicate.':'');
  }finally{form.querySelector('button').disabled=false;}
}
async function init(){
 const params=new URLSearchParams(location.search),id=params.get('v');
 const basePath=new URL('videos.json',document.baseURI).pathname.replace(/videos\.json$/,'');
 const path=location.pathname.startsWith(basePath)?location.pathname.slice(basePath.length):'';
 const isIndependent=/^(ebooks|templates|guides|tools|resources)\/([a-z0-9]+(?:-[a-z0-9]+)*)\/(?:index\.html)?$/.exec(path);
 try{
   const [vResponse,rResponse]=await Promise.all([
      fetch(CONFIG.manifest+'?_t='+Date.now(),{cache:'no-store'}),
      fetch(CONFIG.independentManifest+'?_t='+Date.now(),{cache:'no-store'})
   ]);
   if(!vResponse.ok||!rResponse.ok)throw new Error('Published catalogue unavailable');
   const videoData=await vResponse.json(),resourceData=await rResponse.json();
   if(!Array.isArray(videoData.videos)||!Array.isArray(resourceData.resources))throw new Error('Invalid catalogue format');
   published=publishedOnly(videoData.videos);
   independent=visibleIndependent(resourceData.resources);
   if(params.has('privacy'))privacy();
   else if(isIndependent){
     const labels={ebooks:'ebook',templates:'template',guides:'guide',tools:'tool',resources:'resource'};
     const resource=independent.find(v=>v.kind===labels[isIndependent[1]]&&v.slug===isIndependent[2]);
     resource?independentDetail(resource):unavailable();
   } else if(id) {
     const v=published.find(x=>x.id===id);
     v?detail(v):unavailable();
   } else home();
 }catch(error){
   published=[];independent=[];
   if(id||isIndependent)unavailable();else home();
   console.error('Catalogue loading issue:',error);
 }
 $('year').textContent=new Date().getFullYear();
}

$('navToggle').addEventListener('click',()=>{const nav=$('navlinks');const opened=nav.classList.toggle('open');$('navToggle').setAttribute('aria-expanded',String(opened));});$('downloadForm').addEventListener('submit',submitDownload);$('closeDownload').addEventListener('click',closeModal);$('modalBackdrop').addEventListener('click',closeModal);window.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});if(CONFIG.preview){$('demoCount').addEventListener('change',()=>{history.replaceState({},'',location.pathname);selected=null;init();});}init();
})();
