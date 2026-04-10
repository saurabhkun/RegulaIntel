from neo4j import GraphDatabase
from typing import List

class Neo4jStore:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def add_section(self, section_id: str, text: str, version: str, page: int):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (s:Section {id: $section_id})
                SET s.text = $text, s.version = $version, s.page = $page
                """,
                section_id=section_id, text=text, version=version, page=page
            )
    
    def add_amendment_relation(self, old_id: str, new_id: str):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (old:Section {id: $old_id}), (new:Section {id: $new_id})
                MERGE (old)-[:AMENDED_TO]->(new)
                """,
                old_id=old_id, new_id=new_id
            )
    
    def query_lineage(self, section_id: str):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path=(old:Section)-[:AMENDED_TO*]->(final:Section {id: $id})
                RETURN path
                """,
                id=section_id
            )
            return [record["path"] for record in result]

