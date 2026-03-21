export class DataProcessor {
    static calculateGpaIntensity(achievementARatio, stdDev) {
        if (!achievementARatio || !stdDev) return 0;
        // Formula: 1 / (A % * SD)
        return (1 / ((achievementARatio / 100) * stdDev)).toFixed(4);
    }

    static getIntensityTag(intensity) {
        if (intensity >= 0.05) return { tag: '트상', class: 'tag-top', score: 20 };
        if (intensity >= 0.03) return { tag: '상', class: 'tag-high', score: 40 };
        if (intensity >= 0.015) return { tag: '중', class: 'tag-mid', score: 60 };
        if (intensity >= 0.007) return { tag: '하', class: 'tag-low', score: 80 };
        return { tag: '최하', class: 'tag-low', score: 100 };
    }

    static calculateTotalScore(metrics) {
        const weights = {
            schoolBalance: 0.1,    // 10%
            academyDensity: 0.2,   // 20%
            childcare: 0.05,       // 5%
            apartmentDensity: 0.2, // 20%
            safety: 0.05,          // 5%
            studentsPerHigh: 0.2,  // 20%
            strategicGpa: 0.2      // 20%
        };

        let total = 0;
        for (const key in weights) {
            total += (metrics[key] || 0) * weights[key];
        }
        return Math.min(Math.round(total), 100);
    }

    static getGrade(score) {
        if (score >= 90) return 'S+';
        if (score >= 80) return 'A';
        if (score >= 70) return 'B';
        if (score >= 60) return 'C';
        return 'D';
    }

    // Mock Data Generator for UI development
    static generateMockData(dongName) {
        const seed = dongName.length * 10;
        const metrics = {
            schoolBalance: 60 + (seed % 40),
            academyDensity: 40 + (seed % 60),
            childcare: 50 + (seed % 50),
            apartmentDensity: 30 + (seed % 70),
            safety: 70 + (seed % 30),
            studentsPerHigh: 50 + (seed % 50),
            strategicGpa: 40 + (seed % 60)
        };
        const total = this.calculateTotalScore(metrics);
        return {
            name: dongName,
            totalScore: total,
            grade: this.getGrade(total),
            metrics
        };
    }

    static generateMockSchools(count = 3) {
        const schoolNames = ["가람고등학교", "나래고등학교", "다온고등학교", "라온고등학교", "마루고등학교"];
        const schools = [];
        for (let i = 0; i < count; i++) {
            const a = (10 + Math.random() * 30).toFixed(1);
            const sd = (15 + Math.random() * 10).toFixed(1);
            const intensity = this.calculateGpaIntensity(parseFloat(a), parseFloat(sd));
            const intensityInfo = this.getIntensityTag(parseFloat(intensity));
            
            schools.push({
                name: schoolNames[i % schoolNames.length],
                students: Math.round(180 + Math.random() * 100),
                aRatio: a,
                stdDev: sd,
                intensity: intensity,
                intensityTag: intensityInfo.tag,
                intensityClass: intensityInfo.class,
                strategicScore: intensityInfo.score
            });
        }
        return schools;
    }
}
