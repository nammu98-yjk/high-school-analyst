import { getSgisToken, jsonResponse } from './service.js';

export async function onRequest(context) {
    const { request, env } = context;
    const url = new URL(request.url);
    const cd = url.searchParams.get('cd') || '';

    let token = await getSgisToken(env);
    if (!token) return jsonResponse({ error: 'Failed to get SGIS token' }, 500);

    const SGIS_BASE = 'https://sgisapi.kostat.go.kr/OpenAPI3';
    let apiUrl = cd ? `${SGIS_BASE}/addr/stage.json?accessToken=${token}&cd=${cd}` : `${SGIS_BASE}/addr/stage.json?accessToken=${token}`;
    
    let resp = await fetch(apiUrl);
    let data = await resp.json();

    // 토큰 만료 처리
    if (data.errCd === -401) {
        // KV가 있다면 토큰 삭제 후 다시 가져오기
        if (env.SGIS_KV) await env.SGIS_KV.delete('sgis_token');
        token = await getSgisToken(env);
        apiUrl = cd ? `${SGIS_BASE}/addr/stage.json?accessToken=${token}&cd=${cd}` : `${SGIS_BASE}/addr/stage.json?accessToken=${token}`;
        resp = await fetch(apiUrl);
        data = await resp.json();
    }

    if (data.errCd === 0 && !cd) {
        // 수도권(서울, 인천, 경기) 필터링
        const filtered = data.result.filter(s => ["11", "23", "31"].includes(s.cd));
        return jsonResponse(filtered);
    }

    return jsonResponse(data.result || []);
}
