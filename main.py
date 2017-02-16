from flask import Flask, make_response, request
import comic

app = Flask(__name__)

@app.route('/create', methods=['POST'])
def create():
  data = request.json
  title = data.get('title', None)
  resp = make_response(comic.comic(data['messages'], title=title))
  resp.headers['Content-Type'] = 'image/jpeg'
  return resp

@app.route('/test', methods=['GET'])
def test():
  data = {
    "title": "test",
    "messages": [
      {
        "user": "one",
        "message": "he drinks a whiskey drink",
        "timestamp": 1487018500
      },
      {
        "user": "two",
        "message": "he drinks a vodka drink",
        "timestamp": 1487018500
      },
      {
        "user": "one",
        "message": "he drinks a lager drink",
        "timestamp": 1487018500
      },
      {
        "user": "two",
        "message": "he drinks a cider drink",
        "timestamp": 1487018500
      },
      {
        "user": "three",
        "message": "he sings the songs that remind him of the good times",
        "timestamp": 1487018500
      },
      {
        "user": "one",
        "message": "he sings the songs that remind him of the better times",
        "timestamp": 1487018500
      },
    ]
  }
  resp = make_response(comic.comic(data['messages'], title=data['title']))
  resp.headers['Content-Type'] = 'image/jpeg'
  return resp

if __name__ == '__main__':
  app.run()
