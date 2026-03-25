import { getSgisToken, jsonResponse, getCache, setCache } from './service.js';
import SCHOOLS_DB from '../db/schools_db.json';
import POPULATION_DB from '../db/population_db.json';

const SGIS_BASE = 'https://sgisapi.kostat.go.kr/OpenAPI3';
const SCHOOL_API_KEY = '709cf20f70e64310bc84a0c5d945a9ea';

const SGIS_TO_SI_SIDO = {
    "11": "11", "23": "28", "28": "28", "31": "41", "41": "41"
};

const SGG_MAP = {
    "종로구": "11110", "중구": "11140", "용산구": "11170", "성동구": "11200", "광진구": "11215", "동대문구": "11230", "중랑구": "11260", "성북구": "11290", "강북구": "11305", "도봉구": "11320", "노원구": "11350", "은평구": "11380", "서대문구": "11410", "마포구": "11440", "양천구": "11470", "강서구": "11500", "구로구": "11530", "금천구": "11545", "영등포구": "11560", "동작구": "11590", "관악구": "11620", "서초구": "11650", "강남구": "11680", "송파구": "11710", "강동구": "11740",
    "미추홀구": "28177", "연수구": "28185", "남동구": "28200", "부평구": "28237", "계양구": "28245", "강화군": "28710", "옹진군": "28720", "서구": "28260", "동구": "28140",
    "장안구": "41111", "권선구": "41113", "팔달구": "41115", "영통구": "41117", "수정구": "41131", "중원구": "41133", "분당구": "41135", "의정부시": "41150", "만안구": "41171", "동안구": "41173", "부천시": "41190", "원미구": "41192", "소사구": "41194", "오정구": "41196", "광명시": "41210", "평택시": "41220", "동두천시": "41250", "상록구": "41271", "단원구": "41273", "덕양구": "41281", "일산동구": "41285", "일산서구": "41287", "과천시": "41290", "구리시": "41310", "남양주시": "41360", "오산시": "41370", "시흥시": "41390", "군포시": "41410", "의왕시": "41430", "하남시": "41450", "처인구": "41461", "기흥구": "41463", "수지구": "41465", "파주시": "41480", "이천시": "41500", "안성시": "41550", "김포시": "41570", "화성시": "41590", "광주시": "41610", "양주시": "41630", "포천시": "41650", "여주시": "41670", "연천군": "41800", "가평군": "41820", "양평군": "41830"
};

const SGG_MAP_ADV = {
    "11중구": "11140", "23중구": "28110", "23동구": "28140", "23서구": "28260",
    "28중구": "28110", "28동구": "28140", "28서구": "28260"
};

function safeInt(val) {
    if (!val || val === 'N/A') return 0;
    return parseInt(String(val).replace(/,/g, '')) || 0;
}

/**
 * API 호출 도우미 (캐싱 포함)
 */
