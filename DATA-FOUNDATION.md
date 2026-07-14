# زیرساخت داده گراول — نسخه ۱

این نسخه Cloudflare Web Analytics را برای آمار عمومی حفظ می‌کند و رویدادهای آموزشی رضایت‌محور را به یک Cloudflare Worker می‌فرستد. IP خام و User-Agent در کد Worker ذخیره نمی‌شوند.

## انتشار Worker

1. در Cloudflare به **Workers & Pages → Create → Worker** بروید.
2. پوشه `worker` را با Wrangler منتشر کنید: `cd worker && npx wrangler deploy`.
3. آدرس خروجی، مانند `https://gravel-events.<account>.workers.dev` را در `assets/analytics-config.js` مقابل `endpoint` قرار دهید.
4. در Cloudflare برای Worker، Rate Limiting و Bot protection را فعال کنید.
5. رویداد آزمایشی بفرستید و در Analytics Engine وجود داده را بررسی کنید.

نمونهٔ گزارش روزانه در Analytics Engine SQL API:

```sql
SELECT blob1 AS event, COUNT() AS total
FROM gravel_events
WHERE timestamp > NOW() - INTERVAL '1' DAY
GROUP BY event
ORDER BY total DESC
```

## فرهنگ رویدادها

| رویداد | زمان ثبت | ویژگی‌های مجاز |
|---|---|---|
| `visitor_arrived` | ورود رضایت‌داده‌شده | `entry` |
| `level_selected` | انتخاب سطح | `level` |
| `path_selected` | انتخاب مسیر | `track` |
| `search_performed` | اجرای جست‌وجو | `query`, `results` |
| `search_no_result` | جست‌وجوی بدون نتیجه | `query` |
| `tutorial_opened` | کلیک روی آموزش | `tutorialId`, `source` |
| `tutorial_started` | ورود به صفحه آموزش | `tutorialId` |
| `tutorial_completed` | علامت‌زدن «خواندم» | `tutorialId` |
| `tutorial_abandoned` | خروج پیش از پایان | `tutorialId`, `seconds`, `maxScroll` |
| `next_tutorial_clicked` | کلیک پیشنهاد بعدی | `tutorialId` |
| `topic_requested` | درخواست موضوع | فقط دسته/موضوع پالایش‌شده؛ بدون اطلاعات تماس |

## قانون داده

- متن ویژگی‌ها در مرورگر و Worker محدود می‌شود.
- نام، ایمیل، تلفن، رمز، کلید API و متن گفتگو نباید در properties ارسال شود.
- شناسهٔ بازدیدکننده تصادفی است و هر ۳۰ روز عوض می‌شود.
- برای صادرات بلندمدت، مرحله بعد Queue → R2 با فایل‌های روزانه Parquet است؛ نه یک فایل برای هر رویداد.
- نگهداری دادهٔ خام: ۹۰ روز؛ دادهٔ تجمیعی بدون شناسه: حداکثر ۲۴ ماه.
- دسترسی مدیریتی با MFA، حداقل سطح دسترسی و ثبت تغییرات انجام شود.

## کنترل انتشار

تا وقتی `endpoint` خالی است هیچ رویداد اختصاصی ارسال نمی‌شود و سایت بدون وابستگی به Worker کار می‌کند.
