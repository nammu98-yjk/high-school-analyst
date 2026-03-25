import { ApiService } from './api.js';

class App {
    constructor() {
        this.api = new ApiService();
        this.map = null;
        this.radarChart = null;
        this.markers = [];
        this.allSchoolsData = []; // 고등학교현황 전체 데이터 보관
        this.init();
    }

    async init() {
        this.initElements();
        this.setLoading(true, '데이터 분석 엔진 가동 중...');
        this.initEvents();
        this.initMap();
        this.initChart();
        
        const tokenOk = await this.api.init();
        if (!tokenOk) {
            this.els.selectedAreaLabel.textContent = '⚠️ SGIS 토큰 발급 실패. 서버 로그 확인';
        }

        await this.loadCities();
        this.setLoading(false);
        console.log('App ready.');
    }

    setLoading(show, msg = '데이터 로딩 중...') {
        const overlay = document.getElementById('loadingOverlay');
        const text = document.getElementById('loadingMsg');
        if (overlay) {
            if (show) {
                if (text) text.textContent = msg;
                overlay.classList.remove('hidden');
            } else {
                overlay.classList.add('hidden');
            }
        }
    }

    initElements() {
        this.els = {
            citySelect: document.getElementById('citySelect'),
            districtSelect: document.getElementById('districtSelect'),
            analyzeBtn: document.getElementById('analyzeBtn'),
            selectedAreaLabel: document.getElementById('selectedAreaLabel'),
            bestDongLabel: document.getElementById('bestDongLabel'),
            totalScore: document.getElementById('totalScore'),
            districtGrade: document.getElementById('districtGrade'),
            schoolTableBody: document.getElementById('schoolTableBody'),
            highSchoolTableBody: document.getElementById('highSchoolTableBody'),
            tabRanking: document.getElementById('tabRanking'),
            tabSchools: document.getElementById('tabSchools'),
            tabContentRanking: document.getElementById('tabContentRanking'),
            tabContentSchools: document.getElementById('tabContentSchools'),
        };
    }

