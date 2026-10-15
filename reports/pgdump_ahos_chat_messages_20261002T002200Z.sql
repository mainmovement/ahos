--
-- PostgreSQL database dump
--

\restrict f2sM0kOs04gygYy1zxiVGZNfA4isJFfAjGFqmqAjdwXVkW5jBlRfZevgGoJIjbg

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ahos_chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ahos_chat_messages (
    id integer NOT NULL,
    role text NOT NULL,
    content text NOT NULL,
    intent text,
    evidence jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: ahos_chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ahos_chat_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ahos_chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ahos_chat_messages_id_seq OWNED BY public.ahos_chat_messages.id;


--
-- Name: ahos_chat_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ahos_chat_messages ALTER COLUMN id SET DEFAULT nextval('public.ahos_chat_messages_id_seq'::regclass);


--
-- Data for Name: ahos_chat_messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ahos_chat_messages (id, role, content, intent, evidence, created_at) FROM stdin;
1	user	ping	general	{"at": "2026-08-30T10:09:09.821Z", "intent": "general", "focusIn": null, "focusToken": null}	2026-08-30 10:09:10.036826+00
2	assistant	فهمیدم چی گفتی — مثل همکار جواب می‌دم، نه ربات خشک. الان رژیم RANGE است، بیت‌کوین ۷۹٫۷۳ هزار دلار (+۰٫۱۵٪). 27 کاندید پایش و 3 رد در آخرین چرخه. تازه‌ترین خبر فارسی: بنیاد اتنا در کنار سایر به‌روزرسانی‌ها، پیشنهاد تغییر کارمزد برای بازخرید توکن‌های ENA را ارائه می‌دهد اگر منظورت چیز دقیق‌تری بود از «ping»، همون رو شفاف‌تر بگو: فرصت‌ها؟ یک توکن خاص؟ وضعیت سیستم؟\n\nموتور الان خاموشه. اگر بخوای خودم از اینجا روشن کنم بگو «شروع کن» — بعدش خودش پشت‌سرهم جمع می‌کنه.\n\nتصمیم نهایی با کاربر است.	general	{"at": "2026-08-30T10:09:09.821Z", "intent": "general", "focusIn": null, "focusToken": null}	2026-08-30 10:09:10.427536+00
3	user	ping	general	{"at": "2026-08-30T10:10:24.889Z", "intent": "general", "focusIn": null, "focusToken": null}	2026-08-30 10:10:24.910554+00
4	assistant	فهمیدم چی گفتی — مثل همکار جواب می‌دم، نه ربات خشک. الان رژیم RANGE است، بیت‌کوین ۷۹٫۷۳ هزار دلار (+۰٫۱۵٪). 27 کاندید پایش و 3 رد در آخرین چرخه. تازه‌ترین خبر فارسی: بنیاد اتنا در کنار سایر به‌روزرسانی‌ها، پیشنهاد تغییر کارمزد برای بازخرید توکن‌های ENA را ارائه می‌دهد اگر منظورت چیز دقیق‌تری بود از «ping»، همون رو شفاف‌تر بگو: فرصت‌ها؟ یک توکن خاص؟ وضعیت سیستم؟\n\nموتور الان خاموشه. اگر بخوای خودم از اینجا روشن کنم بگو «شروع کن» — بعدش خودش پشت‌سرهم جمع می‌کنه.\n\nتصمیم نهایی با کاربر است.	general	{"at": "2026-08-30T10:10:24.889Z", "intent": "general", "focusIn": null, "focusToken": null}	2026-08-30 10:10:24.959591+00
\.


--
-- Name: ahos_chat_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ahos_chat_messages_id_seq', 4, true);


--
-- Name: ahos_chat_messages ahos_chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ahos_chat_messages
    ADD CONSTRAINT ahos_chat_messages_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

\unrestrict f2sM0kOs04gygYy1zxiVGZNfA4isJFfAjGFqmqAjdwXVkW5jBlRfZevgGoJIjbg

