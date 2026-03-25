const SGIS_BASE = 'https://sgisapi.kostat.go.kr/OpenAPI3';

/**
 * SGIS 토큰을 가져오거나 갱신합니다.
 * Cloudflare KV를 사용하면 토큰을 재사용할 수 있습니다.
 */
export async function getSgisToken(env) {
    // KV가 설정되어 있다면 먼저 확인
    if (env.SGIS_KV) {
        const cached = await env.SGIS_KV.get('sgis_token');
        if (cached) return cached;
    }

    const key = env.SGIS_CONSUMER_KEY || 'b9f5f345dcd24b989899';
    const secret = env.SGIS_CONSUMER_SECRET || 'f35f7ef12a774550be0e';
    
    const url = `${SGIS_BASE}/auth/authentication.json?consumer_key=${key}&consumer_secret=${secret}`;
    const resp = await fetch(url);
    const data = await resp.json();
    
    if (data && data.errCd === 0) {
        const token = data.result.accessToken;
        // KV가 있다면 저장 (토큰은 보통 4시간 유지)
        if (env.SGIS_KV) {
            await env.SGIS_KV.put('sgis_token', token, { expirationTtl: 14000 }); // 약 3시간 50분
        }
        return token;
    }
    return null;
}

/**
 * KV 캐시 도우미
 */
export async function getCache(env, key) {
    if (env.SGIS_KV) {
        const cached = await env.SGIS_KV.get(key);
        return cached ? JSON.parse(cached) : null;
    }
    return null;
}

export async function setCache(env, key, value, ttl = 86400 * 7) {
    if (env.SGIS_KV) {
        await env.SGIS_KV.put(key, JSON.stringify(value), { expirationTtl: ttl });
    }
}

/**
 * 공통 응답 처리
 */
export function jsonResponse(data, status = 200) {
    return new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Origin': '*'
        }
    });
}