    initEvents() {
        this.els.citySelect.addEventListener('change', (e) => this.handleCityChange(e.target.value));
        this.els.analyzeBtn.addEventListener('click', () => this.analyze());

        // 탭 전환
        this.els.tabRanking.addEventListener('click', () => {
            this.els.tabRanking.classList.add('active');
            this.els.tabSchools.classList.remove('active');
            this.els.tabContentRanking.classList.add('active');
            this.els.tabContentSchools.classList.remove('active');
        });
        this.els.tabSchools.addEventListener('click', () => {
            this.els.tabSchools.classList.add('active');
            this.els.tabRanking.classList.remove('active');
            this.els.tabContentSchools.classList.add('active');
            this.els.tabContentRanking.classList.remove('active');
        });

        // 고등학교현황 정렬 버튼
        document.querySelectorAll('#highSchoolTable .sort-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const col = btn.dataset.col;
                const dir = btn.dataset.dir;
                // 활성 버튼 표시
                document.querySelectorAll('#highSchoolTable .sort-btn').forEach(b => b.classList.remove('active-sort'));
                btn.classList.add('active-sort');
                this.renderHighSchools(col, dir);
            });
        });
    }

    initMap() {
        this.map = L.map('map').setView([37.5665, 126.9780], 11);
        
        // 배경 지도 (어둡고 차분한 느낌)
        this.baseLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20,
            opacity: 0.5 // 지형을 연하게 처리하여 인포그래픽 요소 강조
        }).addTo(this.map);
        
        this.geoJsonLayer = null;
    }

    initChart() {
        const ctx = document.getElementById('radarChart').getContext('2d');
        this.radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['학교밸런스', '학원밀집', '아파트비중', '고교당학생수', '내신확보 유리도'],
                datasets: [{
                    label: '지역 지표',
                    data: [0,0,0,0,0],
                    backgroundColor: 'rgba(88, 166, 255, 0.2)',
                    borderColor: 'rgba(88, 166, 255, 1)',
                    pointBackgroundColor: 'rgba(88, 166, 255, 1)',
                }]
            },
            options: {
                scales: {
                    r: {
                        angleLines: { color: '#30363d' },
                        grid: { color: '#30363d' },
                        pointLabels: { color: '#c9d1d9', font: { size: 10 } },
                        ticks: { display: false },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    async loadCities() {
        const cities = await this.api.getStages();
        
        // 사용자 정의 순서: 서울, 경기, 인천 순
        const sortOrder = { "서울특별시": 1, "경기도": 2, "인천광역시": 3 };
        cities.sort((a, b) => (sortOrder[a.addr_name] || 99) - (sortOrder[b.addr_name] || 99));

        this.els.citySelect.innerHTML = '<option value="">시/도 선택</option>';
        cities.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.cd;
            opt.textContent = c.addr_name;
            this.els.citySelect.appendChild(opt);
        });
    }

    async handleCityChange(cd) {
        if (!cd) return;
        this.els.districtSelect.innerHTML = '<option value="">로딩 중...</option>';
        this.els.districtSelect.disabled = false;

        const districts = await this.api.getStages(cd);
        this.els.districtSelect.innerHTML = '<option value="">시/군/구 선택</option>';
        districts.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.cd;
            opt.textContent = d.addr_name;
            this.els.districtSelect.appendChild(opt);
        });
    }

    async analyze() {
        const distCd = this.els.districtSelect.value;
        const distName = this.els.districtSelect.options[this.els.districtSelect.selectedIndex]?.text || '';
        const cityName = this.els.citySelect.options[this.els.citySelect.selectedIndex]?.text || '';

        if (!distCd || distName === '시/군/구 선택') {
            alert('시/군/구를 선택해주세요.');
            return;
        }

        const fullPath = `${cityName} ${distName}`;
        this.els.selectedAreaLabel.textContent = `${fullPath} 분석 중...`;
        this.els.analyzeBtn.textContent = '⏳ 분석 중...';
        this.els.analyzeBtn.disabled = true;
        this.els.bestDongLabel.textContent = '';
        this.setLoading(true, `${fullPath} 지역 데이터 분석 중...`);

        try {
            const data = await this.api.analyze(distCd, distName, 'district');
            
            // 고등학교현황 데이터 문서화 (지역명 포함)
            this.allSchoolsData = [];
            
            let scoreMap = {};
            if (Array.isArray(data) && data.length > 0) {
                data.forEach(d => {
                    scoreMap[d.adm_cd] = d;
                    // schoolsRaw가 있으면 학교별로 펼쳐서 저장
                    if (d.schoolsRaw && d.schoolsRaw.length > 0) {
                        d.schoolsRaw.forEach(school => {
                            // 중복 학교 제거 (같은 이름의 학교는 한 번만)
                            if (!this.allSchoolsData.find(s => s.schoolName === school.name && s.districtName === d.districtName)) {
                                this.allSchoolsData.push({
                                    districtName: d.districtName || d.name,
                                    schoolName: school.name,
                                    avg: school.avg || 0,
                                    g1: school.g1 || 0,
                                    g2: school.g2 || 0,
                                    g3: school.g3 || 0,
                                });
                            }
                        });
                    }
                });
                
                // 고등학교현황 탭 초기 렌더링 (평균 학생수 내림차순)
                this.renderHighSchools('avg', 'desc');

                const bestDong = [...data].sort((a,b) => b.totalScore - a.totalScore)[0];
                this.els.bestDongLabel.textContent = `최고점 : ${distName} ${bestDong.name} (${bestDong.totalScore}점)`;
                
                this.els.selectedAreaLabel.textContent = fullPath;
                this.updateChartAndScore(bestDong); 
                this.renderRanking(data);
            } else if (data && !Array.isArray(data)) {
                scoreMap[data.adm_cd] = data;
                this.els.selectedAreaLabel.textContent = fullPath;
                this.updateChartAndScore(data);
                this.renderRanking([data]);
            }
            
            await this.drawInfographicMap(distCd, scoreMap);

        } catch (e) {
            console.error('Analyze Error:', e);
            this.els.selectedAreaLabel.textContent = '❌ 데이터 로딩 중 오류가 발생했습니다.';
        } finally {
            this.setLoading(false);
            this.els.analyzeBtn.textContent = '분석 실행';
            this.els.analyzeBtn.disabled = false;
        }
    }

    async drawInfographicMap(adm_cd, scoreMap) {
        try {
            if (this.geoJsonLayer) {
                this.map.removeLayer(this.geoJsonLayer);
            }
            
            const boundaryData = await this.api.getBoundary(adm_cd);
            
            if (!boundaryData || !boundaryData.features) {
                return;
            }

            // SGIS API의 EPSG:5179(UTM-K) 좌표계를 Leaflet의 EPSG:4326(WGS84)로 변환
            proj4.defs("EPSG:5179", "+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
            const convertCoordinates = (coords) => {
                if (typeof coords[0] === 'number') {
                    return proj4("EPSG:5179", "EPSG:4326", [coords[0], coords[1]]); // [lon, lat]
                }
                return coords.map(convertCoordinates); // 재귀 처리 (MultiPolygon 지원)
            };

            boundaryData.features.forEach(feature => {
                if (feature.geometry && feature.geometry.coordinates) {
                    feature.geometry.coordinates = convertCoordinates(feature.geometry.coordinates);
                }
            });

            const getStyle = (feature) => {
                const cd = feature.properties.adm_cd;
                const result = scoreMap[cd];
                let color = '#21262d'; 
                let fillOpacity = 0.4;
                
                if (result) {
                    if (result.grade === 'S') color = '#d73a49';  // Red
                    else if (result.grade === 'A') color = '#e36209'; // Orange
                    else if (result.grade === 'B') color = '#dbab09'; // Yellow
                    else if (result.grade === 'C') color = '#2ea043'; // Green
                    else if (result.grade === 'D') color = '#58a6ff'; // Blue
                    else color = '#8b949e'; // Gray
                    fillOpacity = 0.85; // 뚜렷하게 채우기
                }

                return {
                    fillColor: color,
                    weight: 2,
                    opacity: 1,
                    color: '#c9d1d9', // 경계선 
                    dashArray: '3',
                    fillOpacity: fillOpacity
                };
            };

            this.geoJsonLayer = L.geoJSON(boundaryData, {
                style: getStyle,
                onEachFeature: (feature, layer) => {
                    const cd = feature.properties.adm_cd;
                    const nm = feature.properties.adm_nm;
                    const result = scoreMap[cd];
                    
                    let tooltipContent = `<div style="text-align:center; font-family:'Pretendard';"><strong>${nm}</strong>`;
                    if (result) {
                        tooltipContent += `<br><span style="font-size:0.95rem; font-weight:700; color:${layer.options.fillColor};">${result.totalScore}점 (${result.grade})</span></div>`;
                    } else {
                        tooltipContent += `</div>`;
                    }
                    
                    // 폴리곤 위에 텍스트 박스로 항상 표시
                    layer.bindTooltip(tooltipContent, { 
                        permanent: true, 
                        direction: "center",
                        className: "map-infographic-label"
                    });

                    // 클릭 시 해당 구역(동) 정보를 우측 차트에 렌더링
                    layer.on('click', () => {
                        if (result) {
                            this.updateChartAndScore(result);
                        }
                    });
                }
            }).addTo(this.map);

            this.map.fitBounds(this.geoJsonLayer.getBounds());
            
        } catch(e) {
            console.error('Map draw error:', e);
        }
    }

    updateChartAndScore(result) {
        this.els.totalScore.textContent = result.totalScore;
        this.els.districtGrade.textContent = result.grade;

        const s = result.scores;
        this.radarChart.data.datasets[0].data = [
            s.schoolBalance, s.academyDensity,
            s.apartmentDensity, s.studentsPerHigh, s.gpaIntensity
        ];
        this.radarChart.update();
    }

    renderRanking(results) {
        if (!this.els.schoolTableBody) return;
        this.els.schoolTableBody.innerHTML = '';
        
        // 점수 내림차순 정렬
        results.sort((a, b) => b.totalScore - a.totalScore);
        
        let currentRank = 1;
        let lastScore = -1;

        results.forEach((r, i) => {
            // 공동 순위 계산 (점수가 같으면 같은 등수 부여)
            if (r.totalScore !== lastScore) {
                currentRank = i + 1;
            }
            lastScore = r.totalScore;

            const gradeClass = (r.grade || 'e').toLowerCase();
            const s = r.scores;
            const raw = r.raw;
            const schools = `초${raw.elementary} 중${raw.middle} 고${raw.high}`;

            // 기본 행
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${currentRank}. ${r.name}</td>
                <td><span class="tag ${gradeClass}">${r.grade}</span></td>
                <td><strong>${r.totalScore}점</strong></td>
                <td>${s.studentsPerHigh}점</td>
                <td>${s.academyDensity}점</td>
                <td>${s.apartmentDensity}점</td>
                <td>${s.gpaIntensity}점</td>
                <td>${s.schoolBalance}점</td>
            `;
            tr.style.cursor = 'pointer';

            // 상세 확장 행
            const detailTr = document.createElement('tr');
            detailTr.className = 'detail-row';
            const chartId = `miniChart_${r.adm_cd}`;
            detailTr.innerHTML = `
                <td colspan="8">
                    <div class="detail-content">
                        <table class="mini-data-table">
                            <tr><th>고교당 학생수</th><td>평균 ${r.avgStudents || 0}명</td></tr>
                            <tr><th>학원수 / 학생밀도</th><td>
                                ${raw.academy}개 학원 / 중고생 ${raw.dongStudents > 0 ? raw.dongStudents.toLocaleString() : '-'}명
                                <span style="color:#8b949e;font-size:0.8em">(${raw.dongStudentsSource || '데이터 추정'})</span>
                                ${raw.dongStudents > 0 ? `<br>→ 학생 100명당 ${(raw.academy / (raw.dongStudents / 100)).toFixed(2)}개` : ''}
                            </td></tr>
                            <tr><th>아파트 비중</th><td>총 ${raw.house.toLocaleString()}호 중 아파트 ${raw.apartmentRatio}%</td></tr>
                            <tr><th>내신(중학) 특목진락율</th><td>${raw.eliteRate}%</td></tr>
                            <tr><th>내신(고교) 성취도분포</th><td>표준편차 ${raw.highStdDev} / A등급 ${raw.highARate}%</td></tr>
                            <tr><th>학교수 (초/중/고)</th><td>${schools}</td></tr>
                        </table>
                        <div class="mini-chart-box">
                            <canvas id="${chartId}"></canvas>
                        </div>
                    </div>
                </td>
            `;

            // 클릭 이벤트: 아코디언 토글
            tr.addEventListener('click', () => {
                const isActive = detailTr.classList.contains('active');
                
                // 다른 모든 행 닫기
                document.querySelectorAll('.detail-row').forEach(row => row.classList.remove('active'));
                
                if (!isActive) {
                    detailTr.classList.add('active');
                    this.renderMiniChart(chartId, s);
                }
                
                // 클릭 시 메인 차트/점수도 업데이트
                this.updateChartAndScore(r);
            });

            this.els.schoolTableBody.appendChild(tr);
            this.els.schoolTableBody.appendChild(detailTr);
        });
    }

    renderMiniChart(id, scores) {
        const ctx = document.getElementById(id).getContext('2d');
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['학교', '학원', '비중', '학생', '내신'], // 라벨 축소/수정
                datasets: [{
                    data: [scores.schoolBalance, scores.academyDensity, scores.apartmentDensity, scores.studentsPerHigh, scores.gpaIntensity],
                    backgroundColor: 'rgba(88, 166, 255, 0.2)',
                    borderColor: 'rgba(56, 139, 253, 1)',
                    borderWidth: 2,
                    pointRadius: 2,
                    pointBackgroundColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        grid: { color: 'rgba(48, 54, 61, 0.5)' },
                        ticks: { display: false, stepSize: 25 },
                        suggestedMin: 0,
                        suggestedMax: 100,
                        pointLabels: { 
                            font: { size: 10, weight: 'bold' },
                            color: '#8b949e'
                        }
                    }
                },
                plugins: { 
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
    }

    renderHighSchools(sortCol = 'avg', sortDir = 'desc') {
        const tbody = this.els.highSchoolTableBody;
        if (!tbody) return;

        const sorted = [...this.allSchoolsData].sort((a, b) => {
            return sortDir === 'desc' ? b[sortCol] - a[sortCol] : a[sortCol] - b[sortCol];
        });

        tbody.innerHTML = '';
        if (sorted.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#8b949e; padding:32px;">
                분석 결과가 없습니다. 좌측에서 지역을 선택 후 <strong>분석 실행</strong>을 눌러주세요.
            </td></tr>`;
            return;
        }

        sorted.forEach((s) => {
            const tr = document.createElement('tr');
            const mapUrl = `https://map.naver.com/p/search/${encodeURIComponent(s.schoolName)}`;
            
            tr.innerHTML = `
                <td>${s.districtName}</td>
                <td>
                    <a href="${mapUrl}" target="_blank" class="school-link" title="네이버 지도에서 보기">
                        <strong>${s.schoolName}</strong> <span class="map-icon">📍</span>
                    </a>
                </td>
                <td class="num-cell">${s.avg.toLocaleString()}명</td>
                <td class="num-cell">${s.g1.toLocaleString()}명</td>
                <td class="num-cell">${s.g2.toLocaleString()}명</td>
                <td class="num-cell">${s.g3.toLocaleString()}명</td>
            `;
            tbody.appendChild(tr);
        });
    }
}

new App();
