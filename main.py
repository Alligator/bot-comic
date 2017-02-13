from flask import Flask, make_response, request
import comic

app = Flask(__name__)

@app.route('/create', methods=['POST'])
def index():
  data = request.json
  title = data['title'] if 'title' in data else ''
  resp = make_response(comic.comic(title, data['messages']))
  resp.headers['Content-Type'] = 'image/jpeg'
  return resp

if __name__ == '__main__':
  app.run()
