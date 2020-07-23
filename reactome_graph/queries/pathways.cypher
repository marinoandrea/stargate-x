match (r:Event),
    (r)<-[:hasEvent]-(p:Pathway),
    (r)-[:species]->(s:Species)
where '$species' = s.abbreviation
and r.stId =~ 'R-($species|ALL|NUL)-.*'
and p.stId =~ 'R-($species|ALL|NUL)-.*'
return r.stId as reaction, p.stId as pathway;