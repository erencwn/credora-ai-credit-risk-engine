# Credora — Yapay Zeka Destekli Kredi & Risk Karar Motoru

Credora, kredi başvuru süreçlerini otomatize eden, başvuruların **onay/red durumunu** ve onaylanan başvurular için **optimum yıllık faiz oranını** tahmin eden, uçtan uca (end-to-end) tasarlanmış bir makine öğrenmesi uygulamasıdır. Modelin sadece bir çalışma ortamında (notebook) kalmayıp gerçek dünya kullanımına uygun, API destekli bir yapıya dönüştürüldüğü bu sistem, "Açıklanabilir Yapay Zeka" (XAI) prensiplerini merkeze almaktadır.

Canlı demo: **[credora.finance](https://credora.finance)**

---

## Projenin Amacı ve Analitik Yaklaşım

18.833 kayıttan oluşan **LoanDB** veri seti kullanılarak geliştirilen bu proje, bankacılık sektöründeki temel gerçek dünya problemlerinden birine odaklanmaktadır: **Ciddi sınıf dengesizliği** (Sınıfların dağılımı: %74.6 Red, %25.4 Onay). 

Bu veri seti üzerindeki temel hedeflerimiz şunlardır:
*   **İsabetli Karar Alma:** Dengesiz veri setinin modeli "sürekli red" yönünde eğilimlendirmesini (tembel model problemini) engelleyerek adil ve hassas tahminler üretmek.
*   **Dinamik Faiz Fiyatlandırması:** Kredi onayı alan başvurular için başvuranın risk profiline uygun, gerçekçi bir yıllık faiz oranı hesaplamak.
*   **Şeffaflık (Açıklanabilirlik):** Reddedilen her başvuru için SHAP (SHapley Additive exPlanations) tabanlı, somut ve finansal olarak anlamlı gerekçeler sunarak "sebepsiz red" kavramını ortadan kaldırmak.

---

## Sistem Mimarisi: Çift Modelli Yapı

Gerçek dünya bankacılık operasyonlarına tam uyum sağlamak amacıyla sistem iki entegre model üzerinden çalışmaktadır:

### 1. Dinamik Faiz Tahmin Modeli (`faiz_tahmin_model.pkl`)
*   **Algoritma:** Lineer Regresyon
*   **Girdiler:** `Kredi_Puan`, `Kredi_Vade`, `Kredi_Tutar`, `Deneyim_Yil`
*   **Çıktı:** Yıllık faiz oranı (Yasal ve operasyonel standartlar gereği %12 – %45 aralığına sınırlandırılmıştır).
*   **Entegrasyon Mantığı:** Canlı sistemlerde başvuru anında gerçek faiz oranı henüz belli olmadığı için, kredi onay modelinin eğitimi sırasında gerçek faiz oranı yerine **bu modelin ürettiği tahmini faiz oranları** kullanılmıştır. Bu strateji, eğitim ve üretim (train/serve) ortamları arasındaki tutarlılığı güvence altına alır.

### 2. Kredi Onay Modeli (`credora_lr_model.pkl`)
*   **Algoritma:** Lojistik Regresyon (17 bağımsız değişken, `StandardScaler` ile ölçeklendirilmiş).
*   **Model Seçimi:** Geliştirme sürecinde XGBoost ile karşılaştırmalı analizler yapılmıştır. Lojistik Regresyon, özellikle üretim ortamında (tahmini faiz değerleriyle çalışırken) sergilediği yüksek kararlılık ve sağlamlık nedeniyle tercih edilmiştir.
*   **Karar Eşiği (Threshold) Optimizasyonu:** Varsayılan 0.50 karar eşiği bilinçli olarak **0.41'e** düşürülmüştür. Veri setindeki %75'lik red baskınlığı modeli doğal olarak aşırı temkinli olmaya ittiğinden, eşiğin düşürülmesiyle hak eden başvuru sahiplerinin sistemden elenmemesi (Recall artışı) hedeflenmiş ve Precision metriklerinden ölçülü bir feragatle optimal analitik denge kurulmuştur.

**Nihai Test Performans Metrikleri (Eşik = 0.41):**

| Metrik | Değer |
| :--- | :--- |
| **Accuracy** | %90.81 |
| **ROC-AUC** | 0.9676 |
| **Precision (Onay)** | %80.08 |
| **Recall (Onay)** | %84.94 |
| **F1-Score (Onay)** | 0.8244 |

---

## Açıklanabilirlik (XAI) ve Şeffaflık

Yapay zekanın "kara kutu" olmaktan çıkarılması, sistem tasarımımızın temel prensiplerinden biridir. Karar motoru, her red kararı için son kullanıcıya **en yüksek etkiye sahip olan somut sebebi** (gerekirse ikinci bir sebep ile birlikte) sunar:

*   Karar gerekçeleri yalnızca finansal açıdan anlamlı faktörlere (Kredi Puanı, Borç/Gelir Oranı, Toplam Varlık, Kredi Geçmişi vb.) dayandırılır.
*   "Doldurma" veya kullanıcı için anlamsız sebepler yerine, SHAP değerlerinden türetilmiş gerçek içgörüler gösterilir.
*   Çalışma Durumu veya Eğitim Seviyesi gibi demografik değişkenler tek başlarına bir "red sebebi" olarak müşteriye sunulmaz.

## Veri Etiği ve Model Tasarımı: Yaş Değişkeninin Reddi

Model geliştirme sürecinde yüksek etik standartlar gözetilmiş ve **`Yaş` değişkeni her iki modelden de tamamen çıkarılmıştır.** Yapılan çoklu bağlantı (multicollinearity) analizlerinde, yaş değişkeninin taşıdığı istatistiksel bilginin, `Deneyim_Yıl` (Mesleki Deneyim) değişkeniyle neredeyse birebir örtüştüğü tespit edilmiştir. Yaşın veri setinden çıkarılması:
*   Faiz tahmin modelinin MAE/R² metriklerini **hiç değiştirmemiştir.**
*   Kredi onay modelinin performansında ölçülemeyecek kadar az değişime (bazı metriklerde marjinal iyileşmelere) yol açmıştır.

Yaş değişkenini modelde tutmanın hiçbir istatistiksel veya iş gerekçesi bulunmadığından, ayrımcılık riskini (bias) ortadan kaldırmak adına bu özellik tasarımdan dışlanmıştır.

---

## MLOps ve Sürekli Öğrenme Altyapısı

Modelin canlıya alınmasıyla süreç sonlanmamaktadır. Kullanıcı arayüzünde bulunan "MLOps Aktif" onayı (varsayılan olarak açık) sayesinde, başvuru sırasında modele giden veriler ve tahmin sonuçları ileride gerçekleştirilecek model iyileştirmeleri için **SQLite** veritabanına kaydedilir. Toplanan veriler tamamen anonimleştirilmiş olup kişisel veri içermez; temel amaç zaman içinde oluşabilecek performans sapmalarını (model drift) izlemek ve sürekli öğrenme döngüsünü beslemektir.

---

## 🗂️ Proje Yapısı

```text
Credora/
├── app.py                     # Flask backend (API ve model inference süreçleri)
├── database.py                # SQLite MLOps veri kayıt katmanı
├── index.html                 # Frontend ana sayfası
├── script.js                  # Frontend mantığı (form, canlı önizleme, API entegrasyonu)
├── style.css                  # UI Tema dosyası (Koyu/Açık mod, TL/USD formatlamaları)
├── web.config                 # IIS reverse proxy yapılandırması (Windows Server dağıtımı)
├── requirements.txt           # Python kütüphane bağımlılıkları
├── model/
│   ├── credora_lr_model.pkl       # Kredi onay modeli
│   ├── credora_lr_scaler.pkl      # Veri standardizasyonu (StandardScaler)
│   ├── credora_lr_threshold.pkl   # Optimize edilmiş karar eşiği (0.41)
│   ├── model_columns.pkl          # Özellik (Feature) sırası
│   └── faiz_tahmin_model.pkl      # Faiz tahmin modeli
├── Credora_Data.xlsx          # Eğitim veri seti (LoanDB, 18.833 kayıt)
├── logo/                      # Marka ve UI görselleri
└── ekip/                      # Proje ekibi görselleri
```

---

## Kurulum ve Çalıştırma

Projeyi yerel ortamınızda test etmek için aşağıdaki adımları izleyebilirsiniz:

```bash
# Repoyu klonlayın
git clone https://github.com/erencwn/credora-ai-credit-risk-engine.git
cd credora-ai-credit-risk-engine

# Sanal ortam (virtual environment) oluşturun ve aktif edin
python -m venv venv
venv\Scripts ctivate      # Windows için
# source venv/bin/activate # Linux/Mac için

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Backend sunucusunu başlatın
python app.py
```
Backend sunucusu `http://127.0.0.1:8000` adresinde çalışmaya başlayacaktır. Arayüzü görüntülemek için `index.html` dosyasını tarayıcınızda (veya VS Code Live Server eklentisiyle) açmanız yeterlidir.

---

## Kullanılan Teknolojiler

*   **Makine Öğrenmesi & Veri Bilimi:** scikit-learn, SHAP, pandas
*   **Backend & API:** Flask, Waitress (Production WSGI server), SQLite
*   **Frontend:** Vanilla JavaScript, Tailwind CSS, Particles.js
*   **Altyapı & Dağıtım:** Windows Server, IIS (Reverse Proxy), Let's Encrypt (SSL)

---

## 👥 Ekip

*   Eren Can Türkoğlu
*   Ali Müfit Dede
*   Ömür Tutal Pekyiğit
