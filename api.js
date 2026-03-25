export class ApiService {
    constructor() { }

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
