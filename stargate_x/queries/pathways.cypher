match 
   (r:ReactionLikeEvent)<-[:hasEvent]-(p:Pathway),
   (r)-[:species]->(s:Species)
where '$species' = s.displayName
or r.stId =~ 'R-(ALL|NUL)-.*'
return 
   r.stId as reaction, 
   { data: p, isTopLevel: false} as pathway

union 

match 
   (r:ReactionLikeEvent)<-[:hasEvent*]-(p:TopLevelPathway),
   (r)-[:species]->(s:Species)
where '$species' = s.displayName
or r.stId =~ 'R-(ALL|NUL)-.*'
return 
   r.stId as reaction, 
   { data: p, isTopLevel: true} as pathway;