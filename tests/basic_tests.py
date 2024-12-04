import requests
import json
import pytest
from xprocess import ProcessStarter

url = "http://localhost:8000"

@pytest.fixture(autouse=True)
def myserver(xprocess):
  class Starter(ProcessStarter):
    pattern = "Server is running on port 8000"
    args = ['npm', 'run', 'dev']

  logfile = xprocess.ensure('myserver', Starter)
  conn = url
  yield conn

  xprocess.getinfo('myserver').terminate()

def test_sample():
  addReqs = [{ "payer": "DANNON", "points": 300, "timestamp": "2022-10-31T10:00:00Z" },
  { "payer": "UNILEVER", "points": 200, "timestamp": "2022-10-31T11:00:00Z" },
  { "payer": "DANNON", "points": -200, "timestamp": "2022-10-31T15:00:00Z" },
  { "payer": "MILLER COORS", "points": 10000, "timestamp": "2022-11-01T14:00:00Z" },
  { "payer": "DANNON", "points": 1000, "timestamp": "2022-11-02T14:00:00Z" }]
  for body in addReqs:
    resp= requests.post(url+'/add', json=body)
    assert resp.status_code == 200
    assert resp.text == ''

  resp = requests.post(url+'/spend', json={"points": 5000})
  assert resp.status_code == 200
  assert sorted(resp.json(), key=lambda x: x['points']) == [
    {'payer': 'MILLER COORS',
     'points': -4700},
    {'payer': 'UNILEVER',
     'points': -200},
    {'payer': 'DANNON',
     'points': -100},
  ]

  resp = requests.get(url+'/balance')
  assert resp.status_code == 200
  assert resp.json() == {
    'UNILEVER': 0,
    'DANNON': 1000,
    'MILLER COORS': 5300,
  }

''' TO DO: Consider implementing parametrization
@pytest.mark.parametrize("expected", [])
def test_normalize(expected):
  pass
'''

def test_normalize_1():
  addReqs = [{ "payer": "DANNON", "points": 300, "timestamp": "2022-10-31T10:00:00Z" },
  { "payer": "DANNON", "points": -100, "timestamp": "2022-10-31T11:00:00Z" },
  { "payer": "DANNON", "points": 100, "timestamp": "2022-10-31T15:00:00Z" }]
  for body in addReqs:
    resp= requests.post(url+'/add', json=body)
    assert resp.status_code == 200
    assert resp.text == ''

  resp = requests.post(url+'/spend', json={"points": 300})
  assert resp.status_code == 200
  assert sorted(resp.json(), key=lambda x: x['points']) == [
    {'payer': 'DANNON',
     'points': -300},
  ]

  resp = requests.get(url+'/balance')
  assert resp.status_code == 200
  assert resp.json() == {
    'DANNON': 0
  }

def test_normalize_2():
  addReqs = [{ "payer": "DANNON", "points": 300, "timestamp": "2022-10-31T10:00:00Z" },
  { "payer": "UNILEVER", "points": 300, "timestamp": "2022-10-31T11:00:00Z" },
  { "payer": "DANNON", "points": -100, "timestamp": "2022-10-31T15:00:00Z" },
  { "payer": "MILLER COORS", "points": 200, "timestamp": "2022-11-01T14:00:00Z" },
  { "payer": "DANNON", "points": -200, "timestamp": "2022-11-02T14:00:00Z" }]

  for body in addReqs:
    resp= requests.post(url+'/add', json=body)
    assert resp.status_code == 200
    assert resp.text == ''

  resp = requests.post(url+'/spend', json={"points": 500})
  assert resp.status_code == 200
  assert sorted(resp.json(), key=lambda x: x['points']) == [
    {'payer': 'UNILEVER',
     'points': -300},
    {'payer': 'MILLER COORS',
     'points': -200},
    {'payer': 'DANNON',
     'points': 0},
  ]

  resp = requests.get(url+'/balance')
  assert resp.status_code == 200
  assert resp.json() == {
    'DANNON': 0,
    'UNILEVER': 0,
    'MILLER COORS': 0
  }   
  
