# Credora — Yapay Zeka Destekli Kredi & Risk Karar Motoru

Credora, bir kredi başvurusunun **onaylanıp onaylanmayacağını** ve başvuru onaylanırsa **hangi faiz oranıyla** onaylanacağını tahmin eden, açıklanabilir (explainable) bir yapay zeka sistemidir. Canlı demo: **[credora.finance](https://credora.finance)**

---

## 🎯 Projenin Amacı

Elimizdeki veri seti (**LoanDB**, 18.833 kayıt), gerçekçi bir bankacılık senaryosunu yansıtacak şekilde **ciddi bir sınıf dengesizliği** barındırıyor:

- **%74.6 Red**
- **%25.4 Onay**

Amacımız, bu dengesiz veriyle çalışırken bile:
1. **Mümkün olduğunca isabetli** tahmin yapmak (dengesizliğin modeli "her zaman red de" diyen tembel bir modele dönüştürmesine izin vermeden),
2. Onaylanan başvurular için **gerçekçi bir yıllık faiz oranı** üretmek,
3. Reddedilen her başvuru için **SHAP tabanlı, somut ve anlaşılır bir gerekçe** sunmak — "sebepsiz red" yok.

---

## 🧠 Sistem Mimarisi — İki Model

### 1) Faiz Tahmin Modeli (`faiz_tahmin_model.pkl`)
- **Algoritma:** Lineer Regresyon
- **Girdi:** `Kredi_Puan`, `Kredi_Vade`, `Kredi_Tutar`, `Deneyim_Yil`
- **Çıktı:** Yıllık faiz oranı (%12 – %45 aralığına sınırlandırılmış)
- Kredi onay modeli, eğitim sırasında **gerçek faiz oranı yerine bu modelin ürettiği tahmini** kullanır — çünkü canlı sistemde gerçek faiz zaten bilinmiyor, önce tahmin ediliyor. Bu, eğitim/üretim (train/serve) tutarlılığını garanti eder.

### 2) Kredi Onay Modeli (`credora_lr_model.pkl`)
- **Algoritma:** Lojistik Regresyon (17 özellik, `StandardScaler` ile ölçeklenmiş)
- XGBoost ile karşılaştırıldı; Lojistik Regresyon hem ham performansta hem de tahmini faizle çalışırken (gerçek üretim senaryosu) daha yüksek ve daha dayanıklı sonuç verdiği için seçildi.
- **Karar eşiği (threshold): 0.41** — varsayılan %50 yerine bilinçli olarak düşürüldü. Sebep: veri setindeki %75'lik red baskınlığı, modelin doğal olarak "temkinli" davranmasına yol açıyor; eşiği düşürerek **hak eden başvuranları kaçırmama (Recall)** önceliklendirildi, Precision'dan ölçülü bir feragatle.

**Nihai test metrikleri (eşik=0.41):**

| Metrik | Değer |
|---|---|
| Accuracy | %90.81 |
| ROC-AUC | 0.9676 |
| Precision (Onay) | %80.08 |
| Recall (Onay) | %84.94 |
| F1-Score (Onay) | 0.8244 |

---

## ⚖️ Açıklanabilirlik (XAI) — SHAP

Her red kararı için sistem, **en etkili tek sebebi** (gerekirse ona yakın ikinci bir sebebi) SHAP değerlerinden türetip kullanıcıya sunar. Tasarım ilkeleri:

- Sadece **somut, finansal olarak anlamlı** etkenler sebep olarak gösterilir (Kredi Puanı, Borç/Gelir Oranı, Toplam Varlık, Kredi Geçmişi, Mesleki Deneyim vb.)
- **"3 tane doldurma sebep"** yerine, gerçekten anlamlı olan(lar) gösterilir
- Çalışma Durumu / Eğitim Seviyesi gibi demografik değişkenler **hiçbir zaman** tek başına bir "red sebebi" olarak sunulmaz

## 🛡️ Etik Tasarım Kararı — Yaş Kullanılmıyor

Hem faiz modeli hem kredi onay modeli, **`Yaş` değişkenini hiç kullanmaz.** Analiz ettik: yaşın taşıdığı bilgi, `Deneyim_Yıl` değişkeniyle istatistiksel olarak neredeyse birebir örtüşüyordu (multicollinearity). Yaşı çıkardığımızda:
- Faiz modelinde MAE/R² **birebir aynı** kaldı
- Kredi onay modelinde performans **ölçülemeyecek kadar az** değişti (hatta bazı metriklerde marjinal iyileşme oldu)

Yani yaşı tutmanın hiçbir istatistiksel/iş gerekçesi yoktu — sadece ayrımcılık riski taşıyordu. Bu yüzden kaldırıldı.

---

## 🔄 MLOps — Sürekli Öğrenme Altyapısı

Kullanıcı arayüzdeki "MLOps Aktif" onayını verirse (varsayılan açık), başvuru sırasında modele giden özellikler + tahmin sonucu, ileride modeli yeniden eğitmek ve performans driftini izlemek için **SQLite** veritabanına (anonim olarak, kişisel veri toplanmadan) kaydedilir.

---

## 🗂️ Proje Yapısı

```
Credora/
├── app.py                     # Flask backend (API + model inference)
├── database.py                # SQLite MLOps veri kayıt katmanı
├── index.html                 # Frontend
├── script.js                  # Frontend mantığı (form, canlı önizleme, API çağrıları)
├── style.css                  # Tema (koyu/açık mod, TL/USD tema)
├── web.config                 # IIS reverse proxy yapılandırması (Windows Server dağıtımı)
├── requirements.txt           # Python bağımlılıkları
├── model/
│   ├── credora_lr_model.pkl       # Kredi onay modeli
│   ├── credora_lr_scaler.pkl      # StandardScaler
│   ├── credora_lr_threshold.pkl   # Karar eşiği (0.41)
│   ├── model_columns.pkl          # Özellik sırası
│   └── faiz_tahmin_model.pkl      # Faiz tahmin modeli
├── Credora_Data.xlsx          # Eğitim verisi (LoanDB, 18.833 kayıt)
├── logo/                      # Marka görselleri
└── ekip/                      # Ekip fotoğrafları
```

---

## 🚀 Kurulum

```bash
git clone https://github.com/erencwn/credora-ai-credit-risk-engine.git
cd credora-ai-credit-risk-engine
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python app.py
```

Sunucu `http://127.0.0.1:8000` üzerinde ayağa kalkar. `index.html`'i bir tarayıcıda (veya VS Code Live Server ile) açman yeterli.

---

## 🧰 Kullanılan Teknolojiler

**Backend:** Flask, Waitress (üretim WSGI sunucusu), scikit-learn, SHAP, pandas, SQLite
**Frontend:** Vanilla JavaScript, Tailwind CSS, Particles.js
**Dağıtım:** Windows Server + IIS (reverse proxy) + Let's Encrypt (SSL)

---

## 👥 Ekip

QUANTA ekibi tarafından geliştirilmiştir.
