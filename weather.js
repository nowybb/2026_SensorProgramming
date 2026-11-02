// 외부 날씨: 브라우저 현재 위치 + Open-Meteo (별도의 API 키 불필요)
// 위치 정보는 저장하지 않으며, 날씨 요청에만 사용합니다.
(() => {
  'use strict';
  const el = id => document.getElementById(id);
  const refresh = el('weather-refresh');
  let requestNumber = 0;
  let controller = null;

  function describe(code, day) {
    if (code === 0) return ['맑음', day ? '☀️' : '🌙'];
    if (code === 1) return ['대체로 맑음', day ? '🌤️' : '🌙'];
    if (code === 2) return ['구름 조금', '⛅'];
    if (code === 3) return ['흐림', '☁️'];
    if ([45,48].includes(code)) return ['안개', '🌫️'];
    if ([51,53,55,56,57].includes(code)) return ['이슬비', '🌦️'];
    if ([61,63,65,66,67,80,81,82].includes(code)) return ['비', '🌧️'];
    if ([71,73,75,77,85,86].includes(code)) return ['눈', '❄️'];
    if ([95,96,99].includes(code)) return ['뇌우', '⛈️'];
    return ['날씨 정보', '☁️'];
  }
  function advice(code, chance, humidity) {
    if ([51,53,55,56,57,61,63,65,66,67,80,81,82,95,96,99].includes(code) || (Number.isFinite(chance) && chance >= 60)) {
      return '비에 젖은 신발은 물기를 닦은 뒤 보관하고, 내부 습도를 확인해 주세요.';
    }
    if ([71,73,75,77,85,86].includes(code)) return '눈에 젖은 신발의 물기를 제거한 뒤 충분히 환기해 주세요.';
    if (humidity >= 75) return '바깥 공기가 습한 편이에요. 신발장 내부 습도도 함께 확인해 주세요.';
    return '신발 보관 전 물기를 확인하고, 신발장 내부 상태를 주기적으로 점검해 주세요.';
  }
  function fail(reason) {
    el('weather-location').textContent = '현재 위치 날씨';
    el('weather-description').textContent = '날씨 데이터를 불러오지 못했습니다';
    el('weather-rain').textContent = '오늘 강수확률 —';
    el('weather-temp').textContent = '--°';
    el('weather-icon').textContent = '—';
    el('weather-recommendation').textContent = '실제 날씨 정보를 표시할 수 없습니다. 위치 권한과 인터넷 연결을 확인한 뒤 다시 시도해 주세요.';
    el('weather-update').textContent = reason || '날씨 정보 연결 실패';
  }
  function position() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation || !window.isSecureContext) {
        reject(new Error('위치 기능은 HTTPS 또는 localhost에서만 사용할 수 있습니다.'));
        return;
      }
      navigator.geolocation.getCurrentPosition(resolve, error => {
        const msg = error.code === 1 ? '위치 접근이 거부되었습니다. 브라우저 권한을 확인해 주세요.'
          : error.code === 2 ? '현재 위치를 확인할 수 없습니다.' : '위치 확인 시간이 초과되었습니다.';
        reject(new Error(msg));
      }, {enableHighAccuracy:false, timeout:12000, maximumAge:5*60*1000});
    });
  }
  async function loadWeather() {
    const currentRequest = ++requestNumber;
    if (controller) controller.abort();
    controller = new AbortController();
    const signal = controller.signal;
    refresh.disabled = true;
    el('weather-location').textContent = '현재 위치 확인 중…';
    el('weather-description').textContent = '날씨 데이터를 불러오는 중…';
    el('weather-rain').textContent = '오늘 강수확률 —';
    el('weather-temp').textContent = '--°';
    el('weather-icon').textContent = '📍';
    el('weather-update').textContent = '위치 사용 권한을 허용해 주세요';
    try {
      const geo = await position();
      if (currentRequest !== requestNumber) return;
      const {latitude, longitude} = geo.coords;
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) throw new Error('위치 좌표를 확인할 수 없습니다.');
      el('weather-location').textContent = '📍 현재 위치 기준';
      el('weather-update').textContent = '날씨 API 연결 중…';
      const query = new URLSearchParams({
        latitude:String(latitude), longitude:String(longitude),
        current:'temperature_2m,relative_humidity_2m,weather_code,is_day',
        daily:'precipitation_probability_max', timezone:'auto', forecast_days:'1'
      });
      const timer = setTimeout(() => controller.abort(), 12000);
      let response;
      try {
        response = await fetch('https://api.open-meteo.com/v1/forecast?' + query, {signal,cache:'no-store'});
      } finally { clearTimeout(timer); }
      if (!response.ok) throw new Error('날씨 API 응답 오류: ' + response.status);
      const data = await response.json();
      if (currentRequest !== requestNumber) return;
      const now = data.current;
      if (!now || !Number.isFinite(now.temperature_2m) || !Number.isFinite(now.weather_code) || !Number.isFinite(now.relative_humidity_2m)) {
        throw new Error('날씨 데이터 형식이 올바르지 않습니다.');
      }
      const chance = data.daily?.precipitation_probability_max?.[0];
      const [label, icon] = describe(now.weather_code, Boolean(now.is_day));
      el('weather-description').textContent = `${label} · 외부 습도 ${Math.round(now.relative_humidity_2m)}%`;
      el('weather-rain').textContent = Number.isFinite(chance) ? `오늘 최고 강수확률 ${Math.round(chance)}% (예보)` : '오늘 강수확률 정보 없음';
      el('weather-temp').textContent = `${Math.round(now.temperature_2m)}°`;
      el('weather-icon').textContent = icon;
      el('weather-recommendation').textContent = advice(now.weather_code, chance, now.relative_humidity_2m);
      el('weather-update').textContent = `날씨 기준 ${now.time?.replace('T',' ') || '시간 미제공'} · ${data.current_units?.temperature_2m || '°C'}`;
    } catch (error) {
      if (currentRequest !== requestNumber) return;
      console.warn('날씨 또는 위치 조회 실패:', error);
      fail(error.message);
    } finally {
      if (currentRequest === requestNumber) refresh.disabled = false;
    }
  }
  refresh.addEventListener('click', loadWeather);
  loadWeather();
  setInterval(() => { if (!document.hidden) loadWeather(); }, 10*60*1000);
})();
