(function(){
const config=window.fsaFaceShapeAnalyzer||{},texts=config.texts||{},MAX_SIZE_BYTES=(Number(config.maxFileSizeMb)||8)*1024*1024;
const FEATURE_META={eyes:{title:"Eye Analysis",subtitle:f=>`${f.size||"Balanced"} ${String(f.shape||"natural").toLowerCase()} eyes with ${String(f.spacing||"balanced").toLowerCase()} spacing.`,icon:icon("eyes")},eyebrows:{title:"Eyebrow Analysis",subtitle:f=>`${f.thickness||"Balanced"} brows with ${String(f.arch||"soft").toLowerCase()} arch and ${String(f.spacing||"balanced").toLowerCase()} spacing.`,icon:icon("brows")},lips:{title:"Lip Analysis",subtitle:f=>`${f.thickness||"Balanced"} lips with ${String(f.shape||"balanced").toLowerCase()} structure and ${String(f.cupid_bow||"defined").toLowerCase()} cupid bow.`,icon:icon("lips")},nose:{title:"Nose Analysis",subtitle:f=>`${f.width||"Balanced"} width nose with ${String(f.bridge||"defined").toLowerCase()} bridge and ${String(f.shape||"straight").toLowerCase()} shape.`,icon:icon("nose")}};
const SHAPE_DESCRIPTIONS={round:"Soft curves and balanced proportions create a rounded silhouette with gentle structure.",oval:"Balanced width and length produce one of the most versatile face profiles.",oblong:"Longer facial proportions create a sleek vertical profile with refined structure.",square:"Defined edges and a strong jawline create a confident, angular silhouette.",heart:"A broader upper face tapering into a narrower chin gives this shape its distinct contrast.",diamond:"Prominent cheekbones with a narrower forehead and jaw create a sculpted, faceted profile."};
document.addEventListener("DOMContentLoaded",()=>document.querySelectorAll("[data-fsa-widget]").forEach(init));
function init(widget){
const els={fileInput:widget.querySelector("[data-fsa-file-input]"),intakeShell:widget.querySelector("[data-fsa-intake-shell]"),dropzone:widget.querySelector("[data-fsa-dropzone]"),dropEmpty:widget.querySelector("[data-fsa-drop-empty]"),dropPreview:widget.querySelector("[data-fsa-drop-preview]"),intakeImage:widget.querySelector("[data-fsa-intake-image]"),scanOverlay:widget.querySelector("[data-fsa-scan-overlay]"),intakeTitle:widget.querySelector("[data-fsa-intake-title]"),intakeDescription:widget.querySelector("[data-fsa-intake-description]"),status:widget.querySelector("[data-fsa-status]"),resultsShell:widget.querySelector("[data-fsa-results-shell]"),resultImage:widget.querySelector("[data-fsa-result-image]"),tabs:[...widget.querySelectorAll(".fsa-tab")],results:widget.querySelector("[data-fsa-results]"),sidebarTitle:widget.querySelector(".fsa-sidebar-title"),sidebarDescription:widget.querySelector(".fsa-sidebar-description"),qualityContainer:widget.querySelector("[data-fsa-quality]"),featureRatingsWrap:widget.querySelector("[data-fsa-feature-ratings]"),featureRatingsList:widget.querySelector("[data-fsa-feature-ratings-list]"),reuploadButton:widget.querySelector("[data-fsa-reupload]")};
const state={activeTab:"shape",file:null,result:null,previewUrl:"",isBusy:false};
syncTabs(els.tabs,state.activeTab);
bind(widget,els,state);
if(!config.isConfigured)setStatus(els.status,texts.configMissing||"","warning");
}
function bind(widget,els,state){
const openPicker=()=>{if(state.isBusy)return;els.fileInput.click();};
els.dropzone.addEventListener("click",openPicker);
els.dropzone.addEventListener("keydown",e=>{if((e.key==="Enter"||e.key===" ")&&!state.isBusy){e.preventDefault();openPicker();}});
["dragenter","dragover"].forEach(n=>els.dropzone.addEventListener(n,e=>{e.preventDefault();if(!state.isBusy)els.dropzone.classList.add("is-dragging");}));
["dragleave","dragend"].forEach(n=>els.dropzone.addEventListener(n,e=>{e.preventDefault();if(!els.dropzone.contains(e.relatedTarget))els.dropzone.classList.remove("is-dragging");}));
els.dropzone.addEventListener("drop",e=>{e.preventDefault();els.dropzone.classList.remove("is-dragging");if(state.isBusy)return;const f=e.dataTransfer&&e.dataTransfer.files?e.dataTransfer.files[0]:null;if(f)pickFile(widget,els,state,f);});
els.fileInput.addEventListener("change",()=>{const f=els.fileInput.files&&els.fileInput.files[0];if(f)pickFile(widget,els,state,f);});
els.reuploadButton.addEventListener("click",()=>{if(state.isBusy)return;els.fileInput.value="";els.fileInput.click();});
els.tabs.forEach(tab=>tab.addEventListener("click",()=>{state.activeTab=tab.dataset.tab;syncTabs(els.tabs,state.activeTab);if(state.result)renderActiveTab(els.results,state.result,state.activeTab);}));
}
function pickFile(widget,els,state,file){
const err=validateFile(file);
if(err){setStatus(els.status,err,"error");els.fileInput.value="";return;}
if(state.previewUrl)URL.revokeObjectURL(state.previewUrl);
state.previewUrl=URL.createObjectURL(file);state.file=file;state.result=null;state.activeTab="shape";syncTabs(els.tabs,state.activeTab);
showIntake(els);els.dropEmpty.classList.add("is-hidden");els.dropPreview.classList.remove("is-hidden");setImage(els.intakeImage,state.previewUrl,"");
updateCopy(els,texts.dropReady||"Portrait staged. Releasing into scan mode now...","The preview is locked in. Hold tight while we map face shape, symmetry, and feature-level measurements.");
setStatus(els.status,texts.dropReady||"","success");els.fileInput.value="";
window.setTimeout(()=>{void analyze(widget,els,state);},120);
}
async function analyze(widget,els,state){
if(!state.file||state.isBusy)return;
if(!config.isConfigured){setStatus(els.status,texts.configMissing||"","warning");return;}
state.isBusy=true;widget.classList.add("is-loading");els.dropzone.classList.add("is-scanning");els.scanOverlay.classList.remove("is-hidden");
updateCopy(els,texts.scanningTitle||"Scanning facial geometry",texts.scanningHint||"Reading symmetry, feature balance, and shape relationships.");
setStatus(els.status,texts.analyzing||"Analyzing portrait...","loading");
const fd=new FormData();fd.append("action",config.action||"");fd.append("nonce",config.nonce||"");fd.append("image",state.file);
try{
const res=await fetch(config.ajaxUrl,{method:"POST",body:fd,credentials:"same-origin"});
let payload=null;try{payload=await res.json();}catch(e){payload=null;}
if(!payload||!payload.success){const msg=payload&&payload.data&&payload.data.message?payload.data.message:texts.genericError||"Unable to process this portrait.";throw new Error(msg);}
state.result=payload.data;state.activeTab="shape";renderResult(els,state);
}catch(err){
els.scanOverlay.classList.add("is-hidden");els.dropzone.classList.remove("is-scanning");
updateCopy(els,"Scan interrupted","The portrait stayed in place, but the API did not return a usable analysis. You can try the same image again or choose a new one.");
setStatus(els.status,err instanceof Error?err.message:texts.genericError,"error");
}finally{state.isBusy=false;widget.classList.remove("is-loading");}
}
function renderResult(els,state){
const result=state.result||{},images=result.images||{},preview=images.highlighted_url||images.original_url||state.previewUrl||"";
if(preview){setImage(els.intakeImage,preview,state.previewUrl);setImage(els.resultImage,preview,state.previewUrl);}
els.scanOverlay.classList.add("is-hidden");els.dropzone.classList.remove("is-scanning");els.resultsShell.classList.remove("is-hidden");els.intakeShell.classList.add("is-hidden");
const scoring=result.scoring||{};els.sidebarTitle.textContent=scoring.rating_message||"Results are ready";els.sidebarDescription.textContent="Feature ratings, quality signals, and recommendations from the live response appear below.";
renderQualityChips(els.qualityContainer,result.image_quality||{},result);renderFeatureRatings(els.featureRatingsWrap,els.featureRatingsList,result);syncTabs(els.tabs,state.activeTab);renderActiveTab(els.results,result,state.activeTab);setStatus(els.status,"","info");
}
function renderActiveTab(container,result,tab){container.innerHTML=tab==="score"?renderScoreTab(result):tab==="eyes"?renderFeatureTab("eyes",result):tab==="brows"?renderFeatureTab("eyebrows",result):tab==="lips"?renderFeatureTab("lips",result):tab==="nose"?renderFeatureTab("nose",result):renderShapeTab(result);}
function renderShapeTab(result){
const faceShape=((result.features||{}).face_shape||{}),primaryShape=String(faceShape.primary_shape||"Balanced"),shapeKey=primaryShape.toLowerCase(),probabilities=faceShape.shape_probabilities||{},recommendations=Array.isArray(faceShape.recommendations)?faceShape.recommendations:[],measurements=result.measurements||{},characteristics=faceShape.characteristics||{},harmonyScore=Number(faceShape.harmony_score||0);
return `<div class="fsa-panel"><div class="fsa-panel-hero"><div class="fsa-panel-hero__icon">${icon("shape")}</div><div class="fsa-panel-hero__copy"><p class="fsa-panel-kicker">Shape Profile</p><h2>Face Shape: <span>${esc(primaryShape)}</span></h2><p>${esc(SHAPE_DESCRIPTIONS[shapeKey]||"This shape shows balanced facial relationships with a distinct top-to-bottom flow.")}</p></div><div class="fsa-mini-score"><span>Harmony</span><strong>${formatScore(harmonyScore)}/10</strong></div></div><div class="fsa-content-grid fsa-content-grid--shape"><section class="fsa-surface"><div class="fsa-section-heading"><h3>Characteristics</h3></div>${renderKeyValueRows(characteristics,"character")}</section><section class="fsa-surface"><div class="fsa-section-heading"><h3>All Shape Probabilities</h3></div><div class="fsa-bar-stack">${renderPercentageBars(probabilities)}</div></section></div><div class="fsa-content-grid fsa-content-grid--shape-lower"><section class="fsa-surface"><div class="fsa-section-heading"><h3>Style Recommendations</h3></div>${recommendations.length?`<ul class="fsa-bullet-list">${recommendations.map(i=>`<li>${esc(i)}</li>`).join("")}</ul>`:`<p class="fsa-muted">No tailored recommendations were returned for this portrait.</p>`}</section><section class="fsa-surface"><div class="fsa-section-heading"><h3>Facial Measurements</h3></div><div class="fsa-measurement-grid">${renderMeasurementCards(measurements)}</div></section></div></div>`;
}
function renderScoreTab(result){
const scoring=result.scoring||{},symmetry=result.symmetry||{},imageQuality=result.image_quality||{},overallPercent=clamp(Number(scoring.percentage||Number(scoring.overall_rating||0)*10),0,100),overallRating=Number(scoring.overall_rating||overallPercent/10||0),symmetryScore=Number(symmetry.symmetry_score||0),goldenRatioScore=Number(scoring.golden_ratio_score||0),beard=((result.features||{}).beard||{}),featureScores=scoring.feature_scores||{};
return `<div class="fsa-panel"><div class="fsa-score-hero"><div class="fsa-score-ring" style="--fsa-progress:${overallPercent}%;"><div class="fsa-score-ring__inner"><span>Overall</span><strong>${Math.round(overallPercent)}</strong></div></div><div class="fsa-score-main"><div class="fsa-section-heading"><h2>${esc(scoring.rating_message||"Portrait analysis complete")}</h2></div><div class="fsa-bar-stack fsa-bar-stack--hero">${renderScaleBar("Overall Rating",overallRating,10)}${renderScaleBar("Symmetry Score",symmetryScore,100,"%")}${renderScaleBar("Golden Ratio",goldenRatioScore,10)}</div></div></div><div class="fsa-content-grid"><section class="fsa-surface"><div class="fsa-section-heading"><h3>Feature Comparison</h3></div><div class="fsa-bar-stack">${renderScaleBarsFromEntries(featureScores,10)}</div></section><section class="fsa-surface"><div class="fsa-section-heading"><h3>Symmetry Breakdown</h3></div><div class="fsa-stat-grid">${renderStatCard("Eye Width",formatPercent(symmetry.eye_width_score))}${renderStatCard("Brow Length",formatPercent(symmetry.brow_length_score))}${renderStatCard("Jaw Balance",formatPercent(symmetry.jaw_balance_score))}${renderStatCard("Quality",formatPercent(imageQuality.quality_score))}</div></section></div><div class="fsa-content-grid"><section class="fsa-surface"><div class="fsa-section-heading"><h3>Image Quality</h3></div><div class="fsa-quality-grid">${renderStatCard("Lighting",titleCase(imageQuality.lighting||"Unknown"))}${renderStatCard("Face Angle",titleCase(imageQuality.face_angle||"Unknown"))}${renderStatCard("Blur Score",formatPercent(imageQuality.blur_score))}${renderStatCard("Privacy","Auto-delete active")}</div></section><section class="fsa-surface"><div class="fsa-section-heading"><h3>Additional Signals</h3></div><div class="fsa-stat-grid">${renderStatCard("Beard",beard.detected?titleCase(beard.style||"Detected"):"Not detected")}${renderStatCard("Density",beard.detected?titleCase(beard.density||"Balanced"):"N/A")}${renderStatCard("Coverage",beard.detected?titleCase(beard.coverage||"Balanced"):"N/A")}${renderStatCard("Expires",result.expires_at?formatExpiry(result.expires_at):"Not provided")}</div></section></div></div>`;
}
function renderFeatureTab(key,result){
const feature=((result.features||{})[key]||null),meta=FEATURE_META[key];if(!feature||!meta)return `<div class="fsa-panel"><div class="fsa-surface"><p class="fsa-muted">No data was returned for this section.</p></div></div>`;
const characteristics=extractCharacteristics(feature),measurements=extractMeasurements(feature),ratings=feature.ratings||{};
return `<div class="fsa-panel"><div class="fsa-panel-hero"><div class="fsa-panel-hero__icon">${meta.icon}</div><div class="fsa-panel-hero__copy"><p class="fsa-panel-kicker">Feature Detail</p><h2>${esc(meta.title)}</h2><p>${esc(meta.subtitle(feature))}</p></div></div><div class="fsa-content-grid"><section class="fsa-surface"><div class="fsa-section-heading"><h3>Characteristics</h3></div>${renderRowsFromEntries(characteristics,"character")}</section><section class="fsa-surface"><div class="fsa-section-heading"><h3>Measurements</h3></div>${renderRowsFromEntries(measurements,"measurement")}</section></div><section class="fsa-surface"><div class="fsa-section-heading"><h3>Ratings</h3></div><div class="fsa-bar-stack">${renderScaleBarsFromEntries(ratings,10)}</div></section></div>`;
}
function renderQualityChips(container,imageQuality,result){
const chips=[{label:"Lighting",value:titleCase(imageQuality.lighting||"Unknown")},{label:"Angle",value:titleCase(imageQuality.face_angle||"Unknown")},{label:"Quality",value:formatPercent(imageQuality.quality_score)},{label:"Privacy",value:result.privacy_note?"Auto-delete":"Managed"}].filter(c=>c.value&&c.value!=="-");
container.innerHTML=chips.map(c=>`<div class="fsa-chip"><span>${esc(c.label)}</span><strong>${esc(c.value)}</strong></div>`).join("");
}
function renderFeatureRatings(wrapper,container,result){
const scores=(result.scoring||{}).feature_scores||{},order=["eyebrows","eyes","lips","nose","face_shape"],entries=order.filter(k=>typeof scores[k]==="number").map(k=>[k,scores[k]]);
if(!entries.length){wrapper.classList.add("is-hidden");container.innerHTML="";return;}
wrapper.classList.remove("is-hidden");
container.innerHTML=entries.map(([k,v])=>`<div class="fsa-feature-rating"><div class="fsa-feature-rating__top"><span>${esc(formatFeatureLabel(k))}</span><strong>${formatScore(v)}</strong></div><div class="fsa-progress ${toneClass(v,10)}"><span style="width:${clamp(Number(v)/10*100,0,100)}%"></span></div></div>`).join("");
}
function renderMeasurementCards(measurements){
const keys=["eye_span","face_height","face_width","forehead_width","interocular_distance","jaw_width","mouth_width","nose_length","nose_width"],entries=keys.filter(k=>typeof measurements[k]==="number").map(k=>[k,measurements[k]]);
return entries.length?entries.map(([k,v])=>`<div class="fsa-measurement-card"><span>${esc(labelize(k))}</span><strong>${esc(formatMetricValue(k,v,true))}</strong></div>`).join(""):`<p class="fsa-muted">No measurement data was returned for this portrait.</p>`;
}
function renderKeyValueRows(obj,kind){return renderRowsFromEntries(Object.entries(obj||{}),kind);}
function renderRowsFromEntries(entries,kind){
if(!entries.length)return `<p class="fsa-muted">No data was returned for this section.</p>`;
return `<div class="fsa-data-rows">${entries.map(([k,v])=>`<div class="fsa-data-row"><span>${esc(labelize(k))}</span><strong>${esc(kind==="measurement"?formatMetricValue(k,v,false):formatCharacteristicValue(v))}</strong></div>`).join("")}</div>`;
}
function renderPercentageBars(obj){
const entries=Object.entries(obj||{}).sort((a,b)=>b[1]-a[1]);if(!entries.length)return `<p class="fsa-muted">No shape probability data was returned.</p>`;
return entries.map(([l,v])=>`<div class="fsa-progress-row"><div class="fsa-progress-row__top"><span>${esc(l)}</span><strong>${Math.round(clamp(Number(v||0),0,100))}%</strong></div><div class="fsa-progress is-gold"><span style="width:${clamp(Number(v||0),0,100)}%"></span></div></div>`).join("");
}
function renderScaleBarsFromEntries(obj,max,suffix){const entries=Object.entries(obj||{});return entries.length?entries.map(([k,v])=>renderScaleBar(labelize(k),Number(v||0),max,suffix)).join(""):`<p class="fsa-muted">No rating data was returned.</p>`;}
function renderScaleBar(label,value,max,suffix){const safe=max||10,percent=clamp(Number(value||0)/safe*100,0,100),tail=suffix==="%"?`${formatPercent(value)}`:`${formatScore(value)}${safe===10?"/10":""}`;return `<div class="fsa-progress-row"><div class="fsa-progress-row__top"><span>${esc(label)}</span><strong>${esc(tail)}</strong></div><div class="fsa-progress ${toneClass(value,safe)}"><span style="width:${percent}%"></span></div></div>`;}
function renderStatCard(label,value){return `<div class="fsa-stat-card"><span>${esc(label)}</span><strong>${esc(value??"-")}</strong></div>`;}
function extractCharacteristics(feature){return Object.entries(feature||{}).filter(([k,v])=>k!=="ratings"&&(typeof v==="string"||typeof v==="boolean"));}
function extractMeasurements(feature){return Object.entries(feature||{}).filter(([k,v])=>k!=="ratings"&&typeof v==="number");}
function showIntake(els){els.intakeShell.classList.remove("is-hidden");els.resultsShell.classList.add("is-hidden");}
function updateCopy(els,title,description){els.intakeTitle.textContent=title;els.intakeDescription.textContent=description;}
function validateFile(file){if(!file)return"Choose a portrait before submitting.";if(!/^image\/(jpeg|png|webp)$/i.test(file.type))return texts.unsupportedImage||"Please upload a supported image.";if(file.size>MAX_SIZE_BYTES)return texts.maxFileSize||"Please upload a smaller image.";return"";}
function syncTabs(tabs,active){tabs.forEach(tab=>{const on=tab.dataset.tab===active;tab.classList.toggle("is-active",on);on?tab.setAttribute("aria-current","true"):tab.removeAttribute("aria-current");});}
function setImage(img,src,fallback){if(!img||!src)return;let retried=false;img.classList.remove("is-hidden");img.onerror=()=>{if(!retried&&/^https?:\/\//i.test(src)){retried=true;window.setTimeout(()=>{img.src=src+(src.includes("?")?"&":"?")+"retry="+Date.now();},700);return;}if(fallback&&img.src!==fallback){img.src=fallback;return;}img.classList.add("is-hidden");};img.src=src;}
function setStatus(container,message,tone){if(!container)return;if(!message){container.innerHTML="";return;}container.innerHTML=`<div class="fsa-status-pill fsa-status-pill--${esc(tone||"info")}"><span>${esc(message)}</span></div>`;}
function icon(key){return({shape:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.75a4.5 4.5 0 0 0-4.5 4.5v2.5a6.5 6.5 0 0 1-1.9 4.6L4.8 15.2a2 2 0 0 0 1.4 3.4h11.6a2 2 0 0 0 1.4-3.4l-.8-.85a6.5 6.5 0 0 1-1.9-4.6v-2.5a4.5 4.5 0 0 0-4.5-4.5Z"/><path d="M9.5 20.5a2.5 2.5 0 0 0 5 0"/></svg>',score:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m12 2.8 2.5 5 5.5.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.5-.8 2.5-5Z"/></svg>',eyes:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.8-6 10-6 10 6 10 6-3.8 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg>',brows:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5c1.8-1.8 4-2.7 6.4-2.7 2.5 0 4.3.7 6.1 2.4"/><path d="M8.5 13.4a2.6 2.6 0 1 1 0-5.2 2.6 2.6 0 0 1 0 5.2Z"/><path d="M15.5 7.8c2.4 0 4.6.9 5.5 2.7"/><path d="M15.5 13.4a2.6 2.6 0 1 1 0-5.2 2.6 2.6 0 0 1 0 5.2Z"/></svg>',lips:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12s3.2-4 9-4 9 4 9 4-3.2 4-9 4-9-4-9-4Z"/><path d="M5.5 12s2 2.8 6.5 2.8 6.5-2.8 6.5-2.8"/></svg>',nose:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.6 4.5c.4 3.8-.1 7.2-1.6 10.2-.6 1.3-.2 2.9 1.5 3.6 1.7.6 4.3.3 6-.8"/><path d="M10 19.8c1.8 1 3.8 1 5.9 0"/></svg>'})[key]||"";}
function labelize(input){return String(input||"").replace(/_/g," ").replace(/\bavg\b/gi,"Average").replace(/\bpct\b/gi,"Percent").replace(/\bapi\b/gi,"API").replace(/\s+/g," ").trim().replace(/\b\w/g,c=>c.toUpperCase());}
function titleCase(input){return String(input||"").replace(/[_-]/g," ").replace(/\s+/g," ").trim().replace(/\b\w/g,c=>c.toUpperCase());}
function formatFeatureLabel(key){return key==="face_shape"?"Face Shape":labelize(key);}
function formatCharacteristicValue(v){return typeof v==="boolean"?(v?"Yes":"No"):titleCase(v);}
function formatMetricValue(key,value,usePixels){const n=Number(value||0);if(/pct/i.test(key))return`${n.toFixed(1)}%`;if(/ratio/i.test(key))return n.toFixed(2);if(usePixels)return`${n.toFixed(1)}px`;if(Math.abs(n)>=10)return n.toFixed(1);return n.toFixed(2);}
function formatScore(v){return Number(v||0).toFixed(1);}
function formatPercent(v){if(v===null||v===undefined||v==="")return"-";return`${Number(v).toFixed(1)}%`;}
function formatExpiry(v){const d=new Date(v);return Number.isNaN(d.getTime())?"Not provided":d.toLocaleString(undefined,{month:"short",day:"numeric",hour:"numeric",minute:"2-digit"});}
function toneClass(v,max){const r=(Number(v||0))/(Number(max||10)||10);return r>=0.8?"is-green":r>=0.6?"is-gold":"is-coral";}
function clamp(v,min,max){return Math.min(Math.max(v,min),max);}
function esc(v){return String(v??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\"/g,"&quot;").replace(/'/g,"&#39;");}
})();
