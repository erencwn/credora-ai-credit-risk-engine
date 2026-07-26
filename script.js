document.addEventListener('DOMContentLoaded', () => {
    // State ve global ayarlar
    let currency = 'TRY';
    let GUNCEL_KUR = 45.00; 

    const YEREL_MI = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    const API_BASE = YEREL_MI ? 'http://127.0.0.1:8000' : '';
    
    const BTN_THEME_USD = "mt-8 w-full relative group overflow-hidden rounded-xl p-px font-semibold text-white transition-all duration-300 shadow-[0_0_40px_-10px_rgba(16,185,129,0.5)] hover:shadow-[0_0_60px_-15px_rgba(16,185,129,0.7)] bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500";
    const BTN_THEME_TRY = "mt-8 w-full relative group overflow-hidden rounded-xl p-px font-semibold text-white transition-all duration-300 shadow-[0_0_40px_-10px_rgba(124,58,237,0.5)] hover:shadow-[0_0_60px_-15px_rgba(124,58,237,0.7)] bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500";

    // DOM element seçmeleri
    const form = document.getElementById('creditForm');
    const resultContainer = document.getElementById('resultContainer');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    const amountInput = document.getElementById('amountInput');
    const incomeInput = document.getElementById('incomeInput');
    const scoreInput = document.getElementById('scoreInput');
    const assetsInput = document.getElementById('assetsInput');
    const debtInput = document.getElementById('debtInput');
    const termSelect = document.getElementById('termSelect');
    
    // Deneyim inputu
    const experienceInput = document.getElementById('experienceInput');
    
    const formatInputs = document.querySelectorAll('.format-number');
    
    const toggleBtn = document.getElementById('currencyToggle');
    const toggleThumb = document.getElementById('toggleThumb');
    const labelTRY = document.getElementById('labelTRY');
    const labelUSD = document.getElementById('labelUSD');
    const scoreLabel = document.getElementById('scoreLabel');
    const currSymbols = document.querySelectorAll('.currSym');
    
    const livePreviewDiv = document.getElementById('livePreview');
    const liveRateEl = document.getElementById('liveRate');
    const liveInstEl = document.getElementById('liveInstallment');
    const triggers = document.querySelectorAll('.live-trigger');
    
    const xgboostBadgeBtn = document.getElementById('xgboostBadgeBtn');
    const mlopsPopover = document.getElementById('mlopsPopover');
    const mlopsToggle = document.getElementById('mlopsToggle');
    const xgboostDot = document.getElementById('xgboostDot');
    const xgboostText = document.getElementById('xgboostText');

    // Helper fonksiyonlar
    const temizle = (val) => val ? parseFloat(val.replace(/\./g, '')) : 0;
    const fmt = (n) => Math.round(n).toLocaleString('tr-TR');

    formatInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let val = e.target.value.replace(/\D/g, ''); 
            e.target.value = val !== "" ? parseInt(val, 10).toLocaleString('tr-TR') : "";
        });
    });

    // MLOPS ve tema eventleri
    if (xgboostBadgeBtn && mlopsPopover && mlopsToggle) {
        xgboostBadgeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const isOpen = mlopsPopover.classList.contains('opacity-100');
            mlopsPopover.classList.toggle('opacity-100', !isOpen);
            mlopsPopover.classList.toggle('pointer-events-auto', !isOpen);
            mlopsPopover.classList.toggle('translate-y-0', !isOpen);
            mlopsPopover.classList.toggle('opacity-0', isOpen);
            mlopsPopover.classList.toggle('pointer-events-none', isOpen);
            mlopsPopover.classList.toggle('translate-y-[10px]', isOpen);
        });

        document.addEventListener('click', (e) => {
            if (!xgboostBadgeBtn.contains(e.target) && !mlopsPopover.contains(e.target)) {
                mlopsPopover.classList.remove('opacity-100', 'pointer-events-auto', 'translate-y-0');
                mlopsPopover.classList.add('opacity-0', 'pointer-events-none', 'translate-y-[10px]');
            }
        });

        mlopsToggle.addEventListener('change', (e) => {
            if (e.target.checked) {
                xgboostText.textContent = 'MLOps Aktif';
                xgboostBadgeBtn.classList.replace('text-red-400', 'text-emerald-400');
                xgboostDot.className = 'w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] transition-all duration-300';
            } else {
                xgboostText.textContent = 'MLOps Pasif';
                xgboostBadgeBtn.classList.replace('text-emerald-400', 'text-red-400');
                xgboostDot.className = 'w-2 h-2 rounded-full bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.8)] transition-all duration-300';
            }
        });
    }

    const themeSlider = document.getElementById('themeSlider');
    if (themeSlider) {
        themeSlider.checked = true; 
        themeSlider.addEventListener('change', (e) => {
            const dot = document.querySelector('.dot');
            if(e.target.checked) {
                document.body.classList.remove('theme-light');
                if(dot) dot.style.transform = 'translateX(20px)';
            } else {
                document.body.classList.add('theme-light');
                if(dot) dot.style.transform = 'translateX(0px)';
            }
        });
    }

    // Kur çekme ve para birimi geçişleri
    async function fetchGuncelKur() {
        try {
            const response = await fetch('https://open.er-api.com/v6/latest/USD');
            const data = await response.json();
            if (data?.rates?.TRY) {
                GUNCEL_KUR = data.rates.TRY;
            }
        } catch (error) {
            console.warn("API Hatası. Yedek kur devrede: " + GUNCEL_KUR);
        }
    }

    function applyCurrency() {
        const isTry = currency === 'TRY';
        
        toggleThumb.style.transform = isTry ? 'translateX(0)' : 'translateX(100%)';
        
        if (isTry) {
            toggleThumb.classList.remove('from-emerald-500', 'to-teal-500');
            toggleThumb.classList.add('from-purple-500', 'to-blue-500');
            toggleBtn.classList.remove('border-emerald-500/30');
            toggleBtn.classList.add('border-purple-500/30');
            
            labelTRY.classList.remove('text-neutral-500');
            labelTRY.classList.add('text-white');
            labelUSD.classList.remove('text-white');
            labelUSD.classList.add('text-neutral-500');
            
            currSymbols.forEach(s => s.textContent = '₺');
            scoreLabel.textContent = 'Müşteri Findeks Notu (1–1900)';
            scoreInput.placeholder = '1.550';
            assetsInput.placeholder = '500.000';
            debtInput.placeholder = '0';
            incomeInput.placeholder = '20.000';
            amountInput.placeholder = '50.000';
            document.body.classList.remove('theme-usd');
            if(analyzeBtn) analyzeBtn.className = BTN_THEME_TRY;
        } else {
            toggleThumb.classList.remove('from-purple-500', 'to-blue-500');
            toggleThumb.classList.add('from-emerald-500', 'to-teal-500');
            toggleBtn.classList.remove('border-purple-500/30');
            toggleBtn.classList.add('border-emerald-500/30');
            
            labelTRY.classList.remove('text-white');
            labelTRY.classList.add('text-neutral-500');
            labelUSD.classList.remove('text-neutral-500');
            labelUSD.classList.add('text-white');
            
            currSymbols.forEach(s => s.textContent = '$');
            scoreLabel.textContent = 'FICO Kredi Skoru (300–850)';
            scoreInput.placeholder = '720';
            assetsInput.placeholder = '15.000';
            debtInput.placeholder = '0';
            incomeInput.placeholder = '1.500';
            amountInput.placeholder = '2.000';
            document.body.classList.add('theme-usd');
            if(analyzeBtn) analyzeBtn.className = BTN_THEME_USD;
        }

        resultContainer.innerHTML = '';
        updateLivePreview();
    }

    toggleBtn.addEventListener('click', () => {
        currency = currency === 'TRY' ? 'USD' : 'TRY';
        applyCurrency();
    });

    // Skor dönüşüm ve canlı ön izleme
    function findeksToFico(findeksNotu) {
        if (findeksNotu <= 699) return 300 + (findeksNotu / 699) * (579 - 300);
        if (findeksNotu <= 1099) return 580 + ((findeksNotu - 700) / 399) * (669 - 580);
        if (findeksNotu <= 1499) return 670 + ((findeksNotu - 1100) / 399) * (739 - 670);
        if (findeksNotu <= 1699) return 740 + ((findeksNotu - 1500) / 199) * (799 - 740);
        return 800 + ((findeksNotu - 1700) / 200) * (850 - 800);
    }

    async function updateLivePreview() {
        const amount = temizle(amountInput?.value);
        const income = temizle(incomeInput?.value);
        const score = temizle(scoreInput?.value);
        const months = parseInt(termSelect?.value, 10);
        
        const experience = parseInt(experienceInput?.value, 10) || 0;

        if(amount > 0 && score > 0 && months > 0) {
            livePreviewDiv.classList.remove('hidden');

            try {
                const response = await fetch(`${API_BASE}/api/live_tahmin`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        kredi_puan: score,
                        kredi_vade: months,
                        kredi_tutar: amount,
                        deneyim_yil: experience,
                        para_birimi: currency,
                        guncel_kur: GUNCEL_KUR
                    })
                });

                const data = await response.json();

                if(response.ok) {
                    const sym = currency === 'TRY' ? '₺' : '$';
                    liveRateEl.textContent = `%${(data.aylik_faiz_orani * 100).toFixed(2)}`;
                    liveInstEl.textContent = `${sym}${fmt(data.aylik_taksit)}`;
                } else {
                    console.error("Python Sunucu Hatası:", data.hata);
                }
            } catch (error) {
                console.error("API Bağlantı Hatası (app.py açık mı?):", error);
            }
        } else {
            livePreviewDiv.classList.add('hidden');
        }
    }

    triggers.forEach(input => ['input', 'change'].forEach(evt => input.addEventListener(evt, updateLivePreview)));

    // Form gönderim ve ana API haberleşmesi
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const sym = currency === 'TRY' ? '₺' : '$';
        
        const experience = parseInt(experienceInput.value, 10) || 0;
        
        const payload = {
            para_birimi: currency,
            guncel_kur: GUNCEL_KUR,
            mlops_izni: mlopsToggle ? mlopsToggle.checked : false,
            egitim_seviyesi: document.getElementById('educationSelect').value,
            calisma_durumu: document.getElementById('workStatusSelect').value,
            kredi_gecmisi: parseInt(document.getElementById('creditHistoryInput')?.value || 5, 10),
            deneyim_yil: experience,
            toplam_varlik: temizle(assetsInput.value),
            aylik_borc: temizle(debtInput.value),
            aylik_gelir: temizle(incomeInput.value),
            kredi_tutari: temizle(amountInput.value) || 50000,
            vade: parseInt(termSelect.value, 10) || 24,
            kredi_puani: temizle(scoreInput.value)
        };

        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = `
            <div class="relative px-8 py-4 bg-black/20 backdrop-blur-sm rounded-xl transition-all duration-300 text-lg flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                QUANTA Motoru Analiz Ediyor...
            </div>
        `;

        try {
            const response = await fetch(`${API_BASE}/api/hesapla`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `<div class="relative px-8 py-4 bg-black/20 backdrop-blur-sm rounded-xl transition-all duration-300 text-lg">Yapay Zeka ile Analiz Et</div>`;

            if (response.ok && data.sonuc === "ONAY") {
                resultContainer.innerHTML = `
                    <div class="glass result-approved rounded-3xl p-7 sm:p-9 fade-in mt-6">
                        <div class="flex items-center gap-2.5 mb-6">
                            <div class="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]"></div>
                            <span class="text-sm font-semibold tracking-wide text-emerald-400">Durum: ONAYLANDI</span>
                        </div>
                        <div class="grid grid-cols-2 gap-5 mb-6">
                            <div>
                                <div class="text-xs text-neutral-500 mb-1">Yıllık Faiz Oranı</div>
                                <div class="text-2xl font-semibold mono">%${data.faiz_orani.toFixed(2)}</div>
                            </div>
                            <div>
                                <div class="text-xs text-neutral-500 mb-1">Aylık Taksit (${payload.vade} Ay)</div>
                                <div class="text-2xl font-semibold mono">${sym}${fmt(data.aylik_taksit)}</div>
                            </div>
                        </div>
                        <div class="field rounded-xl p-4 flex gap-3 border border-emerald-500/20 bg-emerald-500/5">
                            <svg class="w-5 h-5 shrink-0 mt-0.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z"/></svg>
                            <p class="text-sm text-neutral-300 leading-relaxed">
                                <span class="text-emerald-400 font-semibold">AI Analizi:</span> ${data.ai_mesaji}
                            </p>
                        </div>
                    </div>
                `;
            } else if (response.ok && data.sonuc === "RED") {
                const redMaddeleri = data.red_sebepleri.map(sebep => `<li class="flex gap-2.5"><span class="text-red-400 font-bold">—</span> ${sebep}</li>`).join('');
                const tavsiyeMaddeleri = data.ai_tavsiyeleri.map(tavsiye => `<li class="flex gap-2.5 text-neutral-400"><span class="text-blue-400">💡</span> ${tavsiye}</li>`).join('');
                
                resultContainer.innerHTML = `
                    <div class="glass result-rejected rounded-3xl p-7 sm:p-9 fade-in mt-6">
                        <div class="flex items-center gap-2.5 mb-6">
                            <div class="w-2.5 h-2.5 rounded-full bg-red-400 shadow-[0_0_10px_rgba(248,113,113,0.8)]"></div>
                            <span class="text-sm font-semibold tracking-wide text-red-400">Durum: REDDEDİLDİ</span>
                        </div>
                        <div class="mb-6">
                            <div class="text-xs text-neutral-500 mb-3 uppercase tracking-wider font-semibold">Neden Reddedildi? (AI Analizi)</div>
                            <ul class="space-y-3 text-sm text-neutral-200 mb-7">${redMaddeleri}</ul>
                            <div class="text-xs text-neutral-500 mb-3 uppercase tracking-wider font-semibold">Sistem Tavsiyeleri</div>
                            <ul class="space-y-2 text-sm">${tavsiyeMaddeleri}</ul>
                        </div>
                    </div>
                `;
            } else {
                alert("Sunucu Hatası: " + (data.hata || "Bilinmeyen bir sorun oluştu."));
            }
            
            resultContainer.scrollIntoView({ behavior:'smooth', block:'nearest' });

        } catch (error) {
            console.error("API Hatası:", error);
            alert("Sunucuya bağlanılamadı! Lütfen daha sonra tekrar deneyin veya sistem yöneticisiyle iletişime geçin.");
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `<div class="relative px-8 py-4 bg-black/20 backdrop-blur-sm rounded-xl transition-all duration-300 text-lg">Yapay Zeka ile Analiz Et</div>`;
        }
    });

    // İlk yüklemede çalışanlar
    fetchGuncelKur();
    applyCurrency(); 
});