match (r:Event),
    (r)<-[:hasEvent]-(p:Pathway),
    (r)-[:species]->(s:Species)
where '$species_name' in s.name
and r.stId =~ 'R-($species_code|ALL|NUL)-.*'
and p.stId =~ 'R-($species_code|ALL|NUL)-.*'
return r.stId as id, p as pathway;