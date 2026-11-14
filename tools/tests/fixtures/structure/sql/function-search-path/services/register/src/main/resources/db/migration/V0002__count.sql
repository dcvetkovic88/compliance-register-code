CREATE FUNCTION register.f() RETURNS int LANGUAGE sql SET search_path = register, ictrisk AS $$ SELECT 1 $$;
