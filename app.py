from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import pandas as pd
import numpy as np
import joblib
import shap
import pickle
import warnings

import database
from flask import send_from_directory

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
warnings.filterwarnings("ignore")

# App tanımı (route'lardan önce olmalı)
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": [
    "https://credora.finance",
    "https://www.credora.finance"
]}})

# Rotalar
@app.route('/')
def ana_sayfa():
    return send_from_directory('.', 'index.html')

database.init_db()

# Modelleri ve scaler'ı yükle
print("Yapay Zeka Modelleri Yükleniyor...")
try:
    model = joblib.load('model/credora_lr_model.pkl')
    model_columns = joblib.load('model/model_columns.pkl')
    scaler = joblib.load('model/credora_lr_scaler.pkl')

    with open('model/faiz_tahmin_model.pkl', 'rb') as f:
        faiz_model = pickle.load(f)

    # Threshold
    try:
        with open('model/credora_lr_threshold.pkl', 'rb') as f:
            threshold = pickle.load(f)
    except Exception as e:
        print("Threshold dosyası bulunamadı, varsayılan 0.50 kullanılacak.")
        threshold = 0.42

    # SHAP explainer (LR için)
    dummy_bg = np.zeros((1, len(model_columns)))
    explainer = shap.LinearExplainer(model, dummy_bg)

    print("Sistem Hazır!")
except Exception as e:
    print(f"Model yükleme hatası: {e}")

# Utils
def findeks_to_fico(findeks_notu):
    if findeks_notu <= 699: return 300 + (findeks_notu / 699) * (579 - 300)
    elif findeks_notu <= 1099: return 580 + ((findeks_notu - 700) / 399) * (669 - 580)
    elif findeks_notu <= 1499: return 670 + ((findeks_notu - 1100) / 399) * (739 - 670)
    elif findeks_notu <= 1699: return 740 + ((findeks_notu - 1500) / 199) * (799 - 740)
    else: return 800 + ((findeks_notu - 1700) / 200) * (850 - 800)

# SHAP yorum sözlüğü
SHAP_YORUMLARI = {
    "Aylik_Gelir": {
        "pozitif": "Gelir seviyeniz, talep edilen kredi hacmini destekleyecek güçte bulunmuştur.",
        "red": "Aylık net gelir beyanınız, talep edilen kredi anaparası ve vadesi göz önüne alındığında ödeme gücü kriterlerinin altında kalmıştır.",
        "tavsiye": "Resmi olarak belgeleyebileceğiniz ek gelirleriniz (kira, yan haklar vb.) varsa bunları beyan ederek başvurunuzu güncelleyebilirsiniz."
    },
    "Aylik_Borc_Odeme": {
        "pozitif": "Mevcut borçluluk durumunuz risk sınırlarının oldukça altındadır.",
        "red": "Halihazırda devam eden finansal yükümlülükleriniz (kredi/kredi kartı), yeni bir kredi limiti tahsisi için yüksek risk oluşturmaktadır.",
        "tavsiye": "Mevcut borçlarınızın bir kısmını erken kapatarak veya borç transferi ile yapılandırarak finansal alan açabilirsiniz."
    },
    "Toplam_Varlik": {
        "pozitif": "Sahip olduğunuz toplam varlık/teminat havuzu risk skorunuzu pozitif etkilemiştir.",
        "red": "Beyan edilen toplam varlıklarınız, bu hacimdeki bir kredi riskini dengelemek/teminatlandırmak için yeterli derinlikte görülmemiştir.",
        "tavsiye": "Daha düşük bir kredi tutarı talep edebilir veya şubenizle ek teminat seçeneklerini görüşebilirsiniz."
    },
    "Kredi_Tutar": {
        "pozitif": "Talep edilen kredi tutarı makul risk sınırları içerisindedir.",
        "red": "Talep edilen kredi anaparası, mevcut algoritmik risk profilinize ve finansal kapasitenize kıyasla oldukça yüksek bulunmuştur.",
        "tavsiye": "İhtiyacınızı optimize ederek anapara tutarını düşürmeniz, modelin onay verme olasılığını doğrudan artıracaktır."
    },
    "Kredi_Gecmisi": {
        "pozitif": "Uzun ve düzenli finansal ayak iziniz güvenilirlik skorunuzu yükseltmiştir.",
        "red": "Finansal sistemdeki geçmişinizin (kredi sicilinizin) kısalığı, yapay zeka modelinin yeterli istatistiksel güvene ulaşmasını engellemiştir.",
        "tavsiye": "Düşük limitli bir kredi kartını düzenli kullanarak bankacılık sistemindeki veri izinizi güçlendirmeye odaklanabilirsiniz."
    },
    "Deneyim_Yil": {
        "pozitif": "Mesleki tecrübeniz ve istikrarınız gelir sürekliliği açısından olumlu değerlendirilmiştir.",
        "red": "Mevcut çalışma ve mesleki deneyim süreniz, gelir sürekliliği projeksiyonları kapsamında beklenen asgari eşiğin altında kalmıştır.",
        "tavsiye": "Aynı sektördeki istihdam süreniz arttıkça modelin istikrar değerlendirmesi pozitife dönecektir."
    },
    "Kredi_Puan": {
        "pozitif": "Kredi skorunuz güçlü bir geri ödeme alışkanlığına işaret etmektedir.",
        "red": "Findeks/FICO kredi skorunuz, bu hacimdeki bir fonlama için bankacılık standartlarında öngörülen asgari güvenlik seviyesinin altındadır.",
        "tavsiye": "Gecikmiş ödemelerinizi kapatmak ve asgari ödeme tutarları yerine borcun tamamını ödemeye çalışmak skorunuzu hızla toparlayacaktır."
    }
}

