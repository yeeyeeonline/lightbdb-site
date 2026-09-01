-- 供本机轮询脚本读取新询单（security definer，需 token 校验）
-- 在 SQL Editor 里 Run 一次

create or replace function public.recent_inquiries(
  p_token text,
  p_since timestamptz default now() - interval '24 hours'
) returns table (
  id uuid,
  created_at timestamptz,
  name text,
  company text,
  email text,
  country text,
  category text,
  message text
)
language plpgsql
security definer
set search_path = public
as $$
begin
  -- token 不对就返回空（把 <TOKEN> 换成下面 generate 出来的值）
  if p_token is distinct from 'LBDB_NOTIFY_7f3a91c4e8b2' then
    return;
  end if;

  return query
    select i.id, i.created_at, i.name, i.company, i.email, i.country, i.category, i.message
    from public.inquiries i
    where i.created_at > p_since
    order by i.created_at desc;
end;
$$;

grant execute on function public.recent_inquiries(text, timestamptz) to anon;

-- 顺手清掉测试数据（可选）
delete from public.inquiries where name = 'Test Inquiry';