def test_normalize_3():
  addReqs = [{ "payer": "DANNON", "points": 500, "timestamp": "2023-11-01T10:00:00Z" },
  { "payer": "UNILEVER", "points": 300, "timestamp": "2023-11-01T11:00:00Z" },
  { "payer": "DANNON", "points": -200, "timestamp": "2023-11-01T12:00:00Z" }]

  for body in addReqs:
    resp= requests.post(url+'/add', json=body)
    assert resp.status_code == 200
    assert resp.text == ''

  resp = requests.post(url+'/spend', json={"points": 400})
  assert resp.status_code == 200
  assert sorted(resp.json(), key=lambda x: x['points']) == [
    {'payer': 'DANNON',
     'points': -300},
    {'payer': 'UNILEVER',
     'points': -100},
  ]

  resp = requests.get(url+'/balance')
  assert resp.status_code == 200
  assert resp.json() == {
    'DANNON': 0,
    'UNILEVER': 200,
  }   

def test_multiple_spend_1():
  addReqs = [{ "payer": "DANNON", "points": 1000, "timestamp": "2023-11-01T10:00:00Z" },
  { "payer": "UNILEVER", "points": 2000, "timestamp": "2023-11-01T11:00:00Z" },
  { "payer": "MILLER COORS", "points": 3000, "timestamp": "2023-11-01T12:00:00Z" }]

  for body in addReqs:
    resp= requests.post(url+'/add', json=body)
    assert resp.status_code == 200
    assert resp.text == ''

  resp = requests.post(url+'/spend', json={"points": 2500})
  assert resp.status_code == 200
  assert sorted(resp.json(), key=lambda x: x['points']) == [
    {'payer': 'UNILEVER',
     'points': -1500},
    {'payer': 'DANNON',
     'points': -1000},
    {'payer': 'MILLER COORS',
     'points': 0}
  ]

  resp = requests.post(url+'/spend', json={"points": 1500})
  assert resp.status_code == 200
  assert sorted(resp.json(), key=lambda x: x['points']) == [
    {'payer': 'MILLER COORS',
     'points': -1000},
    {'payer': 'UNILEVER',
     'points': -500},
    {'payer': 'DANNON',
     'points': 0}
  ]

  resp = requests.get(url+'/balance')
  assert resp.status_code == 200
  assert resp.json() == {
    'DANNON': 0,
    'UNILEVER': 0,
    'MILLER COORS': 2000,
  }   

def test_spend_fail():
  addReqs = [{ "payer": "DANNON", "points": 200, "timestamp": "2023-11-01T10:00:00Z" },
  { "payer": "UNILEVER", "points": 100, "timestamp": "2023-11-01T11:00:00Z" }]

  for body in addReqs:
    resp= requests.post(url+'/add', json=body)
    assert resp.status_code == 200
    assert resp.text == ''

  resp = requests.post(url+'/spend', json={"points": 400})
  assert resp.status_code == 400
  assert resp.text != ''

  resp = requests.get(url+'/balance')
  assert resp.status_code == 200
  assert resp.json() == {
    'DANNON': 200,
    'UNILEVER': 100,
  }   
  
def test_large():
  addReqs = [{ "payer": "DANNON", "points": 300, "timestamp": "2023-11-01T10:00:00Z" },
  { "payer": "UNILEVER", "points": 400, "timestamp": "2023-11-01T11:00:00Z" },
  { "payer": "MILLER COORS", "points": 1000, "timestamp": "2023-11-01T12:00:00Z" },
  { "payer": "DANNON", "points": -300, "timestamp": "2023-11-01T13:00:00Z" },
  { "payer": "UNILEVER", "points": -200, "timestamp": "2023-11-01T14:00:00Z" },
  { "payer": "MILLER COORS", "points": 500, "timestamp": "2023-11-01T15:00:00Z" }]

  for body in addReqs:
    resp= requests.post(url+'/add', json=body)
    assert resp.status_code == 200
    assert resp.text == ''

  resp = requests.post(url+'/spend', json={"points": 1000})
  assert resp.status_code == 200 
  assert sorted(resp.json(), key=lambda x: x['points']) == [
    {'payer': 'MILLER COORS',
     'points': -800},
    {'payer': 'UNILEVER',
     'points': -200},
    {'payer': 'DANNON',
     'points': 0}
  ]

  resp = requests.get(url+'/balance')
  assert resp.status_code == 200
  assert resp.json() == {
    'DANNON': 0,
    'UNILEVER': 0,
    'MILLER COORS': 700
  }   