async function fetchSgisWithCache(path, token, env) {
    const cacheKey = `sgis_${path.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const cached = await getCache(env, cacheKey);
    if (cached) return cached;

    const url = `${SGIS_BASE}${path}${path.includes('?') ? '&' : '?'}accessToken=${token}`;
    const resp = await fetch(url);
    const data = await resp.json();
    
    if (data && data.errCd === 0) {
        await setCache(env, cacheKey, data);
    }
    return data;
}

export async function onRequest(context) {
    try {
        const { request, env } = context;
        const url = new URL(request.url);
        const adm_cd = url.searchParams.get('adm_cd');
        const name = url.searchParams.get('name');
        const level = url.searchParams.get('level') || 'dong';

        if (!adm_cd) return jsonResponse({ error: 'adm_cd required' }, 400);

        const token = await getSgisToken(env);
        if (!token) return jsonResponse({ error: 'Token failed' }, 500);

        const result = await analyzeArea(adm_cd, name, level, token, env);
        return jsonResponse(result);
    } catch (err) {
        console.error('[API Error]', err);
        return jsonResponse({ error: err.message, stack: err.stack }, 500);
    }
}

async function analyzeArea(adm_cd, area_name, level, token, env) {
    if (level === 'dong') {
        const district_cd_sgis = adm_cd.substring(0, 5);
        const [bulkAcad, bulkMid, bulkHigh, bulkHouseTot, bulkHouseApt, bulkPop] = await Promise.all([
            getBulkCompany(adm_cd, 'P855', token, env),
            getBulkCompany(adm_cd, 'P85211', token, env),
            getBulkCompany(adm_cd, 'P85212', token, env),
            getBulkHouse(adm_cd, '00', token, env),
            getBulkHouse(adm_cd, '02', token, env),
            getBulkPop(adm_cd, token, env)
        ]);
        const bulkData = { academy: bulkAcad, middle: bulkMid, high: bulkHigh, house: bulkHouseTot, apt: bulkHouseApt, population: bulkPop };
        const [elem_dist, mid_dist, high_dist] = await Promise.all([
            getCompanyCount(district_cd_sgis, 'P8512', token, env),
            getCompanyCount(district_cd_sgis, 'P85211', token, env),
            getCompanyCount(district_cd_sgis, 'P85212', token, env)
        ]);
        const districtCounts = { elem_dist, mid_dist, high_dist };
        return await analyzeSingleAreaWithData(adm_cd, area_name, districtCounts, bulkData);
    } else {
        const subData = await fetchSgisWithCache(`/addr/stage.json?cd=${adm_cd}`, token, env);
        const subAreas = (subData && subData.errCd === 0) ? subData.result : [];

        if (subAreas.length === 0) {
            return await analyzeArea(adm_cd, area_name, 'dong', token, env);
        }

        const district_cd_sgis = adm_cd.substring(0, 5);
        const [bulkAcad, bulkMid, bulkHigh, bulkHouseTot, bulkHouseApt, bulkPop] = await Promise.all([
            getBulkCompany(district_cd_sgis, 'P855', token, env),
            getBulkCompany(district_cd_sgis, 'P85211', token, env),
            getBulkCompany(district_cd_sgis, 'P85212', token, env),
            getBulkHouse(district_cd_sgis, '00', token, env),
            getBulkHouse(district_cd_sgis, '02', token, env),
            getBulkPop(district_cd_sgis, token, env)
        ]);

        const bulkData = { academy: bulkAcad, middle: bulkMid, high: bulkHigh, house: bulkHouseTot, apt: bulkHouseApt, population: bulkPop };

        const [elem_dist, mid_dist, high_dist] = await Promise.all([
            getCompanyCount(district_cd_sgis, 'P8512', token, env),
            getCompanyCount(district_cd_sgis, 'P85211', token, env),
            getCompanyCount(district_cd_sgis, 'P85212', token, env)
        ]);
        const districtCounts = { elem_dist, mid_dist, high_dist };

        const results = await Promise.all(subAreas.map(area => analyzeSingleAreaWithData(area.cd, area.addr_name, districtCounts, bulkData)));
        const filtered = results.filter(r => r !== null);
        filtered.sort((a, b) => b.totalScore - a.totalScore);
        
        return filtered.length > 0 ? filtered : [await analyzeSingleAreaWithData(adm_cd, area_name, districtCounts, bulkData)];
    }
}

/**
 * 미리 준비된 데이터를 사용하여 단일 행정구역 분석 (네트워크 통신 최소화)
 */
async function analyzeSingleAreaWithData(adm_cd, area_name, districtCounts, bulkData) {
    const district_cd_sgis = adm_cd.substring(0, 5);
    const sido_prefix = adm_cd.substring(0, 2);
    const standard_sido = SGIS_TO_SI_SIDO[sido_prefix] || sido_prefix;

    let district_name = area_name;

    // 1. DB 조회
    let dbEntry = null;
    const searchName = area_name.replace(/\s/g, ''); 
    for (const [code, entry] of Object.entries(SCHOOLS_DB)) {
        if (code.substring(0, 2) === standard_sido) {
            const dbName = (entry.name || "").replace(/\s/g, '');
            if (searchName === dbName || searchName.includes(dbName) || dbName.includes(searchName)) {
                dbEntry = entry;
                break;
            }
        }
    }

    // 2. 인프라 데이터 (BulkData 활용)
    const academy = bulkData.academy[adm_cd] || 0;
    const mid_dong = bulkData.middle[adm_cd] || 0;
    const high_dong = bulkData.high[adm_cd] || 0;
    const house = bulkData.house[adm_cd] || 0;
    const h_apt = bulkData.apt[adm_cd] || 0;
    const population = bulkData.population[adm_cd] || 0;

    const apartment_ratio = house > 0 ? Number((h_apt / house * 100).toFixed(1)) : 0;
    const { elem_dist, mid_dist, high_dist } = districtCounts;

    // 3. 학군지 데이터
    let schools_raw = [];
    let district_gpa_index = -1;
    let district_high_gpa = {};
    let std_dev = 0;
    let a_rate = 0;

    if (dbEntry) {
        schools_raw = dbEntry.students || [];
        const stats = dbEntry.elite_stats || {};
        district_high_gpa = dbEntry.high_gpa || {};
        district_gpa_index = stats.elite_rate !== undefined ? stats.elite_rate : -1;
    } else {
        const sgg_standard = standard_sido + adm_cd.substring(2, 5);
        schools_raw = await fetchSchoolInfoStudents(sgg_standard, district_name);
    }

    const avg_students = schools_raw.length > 0 ? Math.round(schools_raw.reduce((a, b) => a + b.avg, 0) / schools_raw.length) : 0;

    // 4. 동 단위 학생 수
    const sido_nm = { "11": "서울특별시", "23": "인천광역시", "28": "인천광역시", "31": "경기도" }[sido_prefix] || "경기도";
    let dong_students = 0;
    let dong_students_source = "추정치";
    const search_key = `${sido_nm} ${district_name} ${area_name}`;
    let pop_data = POPULATION_DB[search_key];

    if (!pop_data) {
        const matches = Object.keys(POPULATION_DB).filter(k => k.startsWith(sido_nm) && k.endsWith(area_name) && k.includes(district_name));
        if (matches.length > 0) pop_data = POPULATION_DB[matches[0]];
    }

    if (pop_data) {
        dong_students = pop_data.total_students || 0;
        dong_students_source = "주민등록인구(13-18세)";
    } else {
        const avg_mid = 270 * 3;
        const avg_high = avg_students > 0 ? avg_students * 3 : 200 * 3;
        dong_students = (mid_dong * avg_mid) + (high_dong * avg_high);
        if (dong_students === 0) {
            dong_students = Math.round(population * 0.08);
            dong_students_source = "인구비례 추정(8%)";
        } else {
            dong_students_source = "학교수 기반 추정";
        }
    }

    // 5. 점수 산출
    const denom = high_dist > 0 ? high_dist : 0.1;
    const school_balance_score = Math.min(Math.round(((elem_dist + mid_dist) / denom) * 20), 100);

    let academy_score = 0;
    let academy_note = "";
    if (dong_students > 0) {
        const academy_per_100 = academy / (dong_students / 100);
        const score_relative = Math.min(Math.round((academy_per_100 / 4.0) * 100), 100);
        const score_absolute = Math.min(Math.round((academy / 100) * 100), 100);
        academy_score = Math.round(score_relative * 0.5 + score_absolute * 0.5);
        academy_note = `복합점수: ${academy_score}점 (밀도 ${score_relative}점 + 규모 ${score_absolute}점) | 학원 ${academy}개 / 학생 100명당 ${academy_per_100.toFixed(2)}개`;
    } else {
        const academy_ratio = academy / (population / 1000 + 0.1);
        academy_score = Math.min(Math.round((academy_ratio / 5.0) * 100), 100);
        academy_note = `공공데이터 공백으로 인구 기준 산출 (${academy_ratio.toFixed(2)}/1000명)`;
    }

    const apartment_score = Math.min(Math.max(Math.round((apartment_ratio - 40) / 50 * 100), 0), 100);

    let students_score = 0;
    let data_source_note = "학교알리미 실데이터";
    if (avg_students > 0) {
        students_score = Math.min(Math.round((avg_students / 300) * 100), 100);
    } else {
        // 동 단위 인구 데이터 활용
        const pop_per_school = population / (high_dist + 0.1);
        students_score = Math.min(Math.max(100 - Math.round((pop_per_school / 20000) * 50), 0), 100);
        data_source_note = "데이터 공백 (인구 기반 추정치)";
    }

    let gpa_intensity_score = 0;
    let intensity_note = "";
    if (district_gpa_index >= 0) {
        const score_a = Math.max(0, Math.min(100, 100 - (district_gpa_index / 12.0) * 100));
        if (district_high_gpa && !district_high_gpa.error) {
            std_dev = district_high_gpa.mean_std_dev || 0;
            a_rate = district_high_gpa.mean_a_rate || 0;
        }
        if (std_dev > 0) {
            const score_b = Math.max(0, Math.min(100, (std_dev - 12) / 8.0 * 100));
            gpa_intensity_score = Math.round(score_a * 0.5 + score_b * 0.5);
        } else {
            gpa_intensity_score = Math.round(score_a);
        }
        
        let label = "C";
        if (gpa_intensity_score >= 80) label = 'A (블루오션 / 내신 확보 매우 유리)';
        else if (gpa_intensity_score >= 60) label = 'B (내신 확보 유리)';
        else if (gpa_intensity_score >= 40) label = 'C (일반 学군)';
        else if (gpa_intensity_score >= 20) label = 'D (내신 경쟁 치열)';
        else label = 'E (레드오션 / 내신 경쟁 초극심)';
        intensity_note = `${label} → [중학] 엘리트 진학 ${district_gpa_index}%` + (std_dev > 0 ? ` | [고교] 표준편차 ${std_dev} / A등급 ${a_rate}%` : "");
    } else {
        intensity_note = "데이터 수집 제한 (확인 불가)";
    }

    const total = Math.round(
        school_balance_score * 0.05 +
        students_score * 0.25 +
        academy_score * 0.25 +
        apartment_score * 0.15 +
        gpa_intensity_score * 0.30
    );

    const grade = total >= 90 ? 'S' : total >= 80 ? 'A' : total >= 70 ? 'B' : total >= 60 ? 'C' : total >= 50 ? 'D' : 'E';

    return {
        name: area_name,
        adm_cd: adm_cd,
        districtName: district_name,
        totalScore: total,
        grade: grade,
        avgStudents: avg_students,
        gpaIntensity: district_gpa_index > 0 ? Number(district_gpa_index.toFixed(1)) : 0,
        schoolsRaw: schools_raw,
        raw: {
            elementary: elem_dist, middle: mid_dist, high: high_dist,
            academy: academy, dongStudents: dong_students,
            house: house, apartmentRatio: apartment_ratio, population: population,
            eliteRate: district_gpa_index > 0 ? Number(district_gpa_index.toFixed(1)) : 0,
            highStdDev: std_dev, highARate: a_rate
        },
        scores: {
            schoolBalance: school_balance_score,
            academyDensity: academy_score,
            apartmentDensity: apartment_score,
            studentsPerHigh: students_score,
            gpaIntensity: gpa_intensity_score
        },
        notes: {
            gpaIntensity: intensity_note,
            studentsPerHigh: `${data_source_note} 기반 점수.`,
            academyDensity: academy_note
        }
    };
}

// === 상세 수집 함수들 ===
// === 벌크 수집 함수들 (SGIS low_search=1 최적화) ===
async function getBulkCompany(adm_cd, class_code, token, env) {
    const url = `/stats/company.json?adm_cd=${adm_cd}&year=2023&class_code=${class_code}&low_search=1`;
    const data = await fetchSgisWithCache(url, token, env);
    const map = {};
    if (data && data.errCd === 0 && data.result) {
        data.result.forEach(r => {
            const val = r.corp_cnt !== 'N/A' ? parseInt(r.corp_cnt) : (r.tot_worker !== 'N/A' && parseInt(r.tot_worker) > 0 ? 1 : 0);
            map[r.adm_cd] = val;
        });
    }
    return map;
}

async function getBulkHouse(adm_cd, type, token, env) {
    const url = `/stats/house.json?adm_cd=${adm_cd}&year=2022&low_search=1${type === '02' ? '&house_type=02' : ''}`;
    const data = await fetchSgisWithCache(url, token, env);
    const map = {};
    if (data && data.errCd === 0 && data.result) {
        data.result.forEach(r => {
            map[r.adm_cd] = safeInt(r.house_cnt);
        });
    }
    return map;
}

async function getBulkPop(adm_cd, token, env) {
    const url = `/stats/population.json?adm_cd=${adm_cd}&year=2023&low_search=1`;
    const data = await fetchSgisWithCache(url, token, env);
    const map = {};
    if (data && data.errCd === 0 && data.result) {
        data.result.forEach(r => {
            map[r.adm_cd] = safeInt(r.tot_ppltn);
        });
    }
    return map;
}

async function getCompanyCount(adm_cd, class_code, token, env) {
    const url = `/stats/company.json?adm_cd=${adm_cd}&year=2023&class_code=${class_code}&low_search=0`;
    const data = await fetchSgisWithCache(url, token, env);
    if (data && data.errCd === 0 && data.result && data.result.length > 0) {
        const res = data.result[0];
        const val = res.corp_cnt;
        if (val !== 'N/A') return parseInt(val);
        const worker = res.tot_worker;
        if (worker !== 'N/A' && parseInt(worker) > 0) return 1;
    }
    return 0;
}

async function getHouseStats(adm_cd, token, env) {
    const url_tot = `/stats/house.json?adm_cd=${adm_cd}&year=2022&low_search=0`;
    const url_apt = `/stats/house.json?adm_cd=${adm_cd}&year=2022&low_search=0&house_type=02`;
    const [data_tot, data_apt] = await Promise.all([
        fetchSgisWithCache(url_tot, token, env), 
        fetchSgisWithCache(url_apt, token, env)
    ]);
    
    let total = 0, apt = 0;
    if (data_tot?.errCd === 0 && data_tot.result?.[0]) total = safeInt(data_tot.result[0].house_cnt);
    if (data_apt?.errCd === 0 && data_apt.result?.[0]) apt = safeInt(data_apt.result[0].house_cnt);
    
    const ratio = total > 0 ? Number((apt / total * 100).toFixed(1)) : 0;
    return { total, apt, ratio };
}

async function getPopulation(adm_cd, token, env) {
    const url = `/stats/population.json?adm_cd=${adm_cd}&year=2023&low_search=0`;
    const data = await fetchSgisWithCache(url, token, env);
    if (data?.errCd === 0 && data.result?.[0]) return safeInt(data.result[0].tot_ppltn);
    return 0;
}

async function fetchSchoolInfoStudents(sgg_code, sgg_name) {
    return [];
}
