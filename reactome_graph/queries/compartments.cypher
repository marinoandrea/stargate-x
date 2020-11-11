match (n)-[:compartment]->(c:Compartment)
optional match (n)-[:species]->(s:Species)
where '$species' = s.displayName
or n.stId =~ 'R-(ALL|NUL)-.*'
return n.stId as node, c as compartment;

