# LICENSES

## کد این بسته

- محتوای `13_missions_batch3/` بخشی از مخزن AHOS است و از مجوز مخزن اصلی پیروی
  می‌کند (در ریشه‌ی مخزن). در این پوشه مجوز مستقلی الصاق نشده است.

## وابستگی‌های npm (همه مجوزهای استاندارد متن‌باز)

| بسته | نسخه | مجوز (رایج) |
|---|---|---|
| next | 16.4.2 | MIT |
| react / react-dom | 19.3.1 | MIT |
| tailwindcss / @tailwindcss/postcss | 4.3.3 | MIT |
| typescript | 5.9.3 | Apache-2.0 |
| vitest | 5.0.5 | MIT |
| jsdom | 30.1.3 | MIT |
| @testing-library/react / dom | 16.3.3 / 10.4.2 | MIT |
| @vitejs/plugin-react | 6.1.2 | MIT |
| eslint / typescript-eslint / @eslint/js | 9.x / 8.x / 9.x | MIT |
| @types/* | — | MIT |

(اسناد مجوز هر بسته در `node_modules/<pkg>/LICENSE` پس از `npm install` موجود است.)

## فونت‌ها

فونت Vazirmatn (SIL OFL 1.1) و Inter (SIL OFL 1.1) **باینری توزیع نشده‌اند**؛ کد فقط
`@font-face` با `src: local(...)` دارد و در نبود فونت محلی از `system-ui` استفاده
می‌شود. بنابراین هیچ فایل فونتی در این مخزن نیست که مجوزش اینجا بیاید.

## داده‌ها

همه‌ی داده‌های `public/contract/ahos-arena-contract.example.json` و `src/mock/*`
نمونه‌ی DEMO ساختگی هستند و به هیچ منبع خارجی وابسته نیستند. هیچ محتوای باینری
(تصویر/صوت/woff) در بسته وجود ندارد.
