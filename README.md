# SAP Employee Self-Service Portal (MVP)

بورطاي بسيط للموظفين: بيان الأجرة، ملخص الغياب/التأخير، وطلبات Attestation.
دابا كيخدم بـ **بيانات وهمية** (`app/mock_data.py`) — باش الديمو تبان شغالة بلا ما تحتاج
وصول حقيقي لـ SAP. الربط الحقيقي مع SAP كيتدار من خلال `app/sap_connector.py` فقط —
باقي الكود ما خصوش يتبدل.

## المستخدمين ديال الديمو
| Username | Password | الدور |
|---|---|---|
| j.alaoui | demo1234 | موظف |
| s.bennani | demo1234 | موظف |
| m.idrissi | manager1234 | مسؤول (موافقة على الطلبات) |

## الخدمة محليا
```bash
pip install -r requirements.txt
cd app
python main.py
```

## النشر على Railway
1. رفعتي هاد المجلد كامل لـ GitHub repo جديد
2. فـ Railway: New Project → Deploy from GitHub repo
3. Railway غادي يقرا `Procfile` و `requirements.txt` أوتوماتيكيا
4. زيد Environment Variable: `SECRET_KEY` بقيمة عشوائية طويلة
5. Deploy — و التطبيق يولي شغال على رابط Railway

## الخطوة الجاية: الربط مع SAP حقيقي
غير بدل الدوال فـ `app/sap_connector.py` باش تستافد من:
- **RFC/BAPI** عبر مكتبة `pyrfc` (خاصها SAP NetWeaver RFC SDK)
- ولا **OData Services** (REST) إيلا SAP عندكم كيدعمها — أسهل وأحدث
