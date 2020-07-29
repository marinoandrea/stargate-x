match (r:Event),
    (r)<-[:hasEvent*]-(p:Pathway),
    (r)-[:species]->(s:Species),
    lPath = (p)<-[:hasEvent*0..]-(tlp:TopLevelPathway)
where '$species' = s.abbreviation
and r.stId =~ 'R-($species|ALL|NUL)-.*'
and p.stId =~ 'R-($species|ALL|NUL)-.*'
return r.stId as reaction, p.stId as pathway, length(lPath) as level;