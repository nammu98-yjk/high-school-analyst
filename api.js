export const SGIS_CONSUMER_KEY = 'b9f5f345dcd24b989899';
export const SGIS_CONSUMER_SECRET = 'f35f7ef12a774550be0e';

/**
 * 모든 데이터는 Python 백엔드(/api/*)에서 처리.
 * 프론트엔드는 백엔드 API만 호출합니다.
 */
export class ApiService {
    constructor() {}

    async init() {
        // 토큰 상태 확인
        const res = await fetch('/api/token-status');
        const data = await res.json();
        console.log('[API] Token Status:', data);
        return data.hasToken;
    }

    async getStages(cd = '') {
        const url = cd ? `/api/stages?cd=${cd}` : '/api/stages';
        const res = await fetch(url);
        return await res.json();
    }

    async getBoundary(adm_cd) {
        const url = `/api/boundary?adm_cd=${adm_cd}`;
        const res = await fetch(url);
        return await res.json();
    }

    async analyze(adm_cd, name, level = 'dong') {
        const url = `/api/analyze?adm_cd=${adm_cd}&name=${encodeURIComponent(name)}&level=${level}`;
        const res = await fetch(url);
        return await res.json();
    }
}
