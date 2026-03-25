import { getSgisToken, jsonResponse } from './service.js';

export async function onRequest(context) {
    const { env } = context;
    const token = await getSgisToken(env);
    
    return jsonResponse({
        hasToken: token !== null,
        token: token ? (token.substring(0, 10) + '...') : null
    });
}
