-- An alias may carry the name of another service's schema; it qualifies a column, not a relation.
SELECT platform.id FROM register.arrangements AS platform;
SELECT ictrisk.note FROM register.arrangements ictrisk JOIN register.arrangements b ON ictrisk.id = b.id;
