-- LightBDB 询单表 · Supabase 新加坡项目 pitvjzkuidbhqamwyorc
-- 在 Supabase Dashboard → SQL Editor 里整体执行一次即可。
-- 设计原则（A 档最简）：匿名可插入、不可读改删；邮件通知后续用 Database Webhook 加，不影响本表。

create table if not exists public.inquiries (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  name        text not null,
  company     text,
  email       text not null,
  country     text,
  category    text not null check (category in ('BODY','MIND','DESIGN','MULTI')),
  message     text
);

alter table public.inquiries enable row level security;

drop policy if exists "anon can insert inquiries" on public.inquiries;
create policy "anon can insert inquiries"
  on public.inquiries for insert
  to anon
  with check (true);

-- 防垃圾可后加：unlogged honeypot 字段或 Turnstile 校验，第一版先不加。
