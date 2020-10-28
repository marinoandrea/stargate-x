match 
   (r:ReactionLikeEvent)<-[:hasEvent]-(p:Pathway),
   (r)-[:species]->(s:Species)
where '$species' = s.abbreviation
and r.stId =~ 'R-($species|ALL|NUL)-.*'
and p.stId =~ 'R-($species|ALL|NUL)-.*'
return 
   r.stId as reaction, 
   { data: p, isTopLevel: false} as pathway

union 

match 
   (r:ReactionLikeEvent)<-[:hasEvent*]-(p:TopLevelPathway),
   (r)-[:species]->(s:Species)
where '$species' = s.abbreviation
and r.stId =~ 'R-($species|ALL|NUL)-.*'
and p.stId =~ 'R-($species|ALL|NUL)-.*'
return 
   r.stId as reaction, 
   { data: p, isTopLevel: true} as pathway;