@app.route('/api/hesapla', methods=['POST'])
def hesapla():
    try:
        data = request.json
        para_birimi = data.get('para_birimi', 'TRY')
        kredi_gecmisi = float(data.get('kredi_gecmisi', 5))
        deneyim_yil = float(data.get('deneyim_yil', 0))
        toplam_varlik = float(data.get('toplam_varlik', 0))
        aylik_borc = float(data.get('aylik_borc', 0))
        aylik_gelir = float(data.get('aylik_gelir', 1))
        kredi_tutari = float(data.get('kredi_tutari', 0))
        vade = int(data.get('vade', 24))
        kredi_puani = float(data.get('kredi_puani', 0))

        kur = float(data.get('guncel_kur', 45.00))
        satin_alma_gucu_katsayisi = 2.5 
        efektif_kur = kur / satin_alma_gucu_katsayisi

        if para_birimi == 'TRY':
            tutar_usd = kredi_tutari / efektif_kur
            gelir_usd = aylik_gelir / efektif_kur  
            varlik_usd = toplam_varlik / efektif_kur
            borc_usd = aylik_borc / efektif_kur 
            puan_fico = findeks_to_fico(kredi_puani)
        else:
            tutar_usd, gelir_usd, varlik_usd, borc_usd, puan_fico = kredi_tutari, aylik_gelir, toplam_varlik, aylik_borc, kredi_puani

        # Faiz tahmini
        faiz_input_df = pd.DataFrame([[puan_fico, vade, tutar_usd, deneyim_yil]], 
                                     columns=['Kredi_Puan', 'Kredi_Vade', 'Kredi_Tutar', 'Deneyim_Yil'])
        
        yillik_faiz = faiz_model.predict(faiz_input_df)[0]
        yillik_faiz = max(0.12, min(yillik_faiz, 0.45))
        
        aylik_faiz = yillik_faiz / 12
        aylik_taksit = (tutar_usd * aylik_faiz * ((1 + aylik_faiz) ** vade)) / (((1 + aylik_faiz) ** vade) - 1)
        borc_gelir_oran = (borc_usd + aylik_taksit) / gelir_usd

        # Model input dict
        input_dict = {
            "Aylik_Gelir": gelir_usd,
            "Aylik_Borc_Odeme": borc_usd,
            "Toplam_Varlik": varlik_usd,
            "Kredi_Tutar": tutar_usd,
            "Kredi_Vade": vade,
            "Kredi_Puan": puan_fico,
            "Tahmini_Yillik_Faiz": yillik_faiz,
            "YeniHesaplanan_AylikOdemeTutar": aylik_taksit,
            "Toplam_Borc_Gelir_Oran": borc_gelir_oran,
            "Kredi_Gecmisi": kredi_gecmisi,
            "Deneyim_Yil": deneyim_yil
        }

        calisma_durumu = data.get('calisma_durumu', '')
        if f"Calisma_Durum_{calisma_durumu}" in model_columns:
            input_dict[f"Calisma_Durum_{calisma_durumu}"] = 1
            
        egitim_seviyesi = data.get('egitim_seviyesi', '')
        if f"Egitim_Seviye_{egitim_seviyesi}" in model_columns:
            input_dict[f"Egitim_Seviye_{egitim_seviyesi}"] = 1

        df_input = pd.DataFrame([input_dict])
        df_input = df_input.reindex(columns=model_columns, fill_value=0)

        df_input_scaled = scaler.transform(df_input)
        
        # Sınıf 1 = Onay olasılığı
        prediction_proba = model.predict_proba(df_input_scaled)[0][1]
        
        # Threshold kontrolü
        onaylandi_mi = bool(prediction_proba >= threshold)

        shap_degerleri = df_input_scaled[0] * model.coef_[0]
        feature_impacts = list(zip(model_columns, shap_degerleri))
        feature_impacts.sort(key=lambda x: abs(x[1]), reverse=True)

        ai_mesaji = ""
        red_sebepleri = []
        ai_tavsiyeleri = []

        gosterilecek_taksit = aylik_taksit * efektif_kur if para_birimi == 'TRY' else aylik_taksit
        
        if para_birimi == 'TRY':
            gercek_borc_gelir_orani = (aylik_borc + gosterilecek_taksit) / aylik_gelir if aylik_gelir > 0 else 1.0
        else:
            gercek_borc_gelir_orani = (aylik_borc + gosterilecek_taksit) / aylik_gelir if aylik_gelir > 0 else 1.0

        if onaylandi_mi:
            # Pozitif etkenleri al (SHAP > 0)
            pozitif_etkenler = [f[0] for f in feature_impacts if f[1] > 0][:2]
            mesaj_parcalari = [SHAP_YORUMLARI[f]["pozitif"] for f in pozitif_etkenler if f in SHAP_YORUMLARI]
            
            if mesaj_parcalari:
                ai_mesaji = "Finansal profiliniz oldukça stabil değerlendirildi. " + " Ayrıca ".join(mesaj_parcalari)
            else:
                ai_mesaji = "Algoritmamız, sunulan finansal parametreler doğrultusunda başvurunuzu güvenilir bularak onaylamıştır."
        else:
            # Negatif etkenleri belirle. Demografik (dummy) değişkenleri sebebi olarak göstermiyoruz.
            gecerli_negatif_etkenler = []
            for etken, deger in feature_impacts:
                if deger >= 0:
                    continue
                # Yüksek puanda SHAP sapmasını yoksay
                if etken == "Kredi_Puan" and kredi_puani > 1300:
                    continue
                if etken == "Toplam_Borc_Gelir_Oran" or etken in SHAP_YORUMLARI:
                    gecerli_negatif_etkenler.append((etken, deger))

            if gecerli_negatif_etkenler:
                # En baskın sebebi al
                secilenler = [gecerli_negatif_etkenler[0]]
                # İkinci sebep ilkiyle rekabet ediyorsa ekle
                if len(gecerli_negatif_etkenler) > 1:
                    en_etkili_deger = abs(gecerli_negatif_etkenler[0][1])
                    ikinci_etken, ikinci_deger = gecerli_negatif_etkenler[1]
                    if abs(ikinci_deger) >= 0.5 * en_etkili_deger:
                        secilenler.append((ikinci_etken, ikinci_deger))

                for etken, _ in secilenler:
                    if etken == "Toplam_Borc_Gelir_Oran":
                        red_sebepleri.append(f"Talep edilen kredi taksiti ve mevcut borçlarınız, aylık gelirinizin %{int(gercek_borc_gelir_orani*100)}'ine ulaşarak banka risk eşiğini aşmaktadır.")
                        ai_tavsiyeleri.append("Vadeyi uzatarak aylık taksit tutarını düşürmeyi veya kredi miktarını azaltmayı simüle edebilirsiniz.")
                    else:
                        red_sebepleri.append(SHAP_YORUMLARI[etken]["red"])
                        ai_tavsiyeleri.append(SHAP_YORUMLARI[etken]["tavsiye"])
            else:
                red_sebepleri.append("Başvurunuz, mevcut finansal profilinizin bütünsel değerlendirmesi sonucunda risk eşiğinin üzerinde bulunmuştur.")

        if data.get('mlops_izni'):
            try:
                database.basvuru_kaydet(
                    girdi=data,
                    tahmin={
                        "tahmini_yillik_faiz": float(yillik_faiz),
                        "aylik_taksit": float(aylik_taksit),
                        "borc_gelir_orani": float(borc_gelir_oran),
                        "onay_olasiligi": float(prediction_proba),
                        "sonuc": "ONAY" if onaylandi_mi else "RED",
                    }
                )
            except Exception as db_hata:
                print("MLOps kayıt hatası:", str(db_hata))

        if onaylandi_mi:
            return jsonify({
                "sonuc": "ONAY",
                "faiz_orani": round(aylik_faiz * 12 * 100, 2),
                "aylik_taksit": round(gosterilecek_taksit, 2),
                "ai_mesaji": ai_mesaji
            })
        else:
            if not ai_tavsiyeleri:
                ai_tavsiyeleri.append("Risk skorunuzu iyileştirmek için şubenizdeki müşteri temsilcisi ile farklı finansman yapılandırmalarını görüşebilirsiniz.")
            
            return jsonify({
                "sonuc": "RED",
                "red_sebepleri": list(set(red_sebepleri)),
                "ai_tavsiyeleri": list(set(ai_tavsiyeleri))
            })

    except Exception as e:
        print("HATA OLUŞTU:", str(e))
        return jsonify({"hata": str(e)}), 500


