# SCREENSHOT_PLAN — 1600×900 (مالک باید بگیرد؛ در این تحویل اسکرین‌شاتی وجود ندارد)

همه‌ی عکس‌ها با پنجره‌ی 1600×900، حالت پیش‌فرض (`tier=1`)، و با نوار آدرس مرورگر در
قاب گرفته شوند تا URL قابل تأیید باشد. تحویل متنی شامل هیچ تصویری نیست.

| # | صفحه | URL | توضیح |
|---|---|---|---|
| 1 | رادار علم | `/arena/science-radar` | نمای آرام: نوار صحت، چیپ‌های شمارش، ۷ مورد |
| 2 | رادار علم — جزئیات | `/arena/science-radar` + باز کردن «جزئیات» | جدول کامل + فیلتر نوع منبع |
| 3 | خطایابی | `/arena/self-debug` | خلاصه (باز/تشخیص/میانه سن) + کارت‌ها |
| 4 | خطایابی — جزئیات | `/arena/self-debug` + «جزئیات» + باز کردن timeline یک رخداد | خط زمانی + گزیده گزارش |
| 5 | آزمون هفتگی | `/arena/weekly-exam` | کارت آخرین آزمون + «نمونه ناکافی» |
| 6 | آزمون هفتگی — جزئیات | `/arena/weekly-exam` + «جزئیات» | جدول اجراها + جدول موارد |
| 7 | بازار مهارت | `/arena/skill-market` | بنر «نصب ممکن نیست» + شمارش‌ها + موارد شاخص |
| 8 | بازار مهارت — جزئیات | `/arena/skill-market` + «جزئیات» | ستون مجوزها + «دلیل ثبت نشده» |
| 9 | مرکز اخبار | `/arena/news-center` | خبرهای آرام + چیپ‌های LIVE/STALE/UNKNOWN |
| 10 | مرکز اخبار — جزئیات | `/arena/news-center` + «جزئیات» | جدول کامل + موضوع‌های PLANNED |
| 11 | DEMO | `/arena/science-radar?demo=1` | ریبون/چیپ DEMO |
| 12 | VIOLATION | `/arena/science-radar?violation=1` | نوار قرمز تمام‌عرض |
| 13 | Tier 0 | `/arena/news-center?tier=0` | حالت جدولی بدون تزئین |
| 14 | Tier 2 | `/arena/news-center?tier=2` | بلور/تزئین |
| 15 | حالت خالی | `/arena/self-debug?state=empty` | بلوک EMPTY |
| 16 | حالت خطا | `/arena/self-debug?state=error` | بلوک ERROR |
| 17 | حالت UNAVAILABLE | `/arena/skill-market?state=unavailable` | بلوک UNAVAILABLE |
| 18 | بارگذاری | `/arena/weekly-exam?state=loading` | بلوک LOADING |

نکته: هیچ‌کدام از عکس‌ها نباید شامل نمونه‌هایی باشند که به‌عنوان «داده واقعی» خوانده
شوند؛ همه‌ی داده‌های فعلی DEMO هستند و باید چیپ DEMO در قاب دیده شود.
