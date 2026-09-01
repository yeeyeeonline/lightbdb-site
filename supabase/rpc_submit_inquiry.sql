-- 公开表单提交：用 security definer 函数绕过 RLS（Supabase 推荐做法）
-- 在 SQL Editor 里整体 Run 一次即可

create or replace function public.submit_inquiry(
  p_name      text,
  p_email     text,
  p_category  text,
  p_company   text default null,
  p_country   text default null,
  p_message   text default null
) returns json
language plpgsql
security definer
set search_path = public
as $$
declare
  v_id uuid;
begin
  if p_name is null or p_email is null or p_category is null then
    raise exception 'name, email and category are required';
  end if;

  insert into public.inquiries (name, email, category, company, country, message)
  values (p_name, p_email, p_category, p_company, p_country, p_message)
  returning id into v_id;

  return json_build_object('id', v_id);
end;
$$;

-- 只允许匿名调用这一个函数（不能读写表，安全性与 RLS 直插等效）
grant execute on function public.submit_inquiry(text, text, text, text, text, text) to anon;
grant execute on function public.submit_inquiry(text, text, text, text, text, text) to authenticated;
