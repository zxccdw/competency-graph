# from dao.competency_dao import CompetencyDAO
# from SPARQLWrapper import SPARQLWrapper, JSON

# config = {
#     "url": "http://graphdb:7200",
#     "repository": "competencies",
#     "username": "admin",
#     "password": "admin",
# }

# endpoint = f"{config['url']}/repositories/{config['repository']}"
# client = SPARQLWrapper(endpoint)
# client.setReturnFormat(JSON)

# if config['username'] and config['password']:
#     client.setCredentials(config['username'], config['password'])

# competency_dao = CompetencyDAO(client, config)

# print("healthcheck passed")