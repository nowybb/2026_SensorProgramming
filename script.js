// 센서 데이터는 시안용. 공공장소용 화면 제한도 브라우저 수준의 시연 기능이며 인증/보안 기능은 아님.
const demo=[{id:1,occupied:true,drying:true,temp:24.0,humidity:65},{id:2,occupied:false,drying:false,temp:23.1,humidity:44}];
const key='pposong_demo_mode_v1';
let mode=localStorage.getItem(key)==='public'?'public':'home';
const params=new URLSearchParams(location.search);
const qrParam=params.get('cabinet');
// 주소로 선택된 칸은 접속 세션 동안 고정: 화면 버튼으로 다른 칸에 전환하지 않음.
const qrCabinet=(qrParam==='1'||qrParam==='2')?Number(qrParam):null;
let selected=qrCabinet||1;
let currentPage='home';let toastTimer;
const $=id=>document.getElementById(id);
function showToast(msg){const el=$('toast');el.textContent=msg;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),2600)}
function stateLabel(c){return !c.occupied?'비어 있음':c.drying?'건조 중':'보관 중'}
function publicUserView(){return mode==='public' && currentPage!=='admin'}
function render(){
  $('home-mode-label').textContent=mode==='home'?'가정용 모드':'공공장소용 모드';
  $('current-mode-badge').textContent=mode==='home'?'가정용':'공공장소용';
  $('mode-description').textContent=mode==='home'?'로그인 없이 두 칸의 상태를 확인할 수 있어요.':'QR로 접속한 해당 칸만 표시합니다. 실제 접근 제어는 추후 서버에서 구현해야 해요.';
  // 가정용에서만 전체 칸 목록 렌더링
  $('home-grid').innerHTML=mode==='home'?demo.map(c=>`<button class="cabinet-card" onclick="openCabinet(${c.id})"><div class="row"><strong>${String(c.id).padStart(2,'0')}번 칸</strong><span class="badge ${c.occupied?'red':'green'}">${c.occupied?'사용 중':'빈 칸'}</span></div><div class="art">${c.occupied?'👟':'🧺'}</div><div class="state">${stateLabel(c)} · 습도 ${c.humidity}%</div></button>`).join(''):'';
  $('cabinet-list').innerHTML=mode==='home'?demo.map(c=>`<button class="list-item" onclick="openCabinet(${c.id})"><div><strong>${c.id}번 신발장</strong><p>${stateLabel(c)} · ${c.humidity}% RH · 팬 ${c.drying?'ON':'OFF'}</p></div><span class="chev">›</span></button>`).join(''):'';
  $('cabinet-list-note').textContent=mode==='home'?'가정용 모드: 두 칸의 상태를 확인할 수 있어요.':'';
  $('qr-home-link').classList.toggle('hidden',mode==='public');
  $('qr-admin-link').classList.toggle('hidden',mode!=='public');
  $('detail-back').textContent=mode==='public'?'← QR 시작 화면':'← 신발장 목록';
  document.querySelector('input[name="mode"][value="'+mode+'"]').checked=true;
  document.querySelectorAll('.setting-card').forEach(x=>x.classList.remove('selected'));
  $(mode==='home'?'home-choice':'public-choice').classList.add('selected');
  $('history-content').innerHTML='<div class="card history-empty-card"><div class="empty-illustration">🗒️</div><h3>아직 이용 기록이 없어요</h3><p class="small muted mt-9">서버와 데이터베이스를 연결하면 이용 내역이 여기에 표시돼요.</p></div>';
}
function navigate(page){
  // 공공장소용: QR로 접속한 칸 외의 일반 화면은 숨김. 관리자는 별도 프로토타입 경로.
  if(mode==='public' && !['admin','qr','detail','qr-required'].includes(page)) page=qrCabinet?'qr':'qr-required';
  if(mode==='public' && page==='detail' && !qrCabinet){page='qr-required';}
  if(page==='qr' && !qrCabinet && mode==='public')page='qr-required';
  if(page==='detail' && mode==='public')selected=qrCabinet;
  currentPage=page;
  document.body.classList.toggle('qr-entry-active',page==='qr'||page==='qr-required');
  document.body.classList.toggle('public-user-active',publicUserView());
  document.querySelectorAll('.page').forEach(el=>el.classList.toggle('active',el.id==='page-'+page));
  const navPage=(page==='detail')?'cabinets':page==='admin'?'settings':page;
  document.querySelectorAll('.nav-btn').forEach(el=>el.classList.toggle('active',el.dataset.nav===navPage));
  if(page==='detail')renderDetail();
  if(page==='admin')render();
  window.scrollTo({top:0,behavior:'instant'});
}
function openCabinet(id){
  if(mode==='public'){
    if(!qrCabinet||id!==qrCabinet){showToast('공공장소용에서는 QR로 접속한 칸만 확인할 수 있어요.');return;}
  }
  if(!demo.some(c=>c.id===id))return;
  selected=id;navigate('detail');
}
function backFromDetail(){navigate(mode==='public'?'qr':'cabinets')}
function renderQrLanding(){const n=String(selected).padStart(2,'0');$('qr-cabinet-title').textContent=selected+'번';$('qr-selected-cabinet').textContent=n+'번 칸';}
function enterQrCabinet(){if(mode==='public'&&!qrCabinet){navigate('qr-required');return;}openCabinet(selected)}
function renderDetail(){
  const c=demo.find(x=>x.id===selected);if(!c)return;
  $('detail-title').textContent=c.id+'번 신발장';$('detail-badge').textContent=stateLabel(c);$('detail-badge').className='badge '+(c.occupied?'red':'green');
  $('detail-icon').textContent=c.occupied?'👟':'🧺';$('detail-status').textContent=!c.occupied?'신발장이 비어 있어요':c.drying?'신발을 건조하고 있어요':'신발을 보관 중이에요';
  $('detail-desc').textContent=c.drying?'환기 팬이 작동하고 있어요.':'환기 팬이 꺼져 있어요.';
  $('detail-temp').textContent=c.temp.toFixed(1)+'°C';$('detail-humidity').textContent=c.humidity+'%';
  $('detail-fan').textContent=c.drying?'ON':'OFF';$('detail-shoes').textContent=c.occupied?'있음':'없음';
  $('detail-access-note').textContent=mode==='public'?'공공장소용: 화면에서는 QR로 선택한 칸만 표시합니다. 실제 문 제어와 접근 권한 인증은 서버 연결 후 가능합니다.':'가정용: 현재 서보모터가 연결되지 않았습니다.';
  $('door-button').disabled=true;
}
function mockOpenDoor(){showToast('🚪 아직 문 제어 장치가 연결되지 않았어요.')}
function saveMode(){
  const target=document.querySelector('input[name="mode"]:checked');if(!target)return;
  mode=target.value;localStorage.setItem(key,mode);render();
  // 관리자 설정은 시연을 위해 현재 페이지 유지; 사용자 화면으로 이동하려면 칸별 QR 접속.
  navigate('admin');showToast((mode==='home'?'가정용':'공공장소용')+' 모드가 이 브라우저에 저장되었어요.');
}
let adminReturnPage='qr-required';
function openPrototypeAdmin(){
  adminReturnPage=currentPage;
  navigate('admin');
}
function backFromAdmin(){
  if(mode==='public')navigate(qrCabinet?'qr':'qr-required');
  else navigate(adminReturnPage==='admin'?'settings':adminReturnPage);
}
function toggleNoQrChoices(){
  if(mode!=='public')return;
  const choices=$('no-qr-choices');
  const willOpen=choices.classList.contains('hidden');
  choices.classList.toggle('hidden',!willOpen);
  $('no-qr-button').setAttribute('aria-expanded',String(willOpen));
}
function previewCabinet(id){
  // 실제 QR 진입 흐름과 동일하게 URL을 변경해서 테스트
  const u=new URL(location.href);u.searchParams.delete('admin');u.searchParams.set('cabinet',String(id));location.href=u.href;
}
document.querySelectorAll('input[name="mode"]').forEach(r=>r.addEventListener('change',()=>{
  document.querySelectorAll('.setting-card').forEach(x=>x.classList.remove('selected'));
  $(r.value==='home'?'home-choice':'public-choice').classList.add('selected');
}));
async function copyQrLinks(){
  const u=new URL(location.href);u.search='';u.hash='';const base=u.href;
  const content=`1번 칸: ${base}?cabinet=1\n2번 칸: ${base}?cabinet=2`;
  try{await navigator.clipboard.writeText(content);showToast('칸별 페이지 주소가 복사됐어요.')}catch(e){showToast('복사가 제한돼요. 주소 끝에 ?cabinet=1 또는 2를 붙여 주세요.')}
}
render();
if(params.get('admin')==='1')navigate('admin');
else if(qrCabinet){selected=qrCabinet;renderQrLanding();navigate('qr');}
else if(mode==='public')navigate('qr-required');
else navigate('home');
