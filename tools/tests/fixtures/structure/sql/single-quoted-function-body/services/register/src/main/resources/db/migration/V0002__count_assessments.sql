CREATE FUNCTION register.count_assessments() RETURNS integer LANGUAGE sql AS '
SELECT count(*) FROM ictrisk.assessments WHERE note <> ''none''';
