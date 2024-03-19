from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from neo4j import GraphDatabase

app = Flask(__name__)
CORS(app)

class Neo4JDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_stage_treatment_and_tests(self, t_label, n_label, m_label):
        query = """
        MATCH (n:N_Stage_Finding {label: $n_label})-[:Has_Stage]->(target),
              (m:M_Stage_Finding {label: $m_label})-[:Has_Stage]->(target),
              (t:T_Stage_Finding {label: $t_label})-[:Has_Stage]->(target)
        MATCH (target)-[:Has_Recommended_Test]->(test),
              (target)-[:Has_Treatment_Option]->(treatment)
        RETURN target AS Stage, collect(distinct test.label) AS RecommendedTests, collect(distinct treatment.label) AS TreatmentOptions
        """
        stages_info = []  # Lista para almacenar todos los resultados
        with self.driver.session() as session:
            result = session.run(query, t_label=t_label, n_label=n_label, m_label=m_label)
            for record in result:
                stages_info.append({
                    "Stage": record["Stage"]["label"],
                    "RecommendedTests": record["RecommendedTests"],
                    "TreatmentOptions": record["TreatmentOptions"]
                })
        return stages_info if stages_info else None

# Configura aquí tus credenciales de Neo4j
uri = "neo4j://localhost:7687"
user = "neo4j"
password = "password"
db = Neo4JDatabase(uri, user, password)

@app.route('/')
@cross_origin()
def home():
    return "En ejecución"

@app.route('/get_stage_info', methods=['GET'])
@cross_origin()
def get_stage_info():
    t_label = request.args.get('t_label')
    n_label = request.args.get('n_label')
    m_label = request.args.get('m_label')

    if not (t_label and n_label and m_label):
        return jsonify({"error": "Missing parameters"}), 400

    stage_info = db.get_stage_treatment_and_tests(t_label, n_label, m_label)
    if stage_info:
        return jsonify(stage_info)
    else:
        return jsonify({"error": "No results found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=True)