@app.route('/api/live_tahmin', methods=['POST'])
def live_tahmin():
    try:
        data = request.json
        kredi_puan = float(data.get('kredi_puan', 650))
        kredi_vade = int(data.get('kredi_vade', 24))
        kredi_tutar = float(data.get('kredi_tutar', 0))
        deneyim_yil = float(data.get('deneyim_yil', 0))
        para_birimi = data.get('para_birimi', 'TRY')

        kur = float(data.get('guncel_kur', 45.00))
        satin_alma_gucu_katsayisi = 2.5 
        efektif_kur = kur / satin_alma_gucu_katsayisi

        if para_birimi == 'TRY':
            tutar_usd = kredi_tutar / efektif_kur
            puan_fico = findeks_to_fico(kredi_puan)
        else:
            tutar_usd, puan_fico = kredi_tutar, kredi_puan

        faiz_input_df = pd.DataFrame([[puan_fico, kredi_vade, tutar_usd, deneyim_yil]],
                                     columns=['Kredi_Puan', 'Kredi_Vade', 'Kredi_Tutar', 'Deneyim_Yil'])

        yillik_faiz = faiz_model.predict(faiz_input_df)[0]
        yillik_faiz = max(0.12, min(yillik_faiz, 0.45))

        aylik_faiz = yillik_faiz / 12
        if kredi_tutar > 0 and kredi_vade > 0:
            aylik_taksit = (tutar_usd * aylik_faiz * ((1 + aylik_faiz) ** kredi_vade)) / (((1 + aylik_faiz) ** kredi_vade) - 1)
            gosterilecek_taksit = aylik_taksit * efektif_kur if para_birimi == 'TRY' else aylik_taksit
        else:
            gosterilecek_taksit = 0

        return jsonify({
            "aylik_faiz_orani": float(yillik_faiz),
            "aylik_taksit": float(gosterilecek_taksit)
        })

    except Exception as e:
        print("HATA (live_tahmin):", str(e))
        return jsonify({"hata": str(e)}), 500

if __name__ == '__main__':
    from waitress import serve
    print("Quanta - Kredi Karar Motoru LR ve SHAP Analizi İle Çalışıyor. (Port: 8000)")
    # Prod ortamı için Waitress (IIS üzerinden reverse proxy ile dışarı açılacak)
    serve(app, host='127.0.0.1', port=8000)