import { getSgisToken, jsonResponse } from './service.js';

export async function onRequest(context) {
    const { request, env } = context;
    const url = new URL(request.url);
    const adm_cd = url.searchParams.get('adm_cd') || '';
    const year = url.searchParams.get('year') || '2024';

    const token = await getSgisToken(env);
    if (!token) return jsonResponse({ error: 'Failed to get SGIS token' }, 500);

    const SGIS_BASE = 'https://sgisapi.kostat.go.kr/OpenAPI3';
    let apiUrl = `${SGIS_BASE}/boundary/hadmarea.geojson?accessToken=${token}&year=${year}&adm_cd=${adm_cd}&low_search=1`;
    
    let resp = await fetch(apiUrl);
    let data = await resp.json();

    // 부천시 원미/소사/오정구 등 신규 행정구역 지원을 위한 폴백
    if (String(data.errCd) === '-100') {
        apiUrl = `${SGIS_BASE}/boundary/hadmarea.geojson?accessToken=${token}&year=2023&adm_cd=${adm_cd}&low_search=1`;
        resp = await fetch(apiUrl);
        data = await resp.json();
    }

    return jsonResponse(data);
}
