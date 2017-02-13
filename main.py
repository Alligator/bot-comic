from flask import Flask, make_response, request
import comic

app = Flask(__name__)

@app.route('/create', methods=['POST'])
def index():
  resp = make_response(comic.comic('test', request.json))
  resp.headers['Content-Type'] = 'image/jpeg'
  return resp

if __name__ == '__main__':
  app.run()
