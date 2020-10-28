match 
    (n)-[:compartment]->(c:Compartment),
    (n)-[:species]->(s:Species)
where '$species' = s.abbreviation
and n.stId =~ 'R-($species|ALL|NUL)-.*'
return  
    n.stId as node, 
    { data: c, isTopLevel: false } as compartment

union

match 
    (n)-[:compartment]->(c:Compartment),
    (n)-[:species]->(s:Species),
    lPath = (c)-[:componentOf*]->(tlc:Compartment)
where '$species' = s.abbreviation
and n.stId =~ 'R-($species|ALL|NUL)-.*'
return 
    n.stId as node, 
    { data: last(nodes(lPath)), isTopLevel: true } as compartment;
