# تشغيل FLARE AI على جهازك

1. ثبّت Docker Desktop من https://www.docker.com/products/docker-desktop/ ثم شغّله.
2. فك ضغط الحزمة وافتح مجلد `FLARE-AI`.
3. على ويندوز شغّل `start-windows.bat`. على الماك شغّل `start-mac.command`.
4. انتظر اكتمال التنزيل والبناء الأول، ثم افتح http://localhost:8100.

أو افتح Terminal داخل المجلد ونفّذ:

```sh
docker compose up --build -d --wait
```

يحتاج التشغيل الأول اتصال إنترنت لتنزيل الاعتماديات والصور. لا تحتاج تثبيت Python أو Node على جهازك عند استخدام Docker.

## تفعيل Kie

الحزمة لا تحتوي مفتاح API. تنشئ ملفات التشغيل `.env` من `.env.example` إذا لم يكن موجودًا. افتح `.env` بمحرر نصوص، وضع مفتاحك بعد `KIE_API_KEY=` وغيّر `AI_MODE=offline` إلى `AI_MODE=live`، ثم نفّذ:

```sh
docker compose up -d --no-deps api
```

لا تحتاج ملف `compose.tls.yaml` على جهاز عادي. هذا الملف اختياري للبيئات التي تستخدم شهادة HTTPS خاصة موثوقة.

## إيقاف المشروع أو مراجعة خطأ

للإيقاف مع الاحتفاظ بالبيانات:

```sh
docker compose down
```

لعرض السجلات:

```sh
docker compose logs --tail=100 api worker
```

إذا كان المنفذ 8100 مستخدمًا، غيّر جهة اليسار من `127.0.0.1:8100:8100` في `compose.yaml` إلى منفذ متاح، مثل `127.0.0.1:8101:8100`، ثم افتح http://localhost:8101.

هذه نسخة بحثية تجريبية ببيانات محاكاة معلنة. شرح النطاق والاختبارات موجود في README.md ومجلد docs.
